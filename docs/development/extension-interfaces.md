# Supported extension interfaces

SPDX-License-Identifier: CC-BY-4.0

This guide identifies the supported Python contracts for repository extensions.
It separates callback compatibility, canonical records and scientific admission.
Start with the [v1.0 public interface](../v1.0/public-api.md) and its method or domain recipe.
Use this detailed reference for optional native, scientific and protocol capabilities.

## Prerequisites and first action

Select the checkout or installed distribution through its exact documentation URL.
Use its [locked environment](../using/environments.md) and explicit external output paths.
Retain the selected source and dependency lock with your checks.
Do not copy another programme's scientific identities, grants or exposed results as qualification evidence.

Negotiate the callback API before selecting a lifecycle:

```python
from empirical_lawhood.execution.extension_api import require_extension_callback_api

selected = require_extension_callback_api(minimum="1.0.0", maximum_exclusive="2.0.0")
assert selected == "1.0.0"
```

This pure operation checks only the installed callback API range.
It constructs no provider, inspects no prerequisite and reads no scientific input.
An unsupported range refuses. It never selects a different scientific revision.

Use the separate [bounded conformance runner](extension-conformance.md) for selected executable fixtures.
Its service profiles reuse the original source, dependence, certificate and knowledge dependency validators.
Contract conformance and installed lifecycle acceptance remain separate requirements.
Its base profiles do not establish installed lifecycle acceptance or scientific qualification.
The [mass-balance starter](mass-balance-starter.md) supplies the complete ordinary development route.
The [isolated native starter](isolated-native-starter.md) adds a selected worker and original recovery boundaries.

## Supported imports and construction

The names below are the supported extension surface for callback API version `1.0.0`.
The selected distribution's exact source remains part of the implementation identity.
Other internal imports have no general stability promise.

| Responsibility | Supported module and symbols |
| --- | --- |
| Canonical data | `science.records.serialization`: `CanonicalRecord`; `science.records.decoding`: `decode_canonical_bytes`; `science.identity.provenance`: `ObjectIdentity` |
| Scientific and resource contracts | `science.evidence.evidence`: `ClaimSpec`, `EvidenceCeiling`, `OutcomeAccess`, `VisibilityCeiling`; `science.identity.authority`: `ResourceBudget` |
| Requirement relationships | `science.inquiry.recursive_requirements`: `ScientificRequirementSpec`, `ScientificConnectionSpec`, `RequirementSupplyAssessment`, `ScientificConditionScope` |
| Contribution and target assessment | `science.inquiry.scientific_contributions`: `ContributionManifest`, `ContributionProduct`; `science.inquiry.recursive_claim_assessment`: `InquiryClaimAssessment` |
| Portable assessment certificate | `science.evidence.knowledge_certificates`: `KnowledgeAssessmentCertificate`, `KnowledgeCertificateNotice`, `KnowledgeNoticeKind`; [producer and verifier procedure](portable-assessments.md) |
| Portable knowledge store | `storage.contracts.knowledge_store`: `ScientificTypeDescriptor`, `ScientificTypeRegistry`, `KnowledgeTransferManifest`, `KnowledgeImportReceipt`, `KnowledgeObjectLocator`, `KnowledgeStoreLimits`; [bounded exchange procedure](portable-knowledge-stores.md) |
| Operation construction | `execution.recursive_provider`: `RecursiveOperationDeclaration`, `RecursiveScientificHooks`, `RecursiveInquiryHooks`, `RecursiveExecutionProperties`, `RecursiveInputSupplier` |
| Compiler contracts | `execution.recursive_compiler`: `RecursivePortContract`, `RecursiveScientificRootContext`, `RecursiveScientificRootPreparationContext`, `RegisteredPublicationRequirement`, `RegisteredProvenanceRequirement` |
| Execution and outputs | `execution.execution`: `TaskRunner`, `TaskContext`, `RunnerResult`, `TaskOutputPayload`, `ParentPreparedTaskRunner`; `execution.plans`: `OutputTemplate`, `ScientificStage`, `BarrierKind` |
| Experiment construction | `execution.experiment_preparation`: `ExperimentProtocolDeclaration`, `ExperimentRuntimeBinding`, `ExperimentPreparation`, `PreparedExperimentInputs`, `ExecutionSelection`, `ExperimentInputDerivationResult` |
| Prospective design | `execution.recursive_prospective`: `RecursiveProspectiveDesignInputs`, `RecursiveProspectiveAuthoringSpec` |
| Callback signatures | `execution.experiment_callbacks` and `execution.recursive_callbacks`: the named protocols referenced by the declaration fields |
| Outer composition ports | `execution.experiment_ports`: `ExperimentReport`, `ReadAccessSelection`, `OriginalInputAccess`, `ProspectiveOriginalInputAccess`, `ExperimentServiceContext`, `CompositeProgrammeService` |
| Static registration | `execution.extension_bundles`: `ExtensionBundleContribution`, `ExtensionProfileRegistration`, `ExtensionComponentRegistration`; `execution.executable_bindings`: `ExecutableBindingContribution` |
| Static discovery | `execution.workflow_descriptors`: `Workflow`, `WorkflowInput`, `WorkflowOperation`, `WorkflowDeclaration`; `execution.discovery_descriptors`: `EnvironmentDeclaration`, `ConfigurationDeclaration` |
| Bounded result presentation | `api.application_presentations`: `ApplicationPresentation`, `PresentationData`, `PresentationReader`; [closed registration and fallback](workbench-presentations.md) |
| Software installation | `execution.installation_descriptors`: `WorkflowInstallationDeclaration`, `WorkerEnvironment`, `ExternalSoftware` |
| Actual cost accounting | `execution.work_costs`: `CostEvidence`, `CostWorkScope`, `WorkCostMeasurement`, `BilledResourceWindow`, `WorkCostAccount`, `summarize_work_cost` |
| Explicit service composition | `execution.executable_bindings`: `CompositeCampaignRuntimeProvider`, `LayeredCampaignRuntimeProviderResolver`; `execution.providers`: `CampaignRuntimeProviderRegistry` |
| Continuing source contracts | `science.inquiry.continuing_source`: `ContinuingSourceSession`, `LiveActorLease`, `LiveObservation`, `LiveScientificWindow`, `FiniteLiveOperation`, `LiveEffectReceipt`; `execution.continuing_source`: `ContinuingSourceOwner`, `LiveSourceAccess`, `LiveEffectPort`, `require_live_application` |
| Inquiry author and dependent assessment | `design.inquiry_methods`: `InquiryAuthorContract`, `InquiryAuthoringMode`, `InquiryMethodEvidence`, `InquiryEvidenceRole`, `FrozenInquiryConsumer`, `FrozenInquiryProcedure`, `AssignedInquiryOpportunity`, `FixedOpportunityStopping`, `DependentAssessmentContract`, `MissingOpportunityRule` |
| Prior-result representation | `execution.recursive_qualified_parents`: `RecursivePriorExecutionBinding`, `RecursivePriorNativeBinding`, `prior_result_capacity`, `inspect_prior_execution_bindings` |
| Closed physical codecs | `storage.contracts.recursive_storage_codecs`: `RecursiveStorageCodec`; `storage.contracts.artifacts`: `ArtifactWriter`, `ArtifactWriteRequest`, `ArtifactStreamWriteRequest`, `ArtifactWriteResult` |

All module names in this table start with `empirical_lawhood.`.
Canonical schemas retain their own exact `SCHEMA` and `VERSION` pairs.
Binary storage codecs require nonempty payloads unless their code-owned
`RecursiveStorageCodec` explicitly selects `allow_empty=True`. The selection is
part of the generated codec declaration and validation identity. An empty
payload still passes its registered structural validator and complete domain
manifest checks; the selection supplies no missing scientific operands.
The callback API version is not a canonical record version or transport envelope version.
Use [public discovery declarations](discovery-facets.md) for workflow, environment and input-role facts.
These declarations supply no execution or scientific authority.
Use the [work cost procedure](work-cost-accounting.md) for original measurements, nested scopes and shared bills.
Use the [shared-service pattern](shared-services.md) for one immutable configuration and separate input permissions.
Use the [continuing-source procedure](continuing-sources.md) for mutable source ownership, bounded actor memory and finite effects.
Use the [inquiry and assessment extension](inquiry-assessment-extensions.md) for bounded authors, original dependence and frozen consumers.

Use the existing constructors instead of a second lifecycle framework:

1. Construct one `RecursiveOperationDeclaration` for each installed scientific operation.
2. Declare the exact config type, input ports, complete outputs, resources and runner factory.
3. Use its `manifest()`, `registration()` and `provider_factory()` methods for the existing projections.
4. Construct an `ExperimentProtocolDeclaration` when the domain supplies an experiment preparation workflow.
5. Add `ExperimentRuntimeBinding` only for the selected outer composition, read, derivation or export capabilities.
6. Export one `ExtensionDeclaration` and run the [ordered generators](extending-the-engine.md#declare-one-extension).

The constructors validate combinations without calling the selected science.
A pure method can leave inquiry, native and prospective hooks absent.
An unimplemented scientific callback must raise an explicit refusal.
Returning an arbitrary sentinel does not implement a scientific contract.

## Profiles and capability selection

These profiles describe interface requirements. They do not establish conformance, current readiness or qualification.
Select capabilities from the installed declaration and binding, then use the ordinary owning service.
Missing or incompatible capabilities refuse at that service. They do not trigger an alternate lifecycle.

| Profile | Required construction and capability selection | Evidence boundary |
| --- | --- | --- |
| Bounded pure method | Operation declaration, strict codecs, complete ports, resources and `TaskRunner`. Optional scientific hooks match actual consumers. | Disclosed inputs remain exposed. Independent scientific validation stays with the method. |
| Ordinary development | Protocol preparation and lowerer. Add the declared input binder, retained reader and any required runtime composition. | Completion, inquiry outcome, claim disposition and qualification remain separate. |
| Isolated native process | Explicit native execution properties, scientific units/effect slots, `NativeWorkPreparer` and the existing isolated invocation contracts. | Initial work is a pure projection. Source admission and actual contact remain separate. |
| Prospective assessment | Explicit prospective declaration, `ExperimentHandoffBinder`, original source/issue contracts and selected scientific reader. | Development inputs confer no issue, execution or reveal authority. |
| Composite programme | Exact programme record type and `ProgrammeServiceFactory`. Its service implements `author`, `run`, `read` and `recover`. | Component scopes remain distinct. Optional export, derivation and execution-only reads need separate capabilities. |
| Continuing source | Explicit session, current access, exact clock mappings, bounded actor memory and source-owned effect ports. The native adapter must enforce application-time generations and expiry. | The bounded counter example is software conformance only. No Quake implementation, general real-time guarantee or scientific qualification follows. |
| Inquiry author and dependent assessment | Exact author mode, evidence roles, original opportunity allocation, stopping, missingness and frozen consumer through existing scientific and inquiry hooks. | The finite assigned-census example supplies no general authoring algorithm, population confidence or physical qualification. Installed acceptance remains separately required. |
| Registered presentation | Declare an API-layer `ApplicationPresentation` through the closed registry and its original bounded reader. Select its exact panel revision separately from scientific records. | Unsupported panel revisions retain the original report through the generic view. A scientific file cannot select executable browser code. |

The native and prospective interfaces reuse their [existing owners](native-subwork.md).
Their selected prerequisites and bounded conformance evidence remain independent requirements.
Use the [presentation procedure](workbench-presentations.md) for the supported registration, bounds and revision fallback.
The smallest method has no obligation to implement continuing-source or presentation contracts.

## Experiment callback call sites

The [callback protocols](../../src/empirical_lawhood/execution/experiment_callbacks.py) define exact parameters and return annotations.
Each field can select one applicable call form. A union does not require every alternative.
Positional parameters and keyword names must match the actual owning call site.

| Declaration callback | Owning call site | Return contract |
| --- | --- | --- |
| `prepare` | `api.experiment_preparation.prepare_experiment` | Exact `ExperimentPreparation` for the selected specification |
| `bind_inputs` | `api.experiment_preparation.load_experiment_inputs` | Exact `PreparedExperimentInputs` |
| `validate_instance` | `api.experiment_runtime_bindings.authenticate_experiment_instance` | `None`, or raise on refusal |

Method inputs, file inputs and copied input locations have separate optional call forms.
The declaration selects those forms. Simple methods need no unused filesystem parameters.

| Runtime callback | Owning call site | Return contract |
| --- | --- | --- |
| `bind_handoff` | `api.prospective_experiment._load_prepared_prospective_experiment` | Same concrete handoff type, with unchanged scientific and resource fields |
| `prepare_authoring` | `api.experiment_preparation._author_prepared_experiment` | Exact `ExperimentPreparation` with original scientific operands |
| `read_result` | `api.experiment_scientific_read.read_prepared_experiment_science` | `ExperimentReport` |
| `bind_development_runtime` | `api.recursive_execution._development_runtime_supplier` | `RecursiveInputSupplier` with callable `resolve_input(spec)` |
| `programme_service_factory` | `api.composite_experiment_programme.selected_composite_programme_service` | `CompositeProgrammeService` |
| `derive_inputs` | `api.experiment_preparation.derive_experiment_inputs` | Exact `ExperimentInputDerivationResult` with authenticated publications |
| `export_products` | `api.experiment_programme.ExperimentProgrammeService.export_products` | `ExperimentReport` |
| `read_development_result` | `api.experiment_scientific_read.read_prepared_development_science` | `ExperimentReport` |
| `authenticate_instance` | `api.experiment_runtime_bindings.authenticate_experiment_instance` | `None`, or raise on refusal |
| `complete_development_result` | `api.experiment_scientific_read.complete_prepared_development_science` | `ExperimentReport`; no new native entry |
| `validate_development_read_access` | `api.experiment_scientific_read.validate_prepared_development_read_access` | `None`, or raise on refusal |
| `validate_authoring_read_access` | `api.experiment_preparation._authoring_access_guard` | `None`, or raise on refusal |
| `bootstrap_development_input_access` | `api.experiment_runtime_bindings.bootstrap_authored_development_inputs` | Live `OriginalInputAccess` |
| `bootstrap_authoring_input_access` | `api.experiment_preparation._author_prepared_experiment` | Live `OriginalInputAccess`, or the owner's explicit absent scope |
| `bootstrap_selected_input_access` | `api.experiment_runtime_bindings.bootstrap_selected_experiment_inputs` | `CurrentAccessGuard`, which returns `None` or raises |
| `select_read_access` | `api.experiment_read_access.load_experiment_read_access` | Operation-local `ReadAccessSelection` with the complete copied locator census |
| `bootstrap_prospective_input_access` | `api.prospective_experiment._bootstrap_prospective_original_inputs` | Live `ProspectiveOriginalInputAccess` |
| `derive_prospective_design_inputs` | `api.composite_experiment_programme.prepared_component_source_snapshot` | Exact `RecursiveProspectiveDesignInputs` |
| `derive_inputs_with_service` | `api.experiment_programme.ExperimentProgrammeService.derive_inputs` | Exact `ExperimentInputDerivationResult` |

These call-site names identify implementation owners. They do not make private helpers public extension imports.
Use the existing public workflow services to invoke them.
Keep API file and custody composition outside inward adapter declarations.

`ExperimentReport` is a mapping with string keys and domain-owned values.
The shared boundary preserves exact Decimal values, canonical records, complete denominators and adverse or missing findings.
It does not infer a common scientific success value.
For example, operational completion and `useful-supply` can coexist with an `UNEVALUABLE` claim and no qualification.

Access-enabled callbacks receive their explicit access selections only when applicable.
Incomplete prospective assessment requires `supports_incomplete_assessment` and its corresponding reader form.
Ordinary and prospective export forms remain separate.
A dual-route prospective declaration receives its specification when its exposed development binder is selected.

## Scientific and inquiry callbacks

The [recursive callback protocols](../../src/empirical_lawhood/execution/recursive_callbacks.py) describe the actual compiler and custody call forms.
Their named return contracts do not replace existing exact record and identity checks.

| Hook group | Actual owning calls and return contracts |
| --- | --- |
| Root preparation and validation | `runtime.recursive_compiler.validate_recursive_scientific_roots`: one non-`None` invocation-local preparation, then validators returning `None` |
| Claim resolution | The same compiler owner requires the exact declared `ClaimSpec` |
| Operand, unit and effect projections | `compile_recursive_wave` requires sorted, unique tuples with each field's actual ID or SHA-256 grammar |
| Requirement assessments | `project_recursive_assessments` requires exact `RequirementSupplyAssessment` records and evidence joins |
| Qualified parents | `api.recursive_qualified_parents` requires `None` from assessors and scope validators, plus bounded exact prior-execution binding tuples |
| Contribution and successor | `api.recursive_contributions` requires `ContributionManifest` records and a `RecursiveStudyDraft` or explicit absent successor |
| Inquiry outcome and endpoint | `api.recursive_inquiry` selects an outcome ID and requires `None` from endpoint validators |
| Inquiry evidence | `api.recursive_inquiry_evidence` requires a complete tuple of `InquiryEvidenceBinding` records |
| Product identity and work | `api.recursive_inquiry` requires exact `ObjectIdentity` and `ScientificInquiryWork` records |
| Target assessment | `api.recursive_inquiry_claims` requires exact `InquiryClaimAssessment` records with original receipts and assessment contracts |

Root preparation may use a domain-specific immutable type.
Its validator checks the exact shared input tuples from the same compiler invocation.
The generic type parameter does not permit a process-wide cache or a retained access verdict.

## Compatibility and transition

Callback API `1.0.0` supports requests in the explicit range `>=1.0.0,<2.0.0`.
This source introduces that API within distribution version `0.3.0`.
Older distributions without the negotiation function do not implement this callback baseline.
Select their own documentation and retained installation for source-bound recovery.

The transition preserves existing canonical record schemas and bytes.
Existing report callbacks must return mappings with string keys.
Runtime binders must return their actual input supplier, not a placeholder object.
Access selection objects must expose a read-only `selected_records` tuple with exactly the copied locators.
The three existing locator selection owners implement that property.
Existing current-access and concrete domain checks remain in force.

Within a published callback API major version, required keyword names and return contracts remain compatible.
Optional capabilities require explicit selection. They cannot become mandatory through a patch release.
An incompatible call form requires a new major API version and a documented transition.
Deprecations identify the replacement, affected profiles, earliest removal version and retained-reader consequence before removal.
Canonical decoder revisions and source-bound recovery retain their separate policies.

Static signature inspection cannot prove the target of a variadic lazy wrapper.
Keep lazy loading and exercise selected hooks through bounded conformance inputs.
A valid signature alone establishes no returned record, complete output census or scientific result.
Keep each executed profile and unmet prerequisite visible in its retained conformance report.

## References and research

The [compatibility policy](compatibility.md) defines release identity and retained-record support.
The [architecture guide](architecture.md) fixes import direction and scientific ownership.
The [testing guide](testing.md) separates disclosed software controls from scientific qualification.
