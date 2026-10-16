# US wealth gap by education, 1989–2025

`figure.png` plots median family net worth and the gap between families whose reference person has a bachelor’s degree or higher and those with high school/GED or less. Amounts are in 2025 dollars; some college/associate degrees are excluded. All SCF families are included, not only parents.

Data are downloaded from the Federal Reserve’s [Survey of Consumer Finances](https://www.federalreserve.gov/econres/scfindex.htm) public summary extract CSV files for all 13 survey waves, 1989–2025. Estimates use survey weights within each of five imputations, then average the results. This is an original descriptive figure from the source data, not a reproduction of a specified published image; it has no confidence intervals.

To rerun with Python 3.10+ and `curl`: install `pandas` and `matplotlib`, then run `python get_data.py` followed by `python plot.py`. Downloads are cached in `data/raw/`; `python get_data.py --refresh` downloads them again. The plot script writes `figure.png` and supporting outputs in `outputs/`.
