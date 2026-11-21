# Check an extension contract

SPDX-License-Identifier: CC-BY-4.0

This guide gives instructions for bounded extension conformance.
It checks selected declarations and disclosed fixtures through existing owning operations.
Use it before the separate installed lifecycle acceptance.

## Prerequisites and first action

Select the [locked environment](../using/environments.md) and [supported interfaces](extension-interfaces.md).
Use the selected checkout or the installed distribution's matching source archive.
Choose a new output directory outside that source.
Do not select real protected inputs, external services or scientific acquisition.

Prepare a trusted local Python file with a `CONFORMANCE_SELECTION` value.
Use `ExtensionConformanceSelection` from `empirical_lawhood.execution.extension_conformance`.
The [editable codec example](../../scripts/examples/extension_conformance.py) supplies a small first fixture.
Copy it to an explicit working path before editing it.
Its unavailable calculation refuses.
Use the [complete development starter](mass-balance-starter.md) for installed author/run/read/recover acceptance.
The command executes this file as Python, including its imports.
It is a developer check, not a sandbox for hostile code.

```sh
uv run --no-sync python -m empirical_lawhood.cli.extension_conformance \
  --fixture /path/to/extension-conformance.py \
  --project-root /path/to/selected-source \
  --output-dir /path/to/new-conformance-packet
```

The selected fixture supplies these explicit operands:

| Operand | Contract |
| --- | --- |
| `namespace` and `schema_prefix` | Owned operation/protocol prefix and `empirical-lawhood/<namespace>/` schema prefix |
| `operations` | One to 64 exact `RecursiveOperationDeclaration` values. Source, certificate and store contract profiles also permit an empty tuple. |
| `protocols` and `bindings` | At most eight ordinary-development protocols and their exact API compositions |
| `imported_record_types` | Explicit reused canonical types outside the owned schema prefix |
| `profile` | An implemented `ConformanceProfile` from the profiles below |
| `cases` | At most 32 disclosed `ConformanceCase` values for the selected executable profile |
| `unmet_prerequisites` | Explicit missing requirements, retained as a nonpassing result |
| `source_access` and `effect_ports` | The continuing-source profile's access owner and one to sixteen named code-owned effect ports |
| `knowledge_types` | The store profile's exact `ScientificTypeDescriptor` tuple, using the existing registry |

Each `ConformanceCase` names one `ConformanceCall`, its exact arguments and the complete expected return value.
For an expected refusal, set `expected` to the exact exception class name.
Set `refusal_contains` to its required nonempty diagnostic.
An unexpected exception fails the case.
A swallowed contact refusal still fails the case.

The runner supplies no replacement registry.
Preparation and scientific reads use the actual installed protocol and runtime binding.
Install a new repository extension through the [extension recipe](extending-the-engine.md) before those checks.
Do not copy canonical scientific identities or grants from another programme.

## Checks and limits

Declaration inspection validates namespace ownership, declaration combinations, exact codec ownership, ports and callback call forms.
It permits same-class codec reuse.
Different implementations of one exact schema and revision refuse.
It constructs no provider and calls no callback.
This explicit conformance operation remains separate from effect-free catalogue discovery.
The report includes the installed [prior-result capacity](prior-result-capacity.md) before any executable case.
Its local member and payload limits establish no source access, independent-unit count or complete memory capacity.

The executable profile uses these owning boundaries:

| Selected call | Existing owner |
| --- | --- |
| `record.roundtrip` | Strict canonical encoder and decoder, with an exact-byte comparison |
| `record.decode-selected-output` | Exact producer selection and strict bounded canonical decoding |
| `experiment.prepare` | `api.experiment_preparation.prepare_experiment` |
| `experiment.validate-instance` | `api.experiment_runtime_bindings.authenticate_experiment_instance` |
| `experiment.read-development` | `api.experiment_scientific_read.read_prepared_development_science` |
| `experiment.complete-development` | `api.experiment_scientific_read.complete_prepared_development_science` |
| `recursive.compile` | `runtime.recursive_compiler.compile_recursive_wave` |
| `recursive.assess` | `runtime.recursive_compiler.project_recursive_assessments` |
| `execution.output-census` | The scheduler's shared complete output-census, byte-budget and check validator |
| `execution.prepare-native-work` | The scheduler's shared initial native-work preparation and strict return validator |
| `source.require-application` | `runtime.continuing_source.require_live_application` |
| `source.sequence-gaps` | `kernel.continuing_source.source_sequence_gaps` |
| `inquiry.require-actor-evidence` | `planning.inquiry_methods.require_actor_evidence` |
| `inquiry.assessment-contract` | The original `DependentAssessmentContract` constructor |
| `knowledge.verify-certificate` | `api.knowledge_certificates.verify_assessment_certificate` |
| `knowledge.dependency-order` | `runtime.knowledge_store.dependency_order` |

The `declaration` profile performs static inspection alone.
The `ordinary-development` profile exercises selected ordinary call sites.

The `isolated-native-contracts` profile requires a native operation, its preparer and its complete unit census.
It permits the listed pure checks and requires an ordinary retained reader for each selected protocol.
Native preparation requires the exact selected callback and manifest, with `context.prepared_invocation` set to `None`.
It validates the original returned parent, typed work and initial nested census.
It cannot select the later worker preflight, process entry or native calculation.
Use the [isolated native starter](isolated-native-starter.md) for separate installed worker and recovery acceptance.

The `record-revisions` profile requires coexisting output revisions and a successful selected-decoder case for each revision.
It also requires an explicit unsupported-producer refusal.
The selected case retains the complete operation census.
Use the [record upgrade guide](record-revisions.md) for the separate retained-source and installed derivative exercise.

The additional service profiles require positive and expected-refusal cases for every listed owning call:

| Profile | Required calls and selected contracts |
| --- | --- |
| `continuing-source-contracts` | Application guard and sequence gaps; exact source, actor, operation and observation codecs; access and effect method signatures |
| `dependent-assessment-contracts` | Actor evidence, assessment contract, compiler and assessment projector; complete selected operations, registered assessment and claim projectors |
| `portable-certificate-read` | Complete original certificate verification and an explicit selected certificate identity |
| `knowledge-store-contracts` | Bounded dependency order, complete selected roots, exact type descriptors and their callback signatures |

A codec round trip alone cannot satisfy these profiles.
Use the [source fixture](../../scripts/examples/continuing_source_conformance.py), [dependent-assessment fixture](../../scripts/examples/dependent_assessment_conformance.py) or [store fixture](../../scripts/examples/knowledge_store_conformance.py).
Pass that fixture to the same bounded command.
Their disclosed operands supply no source grant, producing receipt or scientific qualification.
The dependent example retains an unevaluable joined finding within its complete assigned census.
The store example retains distinct original identities with the same human label.

For an actual certificate, first retain its [original verification report](portable-assessments.md).
Prepare a new fixture from that exact report:

```sh
uv run --no-sync python scripts/examples/portable_certificate_conformance.py \
  --project-root /selected/source \
  --operator-profile /selected/operator-storage.json \
  --expected-report /selected/original-certificate-report.json \
  --output-fixture /selected/new-certificate-conformance.py
```

Pass the returned fixture to the bounded conformance command.
The fixture retains the report's complete expected finding and its original digest.
Verification repeats current custody and the registered assessment without running a producer or worker.
Incomplete inspection cannot satisfy this profile.
The receipt's exposure, authorship and consumer-admission limits remain explicit.

Use complete compiler fixtures to exercise scientific roots and required ports.
Include wrong keywords, wrong returns, missing readers, conflicting codecs and incomplete output censuses.
Preserve absent scientific connections.
Operation names do not establish scientific relationships.

Keep operational completion, inquiry outcome, claim disposition and qualification as separate report fields.
For example, a completed development result can have `useful-supply`, an `UNEVALUABLE` claim and no qualification.
The runner retains the complete disclosed report and its exact digest.
It does not turn these values into a common scientific success flag.

Contact guards refuse provider input delivery, runner construction, scheduler entry, isolated-native entry, subprocesses and network connections.
The command applies these guards during fixture loading and case execution.
The original filesystem inspector's fixed read-only mount diagnostic remains permitted within its owning call.
It retains its five-second and byte bounds, with actual current volume checks.
Direct process calls and altered diagnostic commands still refuse.
Reports retain these storage diagnostics separately from prohibited contact attempts.
The fixture-loading observations include nested case diagnostics; their counts are not additive.
Worker setup observes Python's lazy host description before fixture entry, under the outer process bounds.
The report retains that observation. Guarded cases still refuse direct host-description subprocesses.
Continuing-owner start, ingest and effect submission also refuse.
During case execution, the selected source access, submission and observation ports refuse contact.
Static inspection checks their signatures without calling them.
These development guards do not replace source, input, resource, issue, execution or reveal authorities.

The command uses a separate process with one numerical thread and a 2 GiB address-space limit.
Its default delivery bound is 60 seconds.
`--timeout-seconds` selects an integer from 1 through 120.
The process also has a 120 CPU-second bound, finite output streams and a 256 KiB fixture limit.
These bounds apply only to the disclosed software check.
They change no scientific worker limit or native calculation policy.

## Output and stops

The new packet retains the exact selected fixture, worker output, worker diagnostics and `conformance.json`.
The report binds the actual source census, dependency lock, observed commit and original fixture digest.
It lists executed checks, expected refusals, failures, unmet prerequisites and measured elapsed and CPU time.
A zero exit status means `PASSED_SELECTED_CHECKS` for that exact selection.
An unmet prerequisite, changed source, changed fixture, resource limit or unexpected result gives a nonzero exit status.

Each profile establishes only its selected declaration and call-site checks.
The report keeps `full_installed_lifecycle` false.
Author/run/read/recover acceptance of the editable starter remains a separate required step.
The native contract profile does not establish installed native lifecycle acceptance.
Continuing-source execution, dependent inquiry and two-store exchange require their separate installed lifecycle acceptance.
Certificate conformance reads one selected original package; it does not establish a new consumer's admission.
Prospective lifecycle conformance remains unimplemented in this runner.

Synthetic inputs and these software results supply no scientific qualification or operator authority.
Keep failures beside successful checks.
Continue through the smallest applicable installed lifecycle after the selected contracts pass.
