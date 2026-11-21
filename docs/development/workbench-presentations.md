# Add a bounded result presentation

SPDX-License-Identifier: CC-BY-4.0

This guide gives instructions for registered result presentations.
It keeps scientific meaning and current custody with their owning readers.
Use the mass-balance presentation as a bounded extension example.

## Existing owners and prerequisites

Read the [extension recipe](extending-the-engine.md) and [workbench architecture](workbench-architecture.md).
Select the installed scientific reader and its exact supported record revisions.
Reuse its current access, original source, receipt, product and final byte checks.
A presentation cannot supply a missing reader, acquisition permission or scientific interpretation.

The [mass-balance composition](../../src/empirical_lawhood/api/domain_composition/mass_balance_starter/application_presentation.py)
uses the original prepared-development reader.
Its complete census contains one to sixteen independent units.
The [opportunity composition](../../src/empirical_lawhood/api/domain_composition/assigned_opportunity/application_presentation.py)
uses the original dependent-assessment reader.
Its opportunities and nested views retain their original dependence root.
Both routes inspect exposed development results without starting workers.
The [Rubisco composition](../../src/empirical_lawhood/api/domain_composition/rubisco_response/application_presentation.py)
reads the original conditional root and complete requirement graph. Separate
companion reads join its inquiry, work account, standalone assessment and
contribution through their existing owners.

The separate [preparation-response composition](../../src/empirical_lawhood/api/domain_composition/rubisco_preparation_response/application_presentation.py)
registers `rubisco.preparation-response` at revision `1.0.0`.
It reads prefix, response, independent analysis and destination-supply waves through their domain owners.
Its [bounded observer](../../src/empirical_lawhood/api/domain_composition/rubisco_response/preparation_observation.py) reads original execution and publication metadata.
These extensions reuse the shared presentation and observation contracts.

## Register the presentation

1. Add `application_presentation.py` beside the selected API domain composition.
2. Export one exact `ApplicationPresentation` as `APPLICATION_PRESENTATION`.
3. Declare its unique panel ID, panel revision, title, route, guide, data columns and maximum complete record count.
4. Supply a reader with the `context`, `directory` and `artifact_writer` arguments.
5. Return `PresentationData` with the original identity, scope, complete summary, rows, original report and provenance.

Use [ApplicationPresentation](../../src/empirical_lawhood/api/application_presentations.py)
for the exact contract.
The descriptor's `workflow_id` labels its documented domain route.
It does not register a scientific workflow or change its identity.
Keep a selected draft's byte limit and exact domain check before its full scientific read.
The shared [bounded selector](../../src/empirical_lawhood/api/application_development.py)
reuses the original authored-package loader.

Keep quantities, units, signed values, uncertainty, missingness and complete denominators in the owning report.
Do not calculate new science in the presentation.
Use plain field names for columns.
Browser data cannot select JavaScript, HTML, Python imports or templates.
Static declarations must not inspect prerequisites or open records.

Regenerate the extension aggregate, executable aggregate and CLI reference in their required order:

```sh
uv run --no-sync python scripts/generate_extension_projections.py --json
```

The existing closed descriptor discovery generates
[the presentation aggregate](../../src/empirical_lawhood/api/generated_application_presentations.py).
Duplicate panel IDs, invalid callbacks and unsafe descriptor paths refuse.
Examine the generated diff.
Use the supported wheel and source-distribution build procedure.
A scientific input file or imported certificate cannot install a presentation.

## Open original findings

Follow the [operator guide](../using/research-workbench.md) to select an engine, storage and original directory.
Select **Registered findings**, then an installed presentation.
Choose **Open result**.
The browser uses the existing durable invocation service.
An exact-record inspection or filter performs another current owning read.

The terminal client accepts the same request:

```json
{
  "schema": "empirical-lawhood/application/request",
  "version": "1.0.0",
  "request_id": "inspect.original.presentation.01",
  "context_id": "retained.study",
  "operation": "presentation.read",
  "parameters": {
    "directory": "/absolute/original-authoring-directory",
    "panel_id": "mass-balance.findings",
    "panel_version": "1.0.0",
    "limit": 50
  }
}
```

Use `presentation.list` for static installed descriptions.
It opens no scientific record or storage plane.
The request's panel version selects presentation compatibility only.
It does not change the canonical scientific record revision.

An unsupported panel revision uses the same current scientific reader.
The response then supplies an identifiable generic field/value view of its original report.
An unknown panel ID refuses before storage access.
An unsupported scientific revision or failed current-access check still refuses through its owner.
The generic fallback cannot bypass those refusals.

The existing four MiB response bound and 200-row page bound remain active.
Filtering preserves the complete denominator and original summary.
The final byte check occurs before a projection returns.
No persistent scientific response cache is created.

## Verify the changed boundary

### Explorer and observation extensions

`PresentationData.exploration` optionally supplies the versioned
`empirical-lawhood/application/exploration` contract. Its complete node/edge
census, original identities, requirements, scoped states, findings, methods and
declared layout remain data. The validator bounds 4096 complete nodes and 8192
edges; the UI displays sixteen nodes and thirty-two edges per window and at most
eight expansion levels. Unsupported exploration revisions retain the original
generic presentation after the same owning read.

Relationships carry original source, direction, kind and scope. Supported kinds
are requires, candidate supply, assessed supply, admitted supply, lineage,
successor, informing reference and classification. A declaration cannot infer
one kind from another. Preserve repeated origins, alternative branches, absent
consumer admission and unknown later updates.

For a selected six-question result, `question_readouts` retains Q1–Q6 in order.
Each row separates acquisition, authentication, independent assessment and
disposition, plus original quantity, uncertainty, complete denominator, evidence
and consequence. Keep source cutoff, nested views, unsuccessful and unanswered
cases in those fields. An empty roster means that this original has no such
result; `pending_bindings` identifies records or bindings not supplied by that original.
It does not report repository-wide implementation availability.

The conditional-root panel's M50 markers concern results outside its original two-operation contract.
The separate preparation-response panel retains all six rows before acquisition, with explicit unavailable findings and complete denominators.
Their presence establishes neither completed assessment nor molecular acquisition.
The UI supplies no molecular calculation or checkpoint assessment.
Only layout `rubisco-joint-root` uses conditional-root requirement counts and case/endpoint headings.
Generic exploration layouts render their supplied summary, rows, work coverage and exact records.
Each node's source fingerprint must identify that node's canonical record; an assessment's fingerprint cannot stand in for an individual question.
Edges can separately retain the parent assessment as their source.
The preparation-response Method tab uses declared source and protocol references.

Named method metadata selects only packaged Python sources and explicit guide
members in the matching source distribution. Inspection reopens the original
and current source before returning bounded bytes, digests and declared symbols.
Current source, original producing implementation and dated native runtime
evidence retain separate labels. Audit attachments are never canonical members.

`ApplicationPresentation` also accepts optional `observation_version` and
`observe(context, directory, artifact_writer, selection)` fields. Both must be
present together. Revision `1.0.0` returns the finite
`empirical-lawhood/operational/domain-observation` contract. It preserves the
original run and packet, nested positions, selected effects, allowances and
complete-return census. Prefix allowance and return counts are cumulative across the original ledger,
including retained continuation input. Selected response counts cover that wave only.
Unknown new contact keeps the total unavailable until an independent readout is published.
The callback must read actual original metadata; it
cannot acquire work or poll a full scientific reconstruction. Unsupported
bindings return the shared explicit unavailable shape.

The domain observation can include `runtime` with `observed_gpu`, `utilisation`,
`memory`, `process` and `native_phase`. Each unavailable value is `null`.
The same object requires `observed_utc`, `worker_source_sha256` and an original
`source` identity. The collector preserves that observation and its time.
It refuses a changed worker source or telemetry without its domain source.
The UI displays this timestamp separately from snapshot receipt time.
This extension does not perform provider or device polling.

Rubisco's safe-checkpoint reader, response assessor, destination assessor and domain callback are implemented.
The [acceptance register](../../programmes/biology/photosynthesis/workflows/rubisco-response/preparation-response-v1.md#implementation-and-retained-acceptance)
separates installed component evidence from pending complete lifecycle and deployment acceptance.
Prefix controls retain four positions; response-observation controls retain twenty original software returns.
Their producer and reader source identities remain distinct.
The actual molecular investigation still has six unanswered questions.
Re-negotiate the selected installation and accept its complete collector, transfer, read and original-return routes before paid scientific work.

Run focused registration, revision fallback, exact-value, denominator and current-access controls.
Reuse original retained results for installed terminal and browser comparisons.
Keep positive, adverse and unevaluable findings inspectable.
Verify that final byte changes refuse after projection construction.
Record browser interaction separately from backend conformance.
Automated checks establish neither newcomer adoption nor scientific qualification.
