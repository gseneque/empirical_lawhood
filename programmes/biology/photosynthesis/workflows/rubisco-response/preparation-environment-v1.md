# Paired preparation and environmental dependence

SPDX-License-Identifier: CC-BY-4.0

This specification defines the bounded environmental extension of the paired preparation investigation.
It tests a fixed formation-force receiver under a pure environmental displacement.
Declare the environmental support before acquiring primary response information.

## Prerequisites and first selection

Read the [paired preparation specification](preparation-response-v1.md), [programme guide](guide.md) and [conditional root](initial-root-v1.md).
Retain the actual root assessment, original molecular inputs and their existing contribution custody.
Select the locked controller and worker environments, operator profile and explicit external destinations.
The existing spending supervisor and evidence-return route remain required for a separately authorized acquisition.

This extension replaces the additional local direction and mixed finite challenge.
It does not add another panel or another molecular operator.
The original local design remains available under its existing schema and meaning.
An already exposed local design does not become an unexposed environmental design.

The selected case remains M1, `keto-hie`, `AS_CONSTRUCTED`, at one common catalytic site.
The receiver is

\[
R_m(x)=-u_m^\mathsf{T}\nabla E_m(x),
\]

where \(u_m\) is the normalized formation-coordinate gradient at genotype \(m\)'s initial checkpoint.
Keep that receiver direction fixed at both checkpoints.
Preparation order is an information order, not physical time.
The four positions remain nested observations within one matched construction, with zero independent biological replicates.
The original four materials, 32 sites and 384 starting hypotheses remain in the denominator.

## Prospective environmental support

Declare the retained local region and eligible environmental atoms before the primary response acquisition.
The default support is common, unchanged protein outside the selected retained/QM core.
It excludes each whole protein residue touched by that core.
The three reaction-coordinate atoms are excluded in both genotypes.
The selection excludes solvent, mutation-specific atoms and other nonprotein atoms.

The default region is `COMMON_PROTEIN_OUTSIDE_SELECTED_SITE_CORE`.
For a smaller declared region, select `SELECTED_COMMON_PROTEIN_RESIDUES` with sorted logical chain and sequence-position pairs.
An explicit selection refuses absent, mutated, noncommon or excluded residues.
Both arms must retain the same residue chemistry, atom-name census, elements, natural masses, charges and parameter types.
They must also retain the same logical covalent neighbors and bond orders.
The bounded map excludes protein residues with covalent connections to nonprotein atoms.

The bounded transport contract permits at most 4096 eligible atoms.
An all-common selection above that limit refuses before acquisition.
It never truncates the atom map or selects the largest couplings.
For a larger construction, prospectively select a physically meaningful explicit residue region within that limit.
This capacity limit is a processing boundary, not a scientific accuracy threshold.
The original molecular inputs are required to select and validate the actual residue list.

For an interface or small-subunit hypothesis, declare that region before observing its response.
Do not search all remaining atoms and then call the largest response an I95M mechanism.
A nearby chemical neighbor, construction strain or numerical error can otherwise determine the selection.
The claim must remain limited to the declared decomposition.

The support binds the complete original representation and preparation identities in both genotypes.
Its common map binds logical residue and atom identities to each arm's actual physical atom indices.
Prefix preparation reconstructs the complete support from those original models, preparations, prototypes and formation coordinates.
An equal atom count, shared atom name or caller-supplied map does not establish that correspondence.

The original periodic cells and Cartesian axes must agree.
The mapped initial coordinates must agree within the prospective tolerance.
The default maximum component discrepancy is \(10^{-6}\) Å.
The bounded contract permits no tolerance above \(10^{-4}\) Å.
It performs no fitted alignment, periodic wrapping or translation to rescue an invalid map.
Later coordinates do not select or rotate the direction.

Use Euclidean Cartesian normalization for this static assay.
Do not apply a mass transform merely because the wider programme concerns dynamics.
A dynamical object would require its own mathematical and physical contract.

## Prepare the environmental design

Use the maintained operator recipe before `prepare-prefix`:

```sh
uv run --no-sync python scripts/operate_preparation_response.py prepare-environment-design \
  --context /absolute/path/to/application-context.json \
  --request /absolute/path/to/environment-design-request.json \
  --operator-profile /absolute/path/to/operator-profile.json
```

Select these request fields:

| Field | Required selection |
| --- | --- |
| `output_directory` | A fresh absolute destination beneath the selected storage root. |
| `design_file` | The original unentered local design parameters, including the paired prefix and formation coordinates. |
| `model_files` | Exact `m1-i95m` and `m1-wt` entries, each with original `preparation`, `prototype` and `representation` files. |
| `region` | Optional region name. Its default is `COMMON_PROTEIN_OUTSIDE_SELECTED_SITE_CORE`. |
| `residue_keys` | Sorted `[chain_id, sequence_position]` pairs for `SELECTED_COMMON_PROTEIN_RESIDUES`. |
| `coordinate_tolerance_angstrom` | Optional exact Decimal encoded as a JSON string, such as `"0.000001"`. |

The recipe returns `environment-design.json` and a support review.
The review identifies the region, residue keys, eligible atom count, exclusions and coordinate tolerance.
Review that actual selection before prefix authoring.
The recipe performs no force call or molecular acquisition.

Use the returned design file with the original `prepare-prefix` operation and its complete original-input request.
The environmental design has a distinct `rubisco-preparation-environment-design` configuration consumer.
Preserve the original local design and its canonical bytes.
Do not hand-author the environmental identity or a nomination.

The `review_response_initial_geometry` function refuses an environmental design before nomination.
Its local mixed-displacement review cannot describe a direction that has not yet been selected.

## Finite acquisition and stages

| Stage | Native returns | Public stage name |
| --- | ---: | --- |
| Same paired preparation prefix | Up to 10 | Existing paired prefix |
| Initial primary actions, both scales and signs, both genotypes | 8 | `initial-primary` |
| Independent nomination and freezing of one common direction | 0 | Initial response analysis |
| Later primary actions and both signs of the environmental action | 12 | `environment-diagnostic` |
| Four withheld pure environmental challenges | 4 | `challenge` |
| **Core total** | **Up to 34** | |
| Optional environmental half-scale refinement | 4 | `additional-refinement` |

The twelve-return environmental diagnostic contains eight later primary returns and four later environmental returns.
The optional refinement retains the same direction and adds both signs at half scale for both later checkpoints.
The complete acquisition uses at most 38 native returns when the optional refinement is selected.
Failed and rejected native returns retain their original cost and assigned denominator.
The optional refinement remains a separately selected purchase within the remaining financial allowance.
Nomination and analysis use no new molecular calls, but their processing and storage remain in the shared cost account.

## Nominate once from initial WT information

The public preparer checks coordinate correspondence before authoring the eight initial effects.
An invalid map refuses this acquisition before any new force call.
Use `assess` with `response_directories=[]` to retain that negative result from the original prefix checkpoints.
The resulting nomination retains `INVALID_COORDINATE_CORRESPONDENCE`, including when no primary action exists.

For a valid map, acquire and independently assess the complete eight-effect `initial-primary` stage.
Use its retained full Cartesian actions at both declared scales.
The nomination uses the fine-scale initial WT action:

\[
r=P_{\mathrm{eligible}}K_{W,0,h/2}u_W,
\qquad
d_W=\frac{r}{\lVert r\rVert}.
\]

The nomination retains the original action identities and selected support.
Transfer the same signed components to I95M through the authenticated common-atom map.
Keep this one direction fixed across both genotypes and both checkpoints.
Do not optimize another direction for the mutant or the later state.

The nomination must precede every environmental diagnostic and finite challenge.
Its input contains no environmental return, later action or withheld outcome.
The initial I95M returns remain part of the complete assigned acquisition but do not select the direction.

Retain a negligible projected response, invalid correspondence or consequential scale sensitivity as a negative or unavailable selection outcome.
These outcomes block dependent environmental work.
The extension has no automatic fallback to the original bond-sum direction.
A different support or fallback requires a distinct prospective design and its own inquiry decision.
Do not retry a failed scientific selection as an operational repair.

| Nomination disposition | Meaning and permitted continuation |
| --- | --- |
| `AVAILABLE` | Complete initial evidence supports one fixed candidate within the selected empirical numerical allowance. |
| `UNAVAILABLE_INITIAL_ACTIONS` | The complete two-arm, two-scale primary evidence is unavailable. Retain its original missing or failed returns. |
| `INVALID_COORDINATE_CORRESPONDENCE` | Mapped initial coordinates exceed the prospective tolerance. Do not align them after observing the actions. |
| `NEGLIGIBLE_PROJECTED_RESPONSE` | The projected norm is at most \(10^{-12}\) hartree/bohr², or its amplitude-scaled magnitude is within the numerical allowance. |
| `NUMERICALLY_UNRESOLVED` | At least one initial selected-direction scale discrepancy exceeds that allowance. |

Only `AVAILABLE` permits the dependent environmental diagnostic.
The negligible label concerns this selected numerical allowance and intervention.
It does not bound every physical environmental response.

## Pure environmental challenge

At each nested position, apply

\[
x'_m=x_m+\alpha d_m,
\qquad
\widehat{\Delta R}_m=-\alpha d_m^\mathsf{T}K_{m,h/2}u_m.
\]

All three reaction-coordinate atoms remain at their original coordinates.
The local reaction geometry therefore remains unchanged.
The local description that discards environmental dependence predicts zero receiver change.
The description that retains the selected cross coefficient predicts the specified signed change.
The original withheld complete-force return discriminates between those predictions.

The environmental challenge has no \(1/\sqrt{2}\) mixed-direction factor.
Its scalar floor is zero.
The additional action and finite challenge use the same frozen environmental direction.
Freeze all four predictions from the complete independent diagnostic before authoring any challenge.

This test concerns whether the local description can serve the receiver without the declared interface information.
It does not prove that a large joint state must be retained.
One economical cross coefficient may suffice.
The revised design gives up the original finite bond-compression challenge and its direct formation-coordinate nonlinearity test.

## Empirical numerical controls

Use the retained full primary actions to assess, at every relevant state,

\[
\alpha\left|d_m^\mathsf{T}
\left(K_{m,h}u_m-K_{m,h/2}u_m\right)\right|.
\]

This requires no additional native calls.
A selected full-vector residual can amplify noise that was small in the original local projections.
The same selected-direction condition applies at both initial and both later states.

The later environmental actions provide an independent reciprocal comparison:

\[
u_m^\mathsf{T}K_{m,h}d_m
\approx d_m^\mathsf{T}K_{m,h}u_m.
\]

Multiply the absolute discrepancy by \(\alpha\) to compare it with the receiver's numerical allowance.
The selected allowance remains the original fraction of the work-equivalent response tolerance.
Its default fraction is 0.1.

Consequential projected or reciprocal discrepancy blocks the withheld challenge.
Select the optional half-scale environmental returns only when they can resolve the remaining question within the spending allowance.
They do not add another direction or preparation recipe.
The readout retains the original coarse discrepancy beside the refined reciprocal comparison.
A favorable fine-scale comparison does not erase consequential coarse/fine sensitivity or supply a rigorous accuracy certificate.

Native-force uncertainty remains unavailable unless a separate supported source supplies it.
Two-scale agreement and reciprocity are empirical consistency checks, not rigorous error enclosures.
They do not validate the chemical model or identify a finite-response mismatch uniquely as nonlinearity.
The original selected work-equivalent tolerance and paired-error convention remain unchanged.
They supply no activation-energy, turnover or specificity error bound.

## Inquiry, custody and retained outcomes

Use the existing preparation, inquiry, contribution, array and complete-force owners.
After checkpoint admission, select `prepare-response` with `stage="initial-primary"` and no diagnostic locators.
Execute and export through the ordinary inquiry route.
Use `assess` with the complete initial response directory and its original contributions.
The independent analysis publishes the nomination, including a negative or unavailable disposition.
Use `read-analysis` to inspect that original assessment.
There is no separate hand-authored nomination step.

For `stage="environment-diagnostic"`, select the original initial analysis as `diagnostic_directory` and its exported `diagnostic_contribution`.
The preparer reconstructs the nominated frames from that assessment.
After its returns, assess both response directories together.
Use the cumulative assessment and its contribution for the challenge's diagnostic locators.
The challenge preparer freezes predictions after the complete twenty-return diagnostic passes its empirical numerical condition.
The optional refinement also uses the original cumulative assessment and the ordinary consequential-work decision.

Each stage retains its own original effect identities and complete assigned census.
A later environmental frame must not rewrite the original initial-primary points or their primary-frame identities.
Independent analysis joins their unchanged receiver direction to the nominated environmental direction.

Preserve the complete supplier and decision history at every successor.
Reconstruct nomination from authenticated original action arrays.
Do not hand-author a direction, omit an unfavorable initial arm, or replace a readout with a scalar summary.
Keep failed and unentered effects visible in final coverage.
Completed-work recovery supplies no new native contact.

Report the original six questions with their complete nested denominators.
The coupling question now concerns the declared environmental support.
Keep numerical consistency, finite-response adequacy, signed pairing and preparation benefit separate.
A small observed signal remains distinct from a useful improved predictor.

## Acceptance and remaining requirements

Portable analytical and custody controls establish software behavior only.
They do not acquire molecular evidence or authorize a remote allocation.
The earlier R3 installed-lifecycle and R4 processing/staging requirements retain their original open scope.
Select acceptance against the final changed source and actual original inputs before rental.
Retain the independent spending supervisor and complete evidence-return requirements.

The reconstruction delivery selects initial tests and conformance checks only.
Final local lifecycle and complete focused-suite validation remain with the repository owner.
Results from an earlier, lost workspace do not establish acceptance of reconstructed bytes.

## References and research

The [paired preparation specification](preparation-response-v1.md) retains the original receiver, tolerances, six questions and historical acceptance scopes.
The [environment support owner](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/preparation_response_environment.py) defines the prospective map and deterministic nomination.
The [response preparation API](../../../../../src/empirical_lawhood/api/domain_composition/rubisco_response/preparation_response.py) composes the supported stage route.
The [independent assessment](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/preparation_response_assessment.py) retains full actions, frozen predictions and negative outcomes.
The [verification guide](../../../../../docs/development/testing.md) separates software controls from scientific and deployment acceptance.
