# SPDX-License-Identifier: MPL-2.0
"""Human-readable presentation of exactly the three retained SCI01 analyses."""

from html import escape


def _table(headers, rows):
    return '<table><thead><tr>' + ''.join('<th>' + escape(str(x)) + '</th>' for x in headers) + '</tr></thead><tbody>' + ''.join(
        '<tr>' + ''.join('<td>' + escape(str(x)) + '</td>' for x in row) + '</tr>' for row in rows) + '</tbody></table>'


def _number(value):
    return 'unavailable' if value is None else f'{value:.8g}'


def render_report(summary, matched, representation):
    if not matched:
        return ('<!doctype html><html lang="en"><meta charset="utf-8"><title>SCI01 matched analysis unavailable</title>'
            '<h1>No matched comparison is available</h1><p>All assigned pairs and their missing prerequisites remain in '
            '<a href="unavailable-pairs.json">the unavailable-pair census</a>. No reversal or mechanism is established.</p>'
            '<p><a href="summary.json">Complete summary</a></p></html>').encode()
    groups = sorted({r['group_id'] for r in matched})
    labels = {group: 'G' + str(i + 1) for i, group in enumerate(groups)}
    method_rows = [r for r in summary['by_method_horizon'] if r['horizon'] == 64]
    reduced = next(r for r in method_rows if r['comparison'] == 'INPUT_KRYLOV48' and r['population'] == 'ALL_RETAINED')
    gated = next(r for r in method_rows if r['comparison'] == 'INPUT_KRYLOV48' and r['population'] == 'ORIGINAL_NUMERICAL_GATES_PASS')
    reversal_groups = {r['group_id'] for r in matched if r['comparison'] == 'INPUT_KRYLOV48' and r['horizon'] == 64
                       and r['both_endpoints_improve_contrast_worsens'] and r['numerically_evaluable']}
    if gated['both_endpoints_improve_contrast_worsens']:
        finding = (f"Matched H64 reduced-model reversals occur in {gated['both_endpoints_improve_contrast_worsens']} of "
            f"{gated['cells']} cells passing the original numerical gates, across {len(reversal_groups)} independent groups. "
            'In these cells, both endpoint errors decrease while the error in their contrast increases.')
    else:
        finding = ('The matched H64 census does not establish the stronger reduced-model conjunction among cells passing the original numerical gates. '
                   'Retain the narrower contrast finding and the complete endpoint contingency table.')
    parts = ['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">',
        '<title>E4/SCI01 — three matched retained analyses</title><style>',
        'body{font:16px/1.55 system-ui,sans-serif;max-width:1200px;margin:40px auto;padding:0 24px;color:#18222e;background:#fafafa}',
        'h1,h2,h3{line-height:1.2}h2{margin-top:48px;border-top:2px solid #b7c9d8;padding-top:18px}',
        'table{border-collapse:collapse;width:100%;font-size:13px;margin:18px 0;background:white}',
        'th,td{padding:9px;border-bottom:1px solid #d9dfe5;text-align:right}th:first-child,td:first-child{text-align:left}',
        'th{background:#eaf0f5}code,pre{font-family:ui-monospace,monospace}pre{background:#eaf0f5;padding:18px;overflow:auto}',
        '.finding{padding:20px;border-left:5px solid #235b76;background:#e9f2f5}.small{font-size:13px;color:#52606c}',
        '</style><body><h1>E4/SCI01: three matched retained analyses</h1>',
        '<p>This report analyses the retained E4/SCI01 evidence. It preserves signed contributions and complete denominators. '
        'Use the linked cell tables and arrays to inspect each result.</p>',
        '<p class="finding">' + escape(finding) + '</p>',
        f"<p>H64 is primary; H128 is a stress diagnostic. The source contains {summary['assigned_cases']} assigned cases, "
        f"{summary['original_usable_cases']} available calculations and {summary['NO_ORIGIN']} NO_ORIGIN cases. "
        f"The {summary['assigned_pairs']} assigned pairs contain {summary['usable_pairs']} usable pairs in "
        f"{summary['usable_independent_groups']} independent groups and {summary['unavailable_pairs']} unavailable pairs. "
        'Panels, views, channels and coordinates are nested observations.</p>',
        '<p>Exactly three analyses were performed. No native trajectory, fitted model, new basis or additional update was acquired. '
        'Original scientific results and numerical failures retain their scopes.</p>',
        '<p><a href="specification.md">Analysis specification</a> · <a href="source-bindings.json">Source bindings</a> · '
        '<a href="summary.json">Complete summaries</a> · <a href="unavailable-pairs.json">Unavailable pairs</a></p>',
        '<h2>1. Matched-cell reversal census</h2>',
        '<p>Each comparison fixes the parameter pair, physical force, nominal group receiver, action, block, panel, view and horizon. '
        'Errors are endpoint block norms on that instrument. No separate maxima or receiver menus enter the comparison.</p>',
        '<p>The four requested events overlap: contrast improvement can accompany any endpoint category. '
        'The JSON summaries include exhaustive contingency tables and arithmetic ties.</p>']
    parts.append(_table(('H64 comparison / population', 'Cells', 'Both improve; contrast worsens', 'One improves; other worsens',
                         'Both worsen', 'Contrast improves', 'Numerical failures retained'),
        ((r['comparison'] + ' / ' + r['population'], r['cells'], *(r[k] for k in (
            'both_endpoints_improve_contrast_worsens', 'one_improves_other_worsens', 'both_endpoints_worsen',
            'contrast_improves', 'numerically_unevaluable_cells'))) for r in method_rows)))
    parts.append('<p>All retained reduced cells contain ' + str(reduced['both_endpoints_improve_contrast_worsens']) +
                 ' reversals. The gate-qualified table preserves the original horizon-specific numerical exclusions.</p>')
    parts.append('<h3>Distribution across the four independent groups</h3>')
    parts.append(_table(('Comparison / group', 'Retained / gate-qualified cells', 'Both improve; contrast worsens',
                         'One improves; other worsens', 'Both worsen', 'Contrast improves'),
        ((r['comparison'] + ' / ' + labels[r['group_id']], f"{r['retained_cells']} / {r['cells']}",
          *(r[k] for k in ('both_endpoints_improve_contrast_worsens', 'one_improves_other_worsens',
                          'both_endpoints_worsen', 'contrast_improves'))) for r in summary['by_group']
         if r['horizon'] == 64 and r['population'] == 'ORIGINAL_NUMERICAL_GATES_PASS')))
    parts.append('<h3>H64 channels, all retained cells</h3>')
    parts.append(_table(('Comparison / action / block', 'Cells', 'Both improve; contrast worsens', 'Mixed endpoints',
                         'Both worsen', 'Contrast improves'),
        ((r['comparison'] + ' / ' + r['action'] + ' / ' + r['block'], r['cells'],
          *(r[k] for k in ('both_endpoints_improve_contrast_worsens', 'one_improves_other_worsens',
                          'both_endpoints_worsen', 'contrast_improves'))) for r in summary['by_channel']
         if r['horizon'] == 64 and r['population'] == 'ALL_RETAINED')))
    parts.extend(['<p><a href="matched-cells.csv">Matched-cell scalar CSV</a> · <a href="matched-cells.json">Complete signed endpoint vectors</a></p>',
        '<h2>2. Signed error-alignment accounting</h2>',
        '<pre>e = predicted − native\nS = ||e_H||² + ||e_L||²\nA = 2〈e_H,e_L〉\nD = ||e_H − e_L||² = S − A\nΔD = ΔS − ΔA</pre>',
        '<p>Positive ΔS increases endpoint energy. Positive −ΔA reduces signed alignment and increases contrast error. '
        'Opposing terms retain their signs. These deterministic inner products are not estimates of statistical covariance.</p>',
        '<p>The table sums matched changes within each channel. Cell-level classifications remain in the export. '
        'The sums describe nested observations; they do not establish independent statistical precision.</p>'])
    parts.append(_table(('H64 comparison / action / block', 'Σ ΔS', 'Σ −ΔA', 'Σ ΔD', 'Worsened-contrast contributors'),
        ((r['comparison'] + ' / ' + r['action'] + ' / ' + r['block'],
          _number(r['sum_delta_endpoint_energy']), _number(r['sum_loss_of_alignment_contribution']),
          _number(r['sum_delta_contrast_squared']), str(r['worsened_contrast_contributions']))
         for r in summary['by_channel'] if r['horizon'] == 64 and r['population'] == 'ALL_RETAINED')))
    parts.extend(['<h2>3. Post-checkpoint representation accounting</h2>',
        '<pre>d_N = I_N + G_N\nI_N = M^(N−τ) d_τ\nG_N = Σ M^(N−1−k) (ML − LR) z_k\ne_reduced,Δ = e_full,Δ − C(d_H − d_L)</pre>',
        '<p>M is the actual full BAOAB map. R is composed from the projected Hessian, and L lifts the retained reduced states. '
        'R is not replaced with LᵀML. Both models continue their own checkpoint states.</p>',
        '<p>I propagates representation error present at the checkpoint. G accumulates representation error generated after the checkpoint. '
        'Each signed term is projected onto the common receiver before the high-minus-low contrast.</p>',
        '<p>This accounts for FULL-minus-reduced response. FULL itself remains an approximation to the native response. '
        'The export also verifies the signed join to the full and reduced native-reference contrast errors.</p>',
        '<h3>H64 paired receiver contributions, all retained cells</h3>'])
    parts.append(_table(('Regime / action / block', 'Σ ||IΔ||²', 'Σ ||GΔ||²', 'Σ 2〈IΔ,GΔ〉', 'Σ ||IΔ+GΔ||²', 'Negative cross terms / cells'),
        ((r['regime'] + ' / ' + r['action'] + ' / ' + r['block'],
          *(_number(r['sum_' + f]) for f in ('inherited_squared', 'generated_squared',
             'twice_inherited_generated_alignment', 'full_minus_reduced_squared')),
          f"{r['negative_cross_terms']} / {r['cells']}") for r in summary['representation_by_channel']
         if r['horizon'] == 64 and r['population'] == 'ALL_RETAINED')))
    parts.extend(['<p><a href="representation.csv">Representation scalar CSV</a> · '
        '<a href="representation.json">All signed endpoint and paired contributions</a> · '
        '<a href="independent-checks.json">Independent state checks</a></p>',
        '<h3>Verification and interpretation</h3>',
        '<p>Maximum normalized saved-state reconstruction residual: ' + _number(summary['maximum_normalized_state_reconstruction_residual']) +
        ' against 1e-10. Maximum native-error join residual: ' + _number(summary['maximum_native_representation_join_residual']) +
        '. Maximum alignment-change identity residual: ' + _number(summary['maximum_alignment_identity_residual']) + '.</p>',
        '<p>The checkpoint information requirement includes the baseline observation, any unavailable prefix and required operator information. '
        'One update does not mean one cheap scalar measurement. '
        'Original costs are retained in <a href="original-calculation-costs.json">calculation costs</a> and '
        '<a href="original-assessment-costs.json">assessment costs</a>.</p>',
        '<p>Weak-channel ratios remain diagnostic. No new relative adequacy threshold, molecular bound or claim of scientific qualification is introduced.</p>',
        '<h3>H128 stress diagnostic</h3>'])
    parts.append(_table(('Comparison / population', 'Cells', 'Both improve; contrast worsens', 'Mixed endpoints', 'Both worsen', 'Contrast improves'),
        ((r['comparison'] + ' / ' + r['population'], r['cells'], *(r[k] for k in ('both_endpoints_improve_contrast_worsens',
            'one_improves_other_worsens', 'both_endpoints_worsen', 'contrast_improves')))
         for r in summary['by_method_horizon'] if r['horizon'] == 128)))
    parts.append(_table(('Label', 'Original independent group'), ((labels[g], g) for g in groups)))
    parts.append('<p class="small">Exact per-case input arrays and derived maps are indexed in source-bindings.json. '
                 'The completion receipt binds every report and data member. Original results remain unchanged.</p></body></html>')
    return '\n'.join(parts).encode()
