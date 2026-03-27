"""
Publication-ready visualizations for AXIOM Phase 5 analysis.
All figures saved as 300 DPI PNGs in forge/experiments/figures/.
"""

import matplotlib

matplotlib.use('Agg')
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# --- Global style setup ---
PALETTE = sns.color_palette("colorblind")
COLORS = {
    'sonnet_unsup': PALETTE[0],   # blue
    'sonnet_sup': PALETTE[1],     # orange
    'haiku_unsup': PALETTE[2],    # green
    'haiku_sup': PALETTE[3],      # red
}
CONDITION_LABELS = [
    'Sonnet 4.6\nUnsupervised',
    'Sonnet 4.6\nSupervised',
    'Haiku 4.5\nUnsupervised',
    'Haiku 4.5\nSupervised',
]
CONDITION_COLORS = [COLORS['sonnet_unsup'], COLORS['sonnet_sup'],
                    COLORS['haiku_unsup'], COLORS['haiku_sup']]


def _setup_style():
    """Set publication-ready matplotlib style."""
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
        'font.size': 12,
        'axes.titlesize': 14,
        'axes.labelsize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'axes.grid': True,
        'grid.alpha': 0.3,
        'grid.color': '#cccccc',
        'axes.axisbelow': True,
        'axes.spines.top': False,
        'axes.spines.right': False,
    })


def _save(fig, name, fig_dir):
    """Save figure and close."""
    path = Path(fig_dir) / name
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  Saved: {path}")


def fig_validity_rate_overall(validity_rates, ci_lo, ci_hi, fig_dir):
    """
    Figure 1: Overall validity rate bar chart with 95% CI error bars.
    validity_rates: list of 4 floats [sonnet_unsup, sonnet_sup, haiku_unsup, haiku_sup]
    ci_lo, ci_hi: list of 4 floats each.
    """
    _setup_style()
    fig, ax = plt.subplots(figsize=(8, 5))

    x = np.arange(4)
    rates = np.array(validity_rates) * 100
    lo = np.array(ci_lo) * 100
    hi = np.array(ci_hi) * 100
    yerr = np.array([rates - lo, hi - rates])

    bars = ax.bar(x, rates, color=CONDITION_COLORS, width=0.6,
                  edgecolor='white', linewidth=0.5)
    ax.errorbar(x, rates, yerr=yerr, fmt='none', ecolor='black',
                capsize=5, capthick=1.5, linewidth=1.5)

    ax.set_xticks(x)
    ax.set_xticklabels(CONDITION_LABELS)
    ax.set_ylabel('Validity Rate (%)')
    ax.set_title('Overall Design Validity Rate by Model and Condition')
    ax.set_ylim(0, 105)

    # Add value labels
    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

    _save(fig, 'fig_validity_rate_overall.png', fig_dir)


def fig_validity_by_celltype(data, fig_dir):
    """
    Figure 2: Grouped bar chart — 3 cell types × 4 conditions.
    data: dict of {cell_type: [sonnet_unsup_rate, sonnet_sup_rate, haiku_unsup_rate, haiku_sup_rate]}
    """
    _setup_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    cell_types = ['pouch', 'cylindrical', 'prismatic']
    cell_labels = ['Pouch', 'Cylindrical', 'Prismatic']
    n_conditions = 4
    bar_width = 0.18
    x = np.arange(len(cell_types))

    for i in range(n_conditions):
        offsets = x + (i - 1.5) * bar_width
        values = [data[ct][i] * 100 for ct in cell_types]
        bars = ax.bar(offsets, values, bar_width, color=CONDITION_COLORS[i],
                      label=CONDITION_LABELS[i].replace('\n', ' '), edgecolor='white', linewidth=0.5)
        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                        f'{val:.0f}', ha='center', va='bottom', fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(cell_labels)
    ax.set_ylabel('Validity Rate (%)')
    ax.set_title('Design Validity Rate by Cell Type and Condition')
    ax.set_ylim(0, 110)
    ax.legend(loc='upper left', framealpha=0.9)

    _save(fig, 'fig_validity_by_celltype.png', fig_dir)


def fig_validity_by_difficulty(data, fig_dir):
    """
    Figure 3: Grouped bar chart — 4 difficulty levels × 4 conditions.
    data: dict of {difficulty: [sonnet_unsup_rate, sonnet_sup_rate, haiku_unsup_rate, haiku_sup_rate]}
    """
    _setup_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    difficulties = ['standard', 'edge_case', 'underspecified', 'contradictory']
    diff_labels = ['Standard', 'Edge Case', 'Underspecified', 'Contradictory']
    n_conditions = 4
    bar_width = 0.18
    x = np.arange(len(difficulties))

    for i in range(n_conditions):
        offsets = x + (i - 1.5) * bar_width
        values = [data.get(d, [0, 0, 0, 0])[i] * 100 for d in difficulties]
        bars = ax.bar(offsets, values, bar_width, color=CONDITION_COLORS[i],
                      label=CONDITION_LABELS[i].replace('\n', ' '), edgecolor='white', linewidth=0.5)
        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                        f'{val:.0f}', ha='center', va='bottom', fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(diff_labels)
    ax.set_ylabel('Validity Rate (%)')
    ax.set_title('Design Validity Rate by Difficulty Level and Condition')
    ax.set_ylim(0, 110)
    ax.legend(loc='upper right', framealpha=0.9)

    _save(fig, 'fig_validity_by_difficulty.png', fig_dir)


def fig_constraint_heatmap(common_data, geo_data, fig_dir):
    """
    Figure 4: Constraint failure rate heatmap.
    common_data: DataFrame with constraint_id as index, 4 condition columns.
    geo_data: dict of {geometry: DataFrame} with same structure.
    """
    _setup_style()

    # Determine layout based on geometry groups
    geo_types = [k for k in ['cylindrical', 'pouch', 'prismatic'] if k in geo_data]
    n_panels = 1 + len(geo_types)
    fig, axes = plt.subplots(1, n_panels, figsize=(4 * n_panels, max(8, len(common_data) * 0.4)),
                              gridspec_kw={'width_ratios': [1] * n_panels})
    if n_panels == 1:
        axes = [axes]

    cond_labels = ['Sonnet\nUnsup.', 'Sonnet\nSup.', 'Haiku\nUnsup.', 'Haiku\nSup.']

    # Common constraints panel
    ax = axes[0]
    if len(common_data) > 0:
        sns.heatmap(common_data * 100, annot=True, fmt='.0f', cmap='RdYlGn_r',
                    vmin=0, vmax=100, ax=ax, cbar_kws={'label': 'Failure Rate (%)'})
        ax.set_xticklabels(cond_labels, rotation=0)
        ax.set_title('Common (C1-C7)')
        ax.set_ylabel('Constraint')

    # Geometry-specific panels
    for idx, geo in enumerate(geo_types):
        ax = axes[idx + 1]
        gdf = geo_data[geo]
        if len(gdf) > 0:
            sns.heatmap(gdf * 100, annot=True, fmt='.0f', cmap='RdYlGn_r',
                        vmin=0, vmax=100, ax=ax, cbar_kws={'label': 'Failure Rate (%)'})
            ax.set_xticklabels(cond_labels, rotation=0)
            prefix_map = {'cylindrical': 'CY', 'pouch': 'PO', 'prismatic': 'PR'}
            ax.set_title(f'{geo.capitalize()} ({prefix_map[geo]}*)')
            ax.set_ylabel('')

    fig.suptitle('Constraint Failure Rate Heatmap', fontsize=14, y=1.02)
    plt.tight_layout()
    _save(fig, 'fig_constraint_heatmap.png', fig_dir)


def fig_retry_flow(retry_data_sonnet, retry_data_haiku, fig_dir):
    """
    Figure 5: Retry flow diagram (simplified stacked bar instead of Sankey).
    retry_data: dict with keys 'attempt_1', 'attempt_2', 'attempt_3', 'attempt_4', 'rejected'
    representing cumulative valid counts.
    """
    _setup_style()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

    for ax, data, title in zip(axes,
                                [retry_data_sonnet, retry_data_haiku],
                                ['Sonnet 4.6 Supervised', 'Haiku 4.5 Supervised']):
        categories = ['Attempt 1', 'Attempt 2', 'Attempt 3', 'Attempt 4', 'Rejected']
        values = [data.get(f'attempt_{i}', 0) for i in range(1, 5)] + [data.get('rejected', 0)]
        colors_flow = [PALETTE[4], PALETTE[5], PALETTE[6], PALETTE[7], PALETTE[3]]

        bars = ax.barh(categories[::-1], values[::-1], color=colors_flow[::-1],
                       edgecolor='white', linewidth=0.5)
        for bar, val in zip(bars, values[::-1]):
            if val > 0:
                ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height() / 2,
                        str(val), ha='left', va='center', fontsize=10, fontweight='bold')
        ax.set_xlabel('Number of Designs')
        ax.set_title(title)
        ax.set_xlim(0, max(values) * 1.2 if max(values) > 0 else 10)

    fig.suptitle('Design Validation: Retry Dynamics', fontsize=14)
    plt.tight_layout()
    _save(fig, 'fig_retry_sankey.png', fig_dir)


def fig_recovery_by_difficulty(data_sonnet, data_haiku, fig_dir):
    """
    Figure 6: Stacked bar — first-attempt valid + recovered + rejected, by difficulty.
    data: dict of {difficulty: {'first_valid': n, 'recovered': n, 'rejected': n}}
    """
    _setup_style()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

    difficulties = ['standard', 'edge_case', 'underspecified', 'contradictory']
    diff_labels = ['Standard', 'Edge Case', 'Underspecified', 'Contradictory']

    for ax, data, title in zip(axes,
                                [data_sonnet, data_haiku],
                                ['Sonnet 4.6 Supervised', 'Haiku 4.5 Supervised']):
        first_valid = [data.get(d, {}).get('first_valid', 0) for d in difficulties]
        recovered = [data.get(d, {}).get('recovered', 0) for d in difficulties]
        rejected = [data.get(d, {}).get('rejected', 0) for d in difficulties]

        x = np.arange(len(difficulties))
        ax.bar(x, first_valid, label='Valid (Attempt 1)', color=PALETTE[0], edgecolor='white')
        ax.bar(x, recovered, bottom=first_valid, label='Recovered (Retries)', color=PALETTE[1], edgecolor='white')
        bottoms = [f + r for f, r in zip(first_valid, recovered)]
        ax.bar(x, rejected, bottom=bottoms, label='Rejected', color=PALETTE[3], edgecolor='white')

        ax.set_xticks(x)
        ax.set_xticklabels(diff_labels, rotation=15, ha='right')
        ax.set_ylabel('Number of Designs')
        ax.set_title(title)
        ax.legend(loc='upper right', fontsize=9)

    fig.suptitle('Recovery by Difficulty Level (Supervised)', fontsize=14)
    plt.tight_layout()
    _save(fig, 'fig_recovery_by_difficulty.png', fig_dir)


def fig_cost_per_valid(costs, fig_dir):
    """
    Figure 7: Cost per valid design bar chart.
    costs: dict of {condition_label: cost_per_valid_usd}
    """
    _setup_style()
    fig, ax = plt.subplots(figsize=(8, 5))

    labels = list(costs.keys())
    values = list(costs.values())

    bars = ax.bar(range(len(labels)), values, color=CONDITION_COLORS[:len(labels)],
                  edgecolor='white', linewidth=0.5, width=0.6)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.001,
                f'${val:.4f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels([lbl.replace(' ', '\n') for lbl in labels])
    ax.set_ylabel('Cost per Valid Design (USD)')
    ax.set_title('Cost per Valid Design by Model and Condition')

    _save(fig, 'fig_cost_per_valid.png', fig_dir)


def fig_constraint_cooccurrence(cooc_matrix, fig_dir):
    """
    Figure 8: Pairwise constraint co-failure heatmap (Jaccard similarity).
    cooc_matrix: DataFrame with constraint IDs as index and columns.
    """
    _setup_style()
    n = len(cooc_matrix)
    fig, ax = plt.subplots(figsize=(max(8, n * 0.5), max(6, n * 0.4)))

    mask = np.triu(np.ones_like(cooc_matrix, dtype=bool), k=1)
    sns.heatmap(cooc_matrix, mask=mask, annot=True, fmt='.2f', cmap='YlOrRd',
                vmin=0, vmax=1, ax=ax, square=True,
                cbar_kws={'label': 'Jaccard Similarity'})
    ax.set_title('Constraint Co-failure Matrix (Jaccard Similarity)')
    plt.tight_layout()
    _save(fig, 'fig_constraint_cooccurrence.png', fig_dir)


def fig_model_comparison_scatter(scatter_data, fig_dir):
    """
    Figure 9: Scatter — x = unsupervised validity, y = supervised validity.
    scatter_data: list of dicts with keys: cell_type, model, unsup_rate, sup_rate.
    """
    _setup_style()
    fig, ax = plt.subplots(figsize=(8, 6))

    markers = {'sonnet': 'o', 'haiku': 's'}
    cell_colors = {'pouch': PALETTE[0], 'cylindrical': PALETTE[1], 'prismatic': PALETTE[2]}

    for d in scatter_data:
        ax.scatter(d['unsup_rate'] * 100, d['sup_rate'] * 100,
                   marker=markers[d['model']], color=cell_colors[d['cell_type']],
                   s=150, edgecolors='black', linewidth=1, zorder=5)

    # Diagonal line (no improvement)
    ax.plot([0, 100], [0, 100], '--', color='gray', alpha=0.5, label='No improvement')

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', markersize=10, label='Sonnet 4.6'),
        Line2D([0], [0], marker='s', color='w', markerfacecolor='gray', markersize=10, label='Haiku 4.5'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=cell_colors['pouch'], markersize=10, label='Pouch'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=cell_colors['cylindrical'], markersize=10, label='Cylindrical'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=cell_colors['prismatic'], markersize=10, label='Prismatic'),
    ]
    ax.legend(handles=legend_elements, loc='lower right')

    ax.set_xlabel('Unsupervised Validity Rate (%)')
    ax.set_ylabel('Supervised Validity Rate (%)')
    ax.set_title('Model Convergence Under Supervision')
    ax.set_xlim(-5, 105)
    ax.set_ylim(-5, 105)

    _save(fig, 'fig_model_comparison_scatter.png', fig_dir)


def fig_prismatic_inversion(data, fig_dir):
    """
    Figure 10: Prismatic inversion — side-by-side bars.
    data: dict with keys: sonnet_unsup, sonnet_sup, haiku_unsup, haiku_sup (rates 0-1).
    """
    _setup_style()
    fig, ax = plt.subplots(figsize=(8, 5))

    x = np.array([0, 1, 3, 4])
    values = np.array([data['sonnet_unsup'], data['sonnet_sup'],
                       data['haiku_unsup'], data['haiku_sup']]) * 100
    colors = [COLORS['sonnet_unsup'], COLORS['sonnet_sup'],
              COLORS['haiku_unsup'], COLORS['haiku_sup']]

    bars = ax.bar(x, values, color=colors, width=0.7, edgecolor='white', linewidth=0.5)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                f'{val:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(['Sonnet\nUnsup.', 'Sonnet\nSup.', 'Haiku\nUnsup.', 'Haiku\nSup.'])
    ax.set_ylabel('Validity Rate (%)')
    ax.set_title('The Prismatic Inversion: Haiku Outperforms Sonnet (Unsupervised)')
    ax.set_ylim(0, 110)

    # Add annotation arrow
    if data['haiku_unsup'] > data['sonnet_unsup']:
        delta = (data['haiku_unsup'] - data['sonnet_unsup']) * 100
        ax.annotate(f'+{delta:.0f} pp',
                    xy=(0, data['sonnet_unsup'] * 100),
                    xytext=(1.5, data['sonnet_unsup'] * 100 + 15),
                    fontsize=12, fontweight='bold', color=PALETTE[3],
                    arrowprops=dict(arrowstyle='->', color=PALETTE[3], lw=2),
                    ha='center')

    _save(fig, 'fig_prismatic_inversion.png', fig_dir)
