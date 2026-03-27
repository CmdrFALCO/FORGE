"""
Statistical tests for AXIOM Phase 5 analysis.
All tests use scipy.stats and statsmodels for multiple comparison correction.
"""

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.contingency_tables import mcnemar
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint


def wilson_ci(successes, n, alpha=0.05):
    """Wilson score interval for binomial proportion."""
    if n == 0:
        return 0.0, 0.0, 0.0
    lo, hi = proportion_confint(successes, n, alpha=alpha, method='wilson')
    return successes / n, lo, hi


def mcnemar_test(paired_a, paired_b):
    """
    McNemar's test on paired binary outcomes.
    paired_a, paired_b: arrays of 0/1 (e.g., unsupervised valid, supervised valid).
    Returns: statistic, p_value, odds_ratio, contingency table.
    """
    a = np.asarray(paired_a).astype(float)
    b = np.asarray(paired_b).astype(float)

    # Drop pairs where either is NaN
    valid_mask = ~(np.isnan(a) | np.isnan(b))
    a = a[valid_mask].astype(int)
    b = b[valid_mask].astype(int)

    if len(a) == 0:
        return {'statistic': np.nan, 'p_value': 1.0, 'odds_ratio': np.nan,
                'table': np.zeros((2, 2), dtype=int), 'note': 'No valid pairs'}

    # Contingency table: [both_pass, a_pass_b_fail], [a_fail_b_pass, both_fail]
    both_pass = np.sum((a == 1) & (b == 1))
    a_pass_b_fail = np.sum((a == 1) & (b == 0))
    a_fail_b_pass = np.sum((a == 0) & (b == 1))
    both_fail = np.sum((a == 0) & (b == 0))

    table = np.array([[both_pass, a_pass_b_fail],
                       [a_fail_b_pass, both_fail]])

    # Discordant cells
    b_disc = a_pass_b_fail
    c_disc = a_fail_b_pass

    if b_disc + c_disc == 0:
        return {'statistic': np.nan, 'p_value': 1.0, 'odds_ratio': np.nan,
                'table': table, 'note': 'No discordant pairs'}

    # Use exact binomial if discordant count < 25
    if b_disc + c_disc < 25:
        result = mcnemar(table, exact=True)
    else:
        result = mcnemar(table, exact=False, correction=True)

    # Odds ratio: c/b (improvement ratio)
    odds_ratio = c_disc / b_disc if b_disc > 0 else np.inf

    return {
        'statistic': result.statistic,
        'p_value': result.pvalue,
        'odds_ratio': odds_ratio,
        'table': table,
        'discordant_improved': int(c_disc),
        'discordant_regressed': int(b_disc),
        'note': None
    }


def wilcoxon_test(paired_a, paired_b):
    """
    Wilcoxon signed-rank test on paired continuous outcomes.
    Returns: statistic, p_value, median_diff, rank_biserial_r.
    """
    a = np.asarray(paired_a, dtype=float)
    b = np.asarray(paired_b, dtype=float)
    diff = b - a

    # Remove zeros for Wilcoxon
    nonzero = diff[diff != 0]
    if len(nonzero) == 0:
        return {'statistic': np.nan, 'p_value': 1.0, 'median_diff': 0.0,
                'rank_biserial_r': 0.0, 'note': 'All differences are zero'}

    try:
        stat, p = stats.wilcoxon(a, b, alternative='two-sided')
        # Rank-biserial correlation: r = 1 - (2*W) / (n*(n+1)/2)
        n = len(nonzero)
        r_rb = 1 - (2 * stat) / (n * (n + 1) / 2)
    except Exception as e:
        return {'statistic': np.nan, 'p_value': np.nan, 'median_diff': float(np.median(diff)),
                'rank_biserial_r': np.nan, 'note': str(e)}

    return {
        'statistic': float(stat),
        'p_value': float(p),
        'median_diff': float(np.median(diff)),
        'rank_biserial_r': float(r_rb),
        'note': None
    }


def chi_square_independence(contingency_table):
    """
    Chi-square test of independence on a contingency table.
    contingency_table: 2D array or DataFrame.
    Returns: chi2, p_value, dof, expected, cramers_v.
    """
    table = np.asarray(contingency_table, dtype=float)
    if table.min() < 0:
        return {'chi2': np.nan, 'p_value': np.nan, 'dof': np.nan,
                'cramers_v': np.nan, 'note': 'Negative values in table'}

    # Check for zero rows/cols
    if np.any(table.sum(axis=0) == 0) or np.any(table.sum(axis=1) == 0):
        return {'chi2': np.nan, 'p_value': np.nan, 'dof': np.nan,
                'cramers_v': np.nan, 'note': 'Zero marginal in table'}

    chi2, p, dof, expected = stats.chi2_contingency(table)

    # Cramer's V
    n = table.sum()
    k = min(table.shape) - 1
    cramers_v = np.sqrt(chi2 / (n * k)) if k > 0 and n > 0 else 0.0

    return {
        'chi2': float(chi2),
        'p_value': float(p),
        'dof': int(dof),
        'expected': expected,
        'cramers_v': float(cramers_v),
        'note': None
    }


def holm_bonferroni(p_values, alpha=0.05):
    """
    Holm-Bonferroni correction for multiple comparisons.
    Returns: reject (bool array), corrected_p_values.
    """
    p_arr = np.asarray(p_values, dtype=float)
    # Handle NaN
    valid_mask = ~np.isnan(p_arr)
    if valid_mask.sum() == 0:
        return np.full(len(p_arr), False), p_arr.copy()

    reject_out = np.full(len(p_arr), False)
    corrected_out = np.full(len(p_arr), np.nan)

    valid_p = p_arr[valid_mask]
    reject, corrected, _, _ = multipletests(valid_p, alpha=alpha, method='holm')

    reject_out[valid_mask] = reject
    corrected_out[valid_mask] = corrected

    return reject_out, corrected_out


def per_constraint_mcnemar(df_unsup, df_sup, constraint_ids, prompt_ids):
    """
    Run McNemar's test for each constraint, comparing unsupervised vs supervised.

    df_unsup, df_sup: DataFrames with columns prompt_id + constraint pass/fail.
    constraint_ids: list of constraint IDs to test.
    prompt_ids: list of prompt IDs to include.

    Returns: DataFrame with results per constraint.
    """
    results = []
    for cid in constraint_ids:
        col = f'c_{cid}_passed'
        if col not in df_unsup.columns or col not in df_sup.columns:
            results.append({
                'constraint_id': cid,
                'unsup_fail_rate': np.nan,
                'sup_fail_rate': np.nan,
                'p_value': np.nan,
                'odds_ratio': np.nan,
                'note': 'Column not found'
            })
            continue

        merged = pd.merge(
            df_unsup[['prompt_id', col]].rename(columns={col: 'unsup'}),
            df_sup[['prompt_id', col]].rename(columns={col: 'sup'}),
            on='prompt_id', how='inner'
        )
        merged = merged[merged['prompt_id'].isin(prompt_ids)]

        if len(merged) == 0:
            results.append({
                'constraint_id': cid,
                'unsup_fail_rate': np.nan,
                'sup_fail_rate': np.nan,
                'p_value': np.nan,
                'odds_ratio': np.nan,
                'note': 'No matching prompts'
            })
            continue

        unsup_pass = merged['unsup'].values
        sup_pass = merged['sup'].values

        unsup_fail_rate = 1 - unsup_pass.mean()
        sup_fail_rate = 1 - sup_pass.mean()

        test = mcnemar_test(unsup_pass, sup_pass)

        results.append({
            'constraint_id': cid,
            'unsup_fail_rate': float(unsup_fail_rate),
            'sup_fail_rate': float(sup_fail_rate),
            'p_value': test['p_value'],
            'odds_ratio': test['odds_ratio'],
            'statistic': test['statistic'],
            'n': len(merged),
            'note': test.get('note')
        })

    df_results = pd.DataFrame(results)

    # Apply Holm-Bonferroni correction
    if len(df_results) > 0 and df_results['p_value'].notna().any():
        reject, corrected = holm_bonferroni(df_results['p_value'].values)
        df_results['p_corrected'] = corrected
        df_results['significant'] = reject
    else:
        df_results['p_corrected'] = np.nan
        df_results['significant'] = False

    return df_results
