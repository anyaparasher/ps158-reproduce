"""First figure: python plot.py (requires pandas and matplotlib).
Run get_data.py first. Point estimates only; no design-based error bars.
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd

ROOT = Path(__file__).resolve().parent


def main():
    data = pd.read_csv(ROOT / 'data/wealth_by_education.csv')
    wealth = data.pivot(index='year', columns='group', values='median_net_worth')
    if wealth.isna().any().any() or list(wealth.index) != list(range(1989, 2026, 3)):
        raise ValueError('Expected complete 1989–2025 series')
    gap = wealth.college - wealth.high_school_or_less
    ratio = wealth.college / wealth.high_school_or_less
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                         'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.8), gridspec_kw={'width_ratios': [1.4, 1]})
    for group, label, color in [('college', "Bachelor’s or higher", '#176b89'),
                                ('high_school_or_less', 'High school/GED or less', '#d47531')]:
        axes[0].plot(wealth.index, wealth[group], label=label, color=color, marker='o', lw=2.4, ms=4)
    axes[0].set_title('Median family net worth', loc='left', fontsize=13)
    axes[0].legend(frameon=False, loc='upper left')
    axes[1].plot(gap.index, gap, color='#6e4b83', marker='o', lw=2.4, ms=4)
    axes[1].set_title('Dollar gap between group medians', loc='left', fontsize=13)
    for ax in axes:
        ax.set_ylim(bottom=0)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${x / 1000:,.0f}k'))
        ax.set_xticks([1989, 1998, 2007, 2016, 2025])
        ax.grid(axis='y', alpha=.18)
        ax.set_axisbelow(True)
        ax.set_xlabel('Survey year')
    fig.suptitle('The US wealth gap by education, 1989–2025', x=.07, ha='left', fontsize=19, weight='bold')
    fig.text(.07, .88, 'Inflation-adjusted 2025 dollars • Education of the family reference person', color='#555555')
    fig.text(.07, .04, 'Source: Federal Reserve, Survey of Consumer Finances public summary extracts. All families; some college excluded.\nWeighted medians computed within each of five implicates, then averaged. Descriptive estimates; no confidence intervals.', fontsize=9, color='#555555')
    fig.subplots_adjust(left=.07, right=.97, top=.79, bottom=.19, wspace=.27)
    out = ROOT / 'outputs'
    out.mkdir(exist_ok=True)
    fig.savefig(ROOT / 'figure.png', dpi=180)
    fig.savefig(out / 'wealth_gap.png', dpi=180)
    plt.close(fig)
    summary = wealth.assign(gap=gap, ratio=ratio)
    summary.to_csv(out / 'figure_data.csv')
    print(summary.round(2).to_string())


if __name__ == '__main__':
    main()
