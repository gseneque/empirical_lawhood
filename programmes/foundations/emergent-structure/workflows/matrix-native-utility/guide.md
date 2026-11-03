# Assess native factor-response utility

SPDX-License-Identifier: CC-BY-4.0

Programme: [Emergent structure — stochastic matrices](../../README.md).

This guide selects an independent native E2 response assessment.
It compares FACTOR with declared origin-mechanical response descriptions.
Start with the [specification](specification.example.json) and freeze its missing scientific selections before acquisition.

## Prerequisites

Use the existing locked main environment and an explicit EL storage profile.
Select at least four distinct physical cores, with one numerical thread per worker.
Keep inputs, temporary files and outputs on EL.
The [environment guide](../../../../../docs/development/maintainer-environment.md) gives the selected host profile.

The example has replacement root and protocol identities and no utility criterion.
It therefore stops before lowering or native contact.
Select the actual independent population, horizon, comparator set, improvement margin, paired-view resolution, null probability, alpha and usable-unit requirement.
These choices belong in the typed specification.
The original 0.01 response-adequacy threshold does not select an improvement margin.

The amended programme selects `NativeAmendedUtilityCriterion` with
`MatrixOriginResponseModel` and the complete 29-check assay in the
[dense response specification](../../records/matrix-dense-response.md).
Its two fixed primary questions are paired FACTOR adequacy through tick 32
(tolerance 0.01, null success probability 0.8) and FACTOR's cumulative error
advantage through tick 128 over **each** of GENERIC_SLOW, IO48 and SPECTRA
(strict margin 0.001, null success probability 0.5).
The common comparison requires both numerical views and a maximum absolute
PRIMARY/FINE loss discrepancy of 0.0001 for FACTOR and every challenger.
Each test uses alpha 1/160. With 96 assigned roots, their critical success
counts are respectively 87 and 61. An unavailable challenger cannot create a win.

Supply an ordinary input selector containing one canonical `NativeUtilityRequest` under the key `request`.
The request binds actual reserved sources, exposure support, paired response panels, the mathematical protocol, template publications and operational resources.
Its sources have their own E2 purpose and complete root census.
E3 TRAIN output does not supply independent E2 confirmation.
The request's explicit worker selection must equal the public execution selection.

## First action

Copy and edit the example on EL.
Use the [configuration guide](../../../../../docs/using/configuration.md) for exact typed input bindings and validation.
Use the [public lifecycle](../../../../../docs/reference/cli.md) through `campaign experiment-explain`, `experiment-prepare`, `experiment-author`, `experiment-run`, `experiment-read` and `experiment-recover`.
Give `experiment-prepare` a new report path with `--output`.
Select `--workers 4` for preparation, authoring, execution and recovery.
The [programme](../matrix-programme/guide.md) accepts this protocol in its `e2` slot.

## Output and stops

Each root retains its native prefix, causal check, frozen forecast, native responses and complete paired score.
The terminal result retains all assigned roots, adverse comparisons and nonuse.
FACTOR, FULL_COUPLED, GENERIC_SLOW, NORM_RADIUS and SPECTRA use the same causal observation scope.
The amended assay also retains IO48 and ZERO_RESPONSE under that scope.
FULL_COUPLED is the origin-linearized reference with its declared phase capacity.
Its name does not establish an unrestricted optimal predictor.

Full public reads authenticate original custody, replay received native operands and compare the utility reduction.
A full read may retain an incomplete assessment after an authenticated closed `BLOCKED` or `FAILED` terminal.
Every assigned root remains in the original denominator.
Actual scores retain their original outcomes.
Missing roots retain exact unknown-contact, refusal or failure custody.
They count as zero usable units and zero successes.

Amended reads expose `amended_primary_tests` with both exact binomial tails,
assigned-root counts, known failures, unknown events and critical counts.
Unknowns remain distinct from observed failure and count as nonsuccesses in
each operational test. Descriptive 95% intervals enclose the possible true
success probability across all completions of unknown events; complete-case
intervals are explicitly conditional on assessability. The root records also
retain joint adequacy-and-advantage and FACTOR-adequate/ZERO-inadequate events.
These diagnostics do not replace either primary test.

This readout establishes neither a complete native assessment nor scientific qualification.
Compact reads authenticate output manifests and hash every retained output body, while scientific decoding and assessment remain deferred.
Partial reads retain their explicit deferred scientific state.
Completed recovery must retain the original receipts and enter no executor.
If exhausted or uncertain prerequisites prevented operational closure, select
`campaign experiment-recover --authoring-dir /path/to/original-authored --custody-only`
without worker, retry or issued-authority options. This initial development
path authenticates the retained producing provenance and current reader,
refuses any still-executable task, and closes only proved exhausted custody.

It retains missing descendants as not attempted and defers scientific assessment.
Follow it with an explicit full `experiment-read` for the complete root accounting.
Development completion and conditional comparison arithmetic establish neither sampling warrant nor scientific qualification.
