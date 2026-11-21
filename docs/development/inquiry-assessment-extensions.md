# Add an inquiry author and dependent assessment

SPDX-License-Identifier: CC-BY-4.0

This guide gives the contract for a bounded inquiry author and its independent assessor.
It preserves original dependence, information limits and the complete assigned denominator.
Use the exposed example before adding a domain method.

## Prerequisites and first action

Select the [locked development environment](../using/environments.md).
Read the [supported extension interfaces](extension-interfaces.md) and [inquiry procedure](../using/recursive-inquiry.md).
Select the executing source, an operator profile and a new external artifact destination.
The example uses the base environment and two pure operations.
It performs no native acquisition.

The source record declares one dependent sequence, four assigned opportunities and two nested views per opportunity.
The views and opportunities do not become additional independent units.
All example evidence is exposed and nonpromotable.
The source declaration supplies no physical independence or qualification.

Run the authoring recipe from the selected checkout:

```sh
uv run --no-sync python scripts/examples/assigned_opportunity_assessment.py author \
  --project-root /selected/checkout \
  --operator-profile /work/operator-profile.json \
  --output-directory /selected/artifact-root/opportunity-positive \
  --case positive
```

Use the returned `authoring_directory` with the ordinary execution command:

```sh
uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign recursive-development-run \
  --authoring-dir /selected/artifact-root/opportunity-positive/wave

uv run --no-sync python scripts/examples/assigned_opportunity_assessment.py read \
  --project-root /selected/checkout \
  --operator-profile /work/operator-profile.json \
  --authoring-directory /selected/artifact-root/opportunity-positive/wave
```

The report retains the original source, method, consumer, denominator and exact fraction bounds.
It reports procedure, instance, admission and joined-use findings separately.
Its `qualification` remains `NOT_ESTABLISHED` for every result.

Select a new destination for each other case: `adverse`, `insufficient`, `interrupted` or `unevaluable`.
The `interrupted` input describes interrupted observations within the original assigned census.
That input does not demonstrate an actual interrupted software invocation.
An actual interruption retains its original operational attempt through the ordinary recovery owner.
Use `read --allow-partial` to inspect that attempt without execution.
This route authenticates compact custody and retains the complete operational and assigned opportunity censuses.
It reports scientific completion as `DEFERRED` and supplies no scientific disposition.
Use the ordinary read for the complete typed assessment after execution settles.
Repeat the original execution command only through its supported recovery decision.

## Existing owners and added records

The [shared contract module](../../src/empirical_lawhood/design/inquiry_methods.py) composes existing canonical identities, allocations, quantities, clocks and multiplicity records.
It does not add a scheduler, decoder framework, input-access service or general authoring algorithm.
The [example declarations](../../src/empirical_lawhood/methods/assigned_opportunity_assessment/bindings.py) use `RecursiveOperationDeclaration`, `RecursiveScientificHooks` and `RecursiveInquiryHooks`.
Registration and generated aggregates retain their existing owners.

| Record | Required meaning |
| --- | --- |
| `InquiryMethodEvidence` | Exact original record, information role, availability and any later-release reference |
| `InquiryAuthorContract` | Author implementation, authoring mode, missing-condition hypotheses, output specification, permitted method family, composition bound, cutoff and activation |
| `FrozenInquiryConsumer` | Exact consumer identity, code-owned parameter rule and finite permitted parameter bounds |
| `FrozenInquiryProcedure` | Original author contract, selected methods and committed parameter values |
| `AssignedInquiryOpportunity` | Assigned opportunity, original dependence root, independent unit and nested views |
| `FixedOpportunityStopping` | Complete fixed assignment and exact assessment cutoff, with no outcome-based stop |
| `DependentAssessmentContract` | Exact assessor revision, estimand, scope, outcome bounds, allocation, opportunities, evidence roles, stopping, multiplicity, missingness and frozen consumer |

The shared contract supports at most 256 opportunities, 32 units, 32 inputs and 16 parameter coordinates.
Its method composition permits at most 16 operations.
The example narrows these limits to one root, 16 opportunities, two views and one selected assessment method.
Each canonical example input or output has a 512 KiB limit.
These limits describe this extension contract, not the generic graph capacity.

`UnitAllocation` retains the original independent-unit census.
The opportunity contract refuses division of one identical root across differently labelled independent units.
The domain must also authenticate that mapping against its original source records.
Different labels or hashes alone do not establish physical independence.

Existing controller consumers, two-ordinal plans and trajectory plans retain their narrower scientific meanings.
The example does not reinterpret their records as a generic dependent-sample evaluator.
Existing implementation-lineage records also retain their separate meaning.

## Authoring mode and information boundaries

The mode distinguishes four author activities:

| Mode | Meaning |
| --- | --- |
| `INVESTIGATOR_RECIPE` | Instantiate the supplied admissible recipe |
| `INTERNAL_SELECTION` | Select within a declared finite method family |
| `INTERNAL_SPECIFICATION` | Supply a specification through an implemented author |
| `PROCEDURE_CONSTRUCTION` | Construct a procedure through an implemented bounded author |

The example implements only `INVESTIGATOR_RECIPE`.
It refuses the other modes instead of claiming an unimplemented algorithm.
Another domain must register its actual implementation and scientific validation for those activities.

The author receives the source roster and requested threshold through its actor input port.
It receives no outcome table or evaluator diagnostics.
Actual availability must precede the author cutoff even when the input declares an earlier causal phase.
The activation coordinate retains its native units, frame and origin.
A changed clock requires its existing explicit transport contract.

The assessor receives the immutable procedure and the exact evaluator outcome table.
Both operations use separate registered input ports.
These ports form a trusted implementation boundary, not a sandbox against hostile Python code.
Current access and later release remain with their existing application and source owners.
A release reference records a dependency and grants no permission by itself.

The permitted parameter rule allows thresholds from zero through one.
The actual threshold remains fixed in each returned procedure.
A later threshold selection produces another author contract, procedure and claim identity.
It cannot revise the earlier forecast or the original consumer join.

## Finite assessment and missing outcomes

The estimand is the equal-weight mean over the complete original assigned opportunity census.
Its scope does not include an unobserved population or later opportunities.
The declared outcome interval is `[0, 1]`.
Both nested numerical views must agree before an observed value enters the sum.
Invalid values and inconsistent views remain visible and make the joined finding unevaluable.

Let `N` denote the complete assigned count and `m` the unresolved count.
Let `S` denote the sum of accepted observed values.
The exact finite-census enclosure is:

```text
lower = S / N
upper = (S + m) / N
```

The implementation uses exact rational arithmetic.
The result retains reduced integer numerators and denominators.
Independent tests enumerate all endpoint completions to check the lower and upper extrema.
These bounds require no independence assumption and are not population confidence intervals.
Multiplicity is explicitly `NOT_APPLICABLE` for this deterministic single predicate.

`RETAIN_OUTCOME_BOUNDS` includes unresolved assignments throughout the enclosure.
`UNEVALUABLE` additionally prevents a joined decision when any opportunity is missing or interrupted.
Neither rule drops an assignment or substitutes a finite-only mean.
The fixed stopping record permits no outcome-driven truncation or repeated acquisition.

| Condition | Joined disposition |
| --- | --- |
| Lower bound reaches the frozen threshold | `SATISFIED` within the declared finite scope |
| Upper bound is below the threshold | `FALSIFIED` within the same scope |
| Bounds straddle the threshold | `UNEVALUABLE`, with insufficient evidence retained |
| Invalid outcome meaning or the selected strict missingness rule applies | `UNEVALUABLE`, with original reasons and assignments |

Procedure, instance and admission findings assess their stated supplied-contract joins.
Their success cannot replace the independent joined-use result or establish physical preparation support.
Operational completion remains a separate software status.

## Register, verify and retain

Keep native science and interpretation in the domain extension.
Use the existing scientific-root validator to compare the complete original design, inputs and information roles.
Use `assessment_projector` for the existing four `AssessmentPhase` values.
Use `inquiry_claim_assessment_projector` for the exact current target claim.

The example projector verifies the original procedure, result, producing receipts and complete assigned census.
It recomputes the bounded arithmetic from retained observations.
It refuses changed consumer, cutoff, root, evidence-role and assessment-revision joins.
An unsupported claim returns no projection.
The public inquiry service repeats authentication at commitment and current readback.

Use [record revision selection](record-revisions.md) when the scientific interpretation changes.
Keep the original decoder, contract, result and receipt.
Later evidence informs a separately authored successor through the existing inquiry lifecycle.
It never rewrites an earlier commitment or converts exposed evidence into fresh confirmation.

Run only the affected bounded controls:

```sh
uv run --no-sync pytest -q --fail-on-skip tests/test_assigned_opportunity_assessment.py
```

Select external temporary and cache destinations as required by the operator profile.
The focused tests include disclosed receipt stand-ins for isolated projection controls.
Those stand-ins supply no custody or scientific authority.
Installed lifecycle acceptance must separately exercise real original receipts and actual interruption recovery.
