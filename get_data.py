"""Download SCF summary extracts, 1989–2025 (2025 dollars).

Run: python get_data.py (Python 3.10+, pandas; system curl required).
Sources: https://www.federalreserve.gov/econres/scfindex.htm
Definitions: https://www.federalreserve.gov/econres/files/bulletin.macro.txt
All SCF families, not restricted to parents/households with children.
EDCL describes the reference person, not both partners or their parents.
EDCL=4: BA or higher; EDCL=1,2: high school/GED or less; omit EDCL=3.
NETWORTH includes housing and retirement accounts, less debts; not income.
Compute WGT-weighted statistics separately in each of five implicates,
then average point estimates. No sampling errors or significance claims.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
from datetime import datetime, timezone
import zipfile
import pandas as pd

ROOT = Path(__file__).resolve().parent
YEARS = range(1989, 2026, 3)
BASE = 'https://www.federalreserve.gov/econres/'


def download(url, path, refresh=False):
    if refresh or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + '.tmp')
        subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                        '--retry', '3', '--max-time', '120', url, '-o', str(temp)], check=True)
        temp.replace(path)
    return path.read_bytes()


def weighted_median(frame):
    # Inverse empirical CDF; ties aggregated implicitly by cumulative weights.
    ordered = frame.sort_values('NETWORTH')
    weights = ordered.WGT.cumsum()
    return float(ordered.NETWORTH.iloc[weights.searchsorted(weights.iloc[-1] / 2)])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true', help='redownload cached sources')
    args = parser.parse_args()
    raw = ROOT / 'data' / 'raw'
    records, manifest = [], []
    download(BASE + 'files/bulletin.macro.txt', raw / 'bulletin.macro.txt', args.refresh)
    for year in YEARS:
        page_url = BASE + ('scfindex.htm' if year == 2025 else f'scf_{year}.htm')
        page = download(page_url, raw / f'scf_{year}.html', args.refresh).decode()
        if '2025 dollars' not in page:
            raise ValueError(f'{year}: source no longer confirms 2025 dollars; inspect before combining vintages')
        url = BASE + f'files/scfp{year}excel.zip'
        payload = download(url, raw / f'scfp{year}excel.zip', args.refresh)
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            names = [n for n in archive.namelist() if n.lower().endswith('.csv')]
            if len(names) != 1:
                raise ValueError(f'Unexpected archive contents: {archive.namelist()}')
            frame = pd.read_csv(archive.open(names[0]))
        frame.columns = frame.columns.str.upper()
        iid = 'Y1' if 'Y1' in frame else 'X1'
        frame = frame[[iid, 'WGT', 'NETWORTH', 'EDCL']].copy()
        frame['implicate'] = frame[iid].astype(int) % 10
        if set(frame.implicate) != {1, 2, 3, 4, 5}:
            raise ValueError(f'{year}: unexpected implicate identifiers')
        if frame[['NETWORTH', 'WGT', 'EDCL']].isna().any().any() or (frame.WGT <= 0).any():
            raise ValueError(f'{year}: invalid values or weights')
        if not set(frame.EDCL).issubset({1, 2, 3, 4}):
            raise ValueError(f'{year}: unexpected education codes')
        sizes = frame.groupby(frame[iid].astype(int) // 10).size()
        if not sizes.eq(5).all():
            raise ValueError(f'{year}: expected five records per family')
        for group, codes in [('college', [4]), ('high_school_or_less', [1, 2])]:
            selected = frame[frame.EDCL.isin(codes)]
            estimates = []
            for _, imp in selected.groupby('implicate'):
                estimates.append((weighted_median(imp), float((imp.NETWORTH * imp.WGT).sum() / imp.WGT.sum())))
            records.append(dict(year=year, group=group, dollar_year=2025,
                                median_net_worth=sum(x[0] for x in estimates) / 5,
                                mean_net_worth=sum(x[1] for x in estimates) / 5))
        manifest.append(dict(year=year, url=url, documentation=page_url,
                             sha256=hashlib.sha256(payload).hexdigest(), records=len(frame),
                             families=len(sizes), dollar_year=2025))
        print(f'{year}: {len(sizes):,} families')
    out = ROOT / 'data'
    pd.DataFrame(records).to_csv(out / 'wealth_by_education.csv', index=False)
    (out / 'sources.json').write_text(json.dumps(dict(
        retrieved_utc=datetime.now(timezone.utc).isoformat(), sources=manifest,
        method='WGT-weighted median and mean within each implicate, then average over five implicates; no standard errors.'), indent=2) + '\n')


if __name__ == '__main__':
    main()
