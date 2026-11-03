# Parent-anchored plant prediction precursor v1

SPDX-License-Identifier: CC-BY-4.0

This protocol selects an inexpensive candidate-sensitive prediction component toward the full Rubisco programme. It does not replace the required consequential EL comparison or high-specificity nomination. All natural training and plant-mutant outcomes have already been exposed to the investigators. Freeze this computational design before fitting/prediction; software commitment does not create fresh biological evidence.

## Scientific question and exact inputs

Does a natural-plant LSU sequence predictor, anchored to the measured exact A369 bacterial parent, predict both intrinsic mutant point responses better than predicting no change across the complete nine-mutant panel?

Natural training is Iqbal et al., *Predicting plant Rubisco kinetics from RbcL sequence data using machine learning*, DOI 10.1093/jxb/erac368. The acquired primary XML has 177,420 bytes, SHA-256 `77c7bb857c26132820123d70ad356deb36124b162300f124784df6eddadbdd0f`. Original supplementary training workbook has 35,582 bytes, SHA-256 `bbd449d86c96297acf6351cf184464ceb23cbc1f42535beff4fce8b0dcd7bbc0`, native workbook fingerprint `7e778dc69a2d1c8d958a7cf1ac18b8895201a951bf56bb45fb5a0862b61fabee`. Sheet1 rows 2..184 retain 183 species associations, 132 unique LSU sequences, 86 genera and 17 native citation strings. Kcat has 165 means, specificity 170; 155 rows have both. Missing endpoint cells remain missing. Original sequence strings use twenty uppercase amino acids and lengths 422–485. Do not discard shorter sequences, replace native associations or merge duplicated sequences into independent biological units.

Workbook fields are A species, B accession, C native taxonomy, D sequence database, E/F turnover mean/SD, G/H specificity mean/SD, I/J adjusted aerobic affinity mean/SD, K cached sequence length, L citation, M year and N sequence. Preserve native cells and formulas. The workbook has no unit row: the primary paper supplies s⁻¹ turnover, mol/mol specificity and in-vitro 25 °C/pH near 8 context. Its conversions of SE to SD and assumptions about missing/ranged counts do not authenticate biological n or assay covariance. No SD-derived weighting or coverage claim is used here. The native tobacco row 112 has V369, turnover 3.1 and specificity 80; its 477-aa sequence independently matches the inspected native-V369 P00876 view. The assessment parent instead has A369.

The assessment source is the sealed McDonald2026 panel, fingerprint `23e913faf1c50f6e4afbbbbe642521e4894e32c891eb1d913eac1107862a73d0`. Use its S8-derived 477-aa A369 LSU and constant 123-aa SSU. The focal denominator is exactly I251L, T391C, T391I, T391V, A438R, I465V, N468D, N468Q and A470R. Retain the six site groups 251/391/438/465/468/470. A369V is a separately required diagnostic. Leaf specificity is missing, and the plant-fusion assembly is a different view; neither enters the focal denominator.

## Frozen conventional method

Implement the published inexpensive **unweighted Levenshtein KNN** family using maintained RapidFuzz 3.14.3, uniform insertion/deletion/substitution costs 1, processor None and no distance cutoff. Use raw native LSU strings; no MSA, protein-model weights or unreviewed object arrays are needed. This is a declared adaptation of the published comparator, not reproduction of the paper's best ESM GP. The public fitted GP/embedding/notebook operands are currently missing. No unlicensed source code is copied.

For each endpoint separately, retain every source row with a nonmissing positive mean. Candidate k values are fixed to 1, 3, 5, 9, 15, 31. Tune only on natural data using leave-one-genus-out assessment. In each fold, all rows of the held genus leave training together. Select the lowest mean genus-level absolute error; break exact score ties toward smaller k. Also retain the fixed k=1 comparator. Report every k's complete natural cross-validation errors; these are model diagnostics on source associations, not independent biological calibration.

For every query, sort neighbours by exact integer distance. Include the entire distance tie at the kth boundary; average their raw endpoint means with equal row weights. Retain every neighbour row, distance, boundary and complete tie membership. Different species/source rows with identical sequences remain correlated source associations. Their counts do not establish biological replication. This explicit tie policy and genus tuning differ from incompletely specified published defaults and must not be hidden.

For each positive model output m and observed parent endpoint y, forecast:

`forecast(mutant) = y(parent) × m(mutant LSU) / m(A369-parent LSU)`.

The parent/no-change comparator forecasts the measured parent for every case. Natural means/SDs are not replaced by the assessment's parent values during fit. No mutant outcome participates in natural fitting, k selection or feature preprocessing. Anchoring can cancel a common multiplicative level bias; it does not establish causal mutation accuracy. Refuse absent/nonpositive outputs instead of clamping them into valid kinetics.

Retain the natural model's unanchored outputs as well. Commit all nine focal forecasts, the A369V diagnostic, chosen k values, natural tuning tables and neighbour rosters before the evaluation function accesses mutant endpoint labels. Source parsing may already have exposed those labels; report that distinction. No adaptive arm or EL construction is asserted in this precursor.

## Assessment, cost and interpretation

Report absolute endpoint error, absolute log error and parent–mutant log-contrast error for every method/case/endpoint. Summarize both the nine rows and the six equally weighted sites; keep endpoints separate. Preserve A369V as a diagnostic outside both focal summaries. Show T391I individually. Its specificity mean change is unresolved; a successful turnover prediction does not establish specificity preservation.

Retain complete feature/distance/neighbour equality checks. If parent and mutant neighbourhoods produce identical model values, the anchored method collapses to no change. That result rejects its discrimination in this panel rather than supplying a working kinetic predictor. An LSU-only model necessarily gives identical inputs for a Galdieria parent and SSU-only I95M; this protocol cannot support that edit.

Compare the two-endpoint error vectors against parent/no-change without compensating one endpoint's error with the other. Lower error on both endpoints and informative turnover contrasts would justify further assessment of this cheap relation within the exact exposed panel. A trade-off, equality or poor prediction retains its negative/limited disposition. No retrospectively chosen 10%/3% gate, biological bootstrap, nominal mutation coverage, general predictive accuracy or EL advantage follows. Source mean/SD sensitivity may be reported as a conditional perturbation, without treating SD as a confidence interval or inventing endpoint covariance.

The finite workload is all natural rows/genera/k values, three methods (parent, fixed 1NN, genus-selected KNN), nine focal mutants and one diagnostic. Cap pure computation at 10 CPU-minutes and 128 MiB retained analytical output; no GPU, large weights or new biological measurements. Record producing source/lock/library versions, actual time, all original/protocol digests and software forecast/evaluation ordering. Any changed roster, fit rule or metric creates a successor protocol before its execution.

This component can expose whether inexpensive natural-sequence transfer supplies useful mutant feedback. Failure identifies a response-relation gap; it is not proof of biological impossibility. Success would still require stronger applicability/transport assessment and the full programme's fair consequential EL comparison. Phases 2–9 remain open until their complete scientific gates hold.
