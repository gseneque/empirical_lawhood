# Investigate a prerequisite and use its assessed contribution

SPDX-License-Identifier: CC-BY-4.0

A failed requirement can become another scientific question. Its proposed
supplier has conditions of its own. This workflow records those questions,
executes a selected finite wave over registered operations, and retains an
assessed contribution for later inquiry. A supplying procedure, actual supply on
an instance, consumer admission and successful joined use have separate results.

Start with the supplied RC draft to inspect a complete numerical design, the
battery draft to investigate continuation on a nonlinear substrate, or the
materials draft to see a programme with unavailable physical premises. Unresolved
questions are valid authoring products. A selected executable path needs all of
its input premises or a declared terminal refusal.

The [Rubisco kinetic join](../../programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/guide.md) supplies a complete
exposed three-member roster through this same route. It preserves partial and
rejected members, unknown covariance and a conditional numerical evidence
ceiling; it supplies no mutation-to-kinetics or nomination authority.

Authoring refuses a preparation outside the assigned roster or a repeated native acquisition slot.
Fixed scientific operations also refuse unsupported quantities, units, receivers, times or criteria.
Use the [extension guide](../development/extending-the-engine.md#bind-scientific-units-and-effect-slots) when a new question needs another registered operation.

## Choose a programme example

The shared workflow ID is `recursive-inquiry`.
Its examples have separate scientific purposes and live with their programmes:

- [RC measurement, preparation and joined use](../../programmes/foundations/measurement-and-response/workflows/recursive-rc/guide.md).
- [Battery state supply and subsequent voltage inquiry](../../programmes/energy/battery-charging/workflows/recursive-battery/guide.md).
- [Unresolved material prerequisites](../../programmes/materials/superconductivity/workflows/recursive-materials/guide.md).

A target, a supplier assessment and later instance use are separate claims.
An operation's scientific meaning belongs to its domain and declared evidence.
The shared engine retains their records, ordering, resources and custody.

## Select the environment and inspect the design

Use the selected checkout and its [locked environment](environments.md).
The RC route uses the locked base profile. The battery route uses a focused
profile with PyBaMM 26.6.2.0, Chen2020, CasADi and pinned NumPy/SciPy versions.
Set the [numerical runtime variables](environments.md#frozen-rc-numerical-input-profile) before authoring or execution:

```bash
uv sync --locked --python 3.11.14 --group battery-recursion
uv run --no-sync empirical-lawhood workflow show recursive-inquiry --format json
uv run --no-sync empirical-lawhood config validate \
  --consumer recursive-inquiry --config programmes/foundations/measurement-and-response/workflows/recursive-rc/rc-original.json
uv run --no-sync empirical-lawhood campaign recursive-explain \
  --input programmes/foundations/measurement-and-response/workflows/recursive-rc/rc-original.json
```

Discovery lists static facts. Explanation reads the selected draft and shows
requirements, chosen suppliers, unselected alternatives, cutoffs and evidence
limits. Neither command acquires observations or supplies authority.

The [original battery protocol](../../programmes/energy/battery-charging/workflows/recursive-battery/battery-protocol.md) owns its scientific tolerances,
preparations, nested histories and endpoint assessments. The separately selected
[thermal inquiry protocol](../../programmes/energy/battery-charging/records/battery-thermal-inquiry-selection.md)
owns the new temperature/model-adequacy question. The original
[RC protocol](../../programmes/foundations/measurement-and-response/workflows/rc-prerequisite-chain/protocol.md) remains unchanged. The general
RC draft gives the explicit operation graph around that exact scientific input.

## Freeze and execute one selected wave

Select an [operator storage profile](configuration.md) and a new authoring
directory under its guarded external root. The authoring export binds the exact
draft, registered implementations, source/configuration bytes, resource
declarations, scientific plan, execution plan and graph correspondence. It grants
no issue, reveal or qualification authority.

```bash
uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign recursive-author --input /work/selected-draft.json \
  --output-dir /selected/guarded-root/wave-a

uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign recursive-development-run --authoring-dir /selected/guarded-root/wave-a

uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign recursive-development-result --authoring-dir /selected/guarded-root/wave-a
```

Exposed numerical execution uses the existing scheduler and primary completion
receipts. Every assigned unit and declared nested branch remains in its census.
A scientifically failed, refused or unevaluable assessment can be a successfully
completed software task. Operational interruption retains its different state.

Both `recursive-development-run` and `recursive-inquiry-run` accept `--workers INTEGER`.
The default is one worker.
This option limits concurrent tasks and preserves the complete authored census.
The API refuses counts above the selected CPU capacity or current process affinity.

Before selecting more workers, measure an exposed allocation on a host with sufficient CPU and memory.
Capacity detection does not enforce effective CPU quotas or available memory.
Matrix task budgets do not reserve memory.
The Python APIs also accept the existing `ExecutionResourceCapacity` through `parallel_resource_capacity`.

Completed recovery and result reading authenticate retained products without
native acquisition. A durable contact marker without a completion receipt stops
automatic repetition. Preserve uncertain outputs for inspection. Changing a task
label or losing the local catalog supplies no retry authority.

The run report counts new potential native-effect entries in
`new_native_contact_count`; a completed resume reports zero. Actual acquired
observations and native phase counts remain in the authenticated scientific products.

Use `--terminal-product-format compact` to authenticate custody without decoding scientific records.
The compact report retains the complete task, receipt and product census.
Use `recursive-development-result --terminal-product-format compact --allow-partial` for an interrupted wave.
This command reads retained evidence and does not resume execution.
Use the document report or an independent typed consumer for scientific assessment.
The [causal matrix example](../../programmes/foundations/emergent-structure/workflows/causal-response/worked-example.md) exercises the installed array, commitment and recovery contracts.

<a id="retain-a-bounded-inquiry-decision"></a>

## Retain an inquiry decision

The selected inquiry route composes an immutable specification, evidence state,
finite menu, policy and existing campaign decision right. Its input is a strict
`WorkBoundInquiryDecisionRequest` at version 3.0.0, containing the exact
version-two work-bound state. Historical version-one inputs
use `InquiryDecisionRequest`. Scientific inputs come from explicitly selected
authenticated authored waves. Registered domain projectors retain their original
scope and supply the assessment outcome. A reader cannot assign a favourable
outcome or relabel evidence to a requested endpoint. Failed operations remain in
the operational census even when they produce no scientific record. Missing
actual expense remains unknown. It prevents ACT only when the policy bounds
that expense coordinate; an unrestricted policy does not replace unknown costs
with invented values.

The [robust policy contract](../development/recursive-inquiry-policy.md) defines the current version-three request with version-two specification, menu and policy.
It binds target requirements, compatible stock, supplier alternatives, uncertainty and actual independent assessment.
Its branch stop retains unresolved target requirements.
Historical version-1 records keep their exact original bytes and scientific scope.
Historical robust version-two requests cannot be freshly committed or admitted.
Read retained version-two decisions with `campaign recursive-inquiry-result
--decision-dir PATH --historical`; its `HISTORICAL_ARCHIVE` report grants no current
eligibility. The API archive reader uses `revalidate_sources=False`.

### Prepare a source-only version-three request

Select a writable operator profile and a new directory under its guarded artifact root.
Run from the selected checkout and locked main environment.
Replace the checkout and profile paths below.
The script prepares the material adapter's exact exposed analytic source.
It authenticates a source-only authored packet without supplier execution.

```sh
uv run --no-sync python - <<'PY'
from decimal import Decimal
from pathlib import Path

from empirical_lawhood.adapters.methods.analytic_material_inquiry import policy_binding as binding
from empirical_lawhood.adapters.simulators.uniform_electron_gas_response.native_quickstart import UniformElectronGasAnalyticReferenceConfig
from empirical_lawhood.api.codecs import load_registered_authoring
from empirical_lawhood.api.integration_artifact_profiles import integration_artifact_profile_validators
from empirical_lawhood.api.recursive_authoring import author_recursive_wave, load_authored_wave
from empirical_lawhood.api.recursive_inquiry import project_inquiry_state
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_inquiry import identity
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.runtime.operator_profile import OperatorStorageProfile, resolve_external_root_contract
from empirical_lawhood.runtime.recursive_inquiry import InquiryStateSources, InquiryWaveSource, WorkBoundInquiryDecisionRequest

project = Path('/selected/checkout').resolve(strict=True)
profile = load_registered_authoring(Path('/work/operator-profile.json'),
    root_schemas={OperatorStorageProfile.SCHEMA: OperatorStorageProfile})
contract = resolve_external_root_contract(profile, repo_root=project, home_root=Path.home())
plane = ExternalArtifactPlane(GuardedExternalRoot(contract), integration_artifact_profile_validators())
work = plane.root.resolve('material-policy', for_write=True)
work.mkdir()  # Requires a fresh directory.

def save(name, record):
    path = work / name
    with path.open('xb') as stream:
        stream.write(record.canonical_bytes())
    return path

source = decode_canonical_bytes(
    (project / 'programmes/materials/superconductivity/workflows/electron-gas-response/config.json').read_bytes(),
    UniformElectronGasAnalyticReferenceConfig, maximum_bytes=None)
source_records = (source,)
draft = binding.policy_supply_draft(*source_records)
origins = binding.input_origins(draft)
save('draft.json', draft)
save('origins.json', origins)
by_digest = {record.fingerprint(): record for record in source_records}
inputs = tuple((external.input_id, save(external.input_id.rsplit('.', 1)[-1] + '.json',
    by_digest[external.expected_content_sha256])) for external in draft.external_inputs)
origin_dir = work / 'origin'
author_recursive_wave(draft=draft, origins=origins, input_bindings=inputs,
    project_root=project, artifact_writer=plane, output_dir=origin_dir)
packet, _, _, _ = load_authored_wave(directory=origin_dir, artifact_writer=plane)
sources = InquiryStateSources((InquiryWaveSource(
    origin_dir.relative_to(Path(contract.canonical_path)).as_posix(),
    identity(packet, packet.packet_id), include_products=False),))
specification = binding.inquiry_specification(draft,
    specification_id='inquiry.exposed-origin', stage='origin')
cutoff = InformationCutoff('cutoff.inquiry.exposed-origin', specification.endpoint.clock_id,
    CausalPhase.POST_OUTCOME, Decimal('0'))
state = project_inquiry_state(specification=specification, state_id='state.inquiry.exposed-origin',
    information_cutoff=cutoff, sources=sources, artifact_writer=plane)
menu, policy = binding.inquiry_menu(specification, state, stage='origin', next_draft=draft)
right = next(row for row in draft.campaign.decision_rights
    if row.action is specification.required_decision_action)
request = WorkBoundInquiryDecisionRequest(specification=specification, state=state, sources=sources,
    menu=menu, policy=policy, campaign=draft.campaign, right=right, actor_id=right.decision_maker_id)
save('request.json', request)
print(work)
PY
```

Use the printed directory in place of `/selected/guarded-root/material-policy` below.
The artifact root includes the profile's artifact namespace.
The adapter supplies the campaign, applicable right and local development actor identifier.
These records establish decision provenance, without scientific execution or qualification authority.
Coordinate zero with `POST_OUTCOME` describes this exposed analytic chart.
It does not declare a prospective confirmation seal or new independent units.
The `include_products=False` source claims no completed supplier product.

Persist the decision before optional contribution export:

```bash
uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign recursive-inquiry-decide --input /selected/guarded-root/material-policy/request.json \
  --output-dir /selected/guarded-root/material-policy/decision.origin

uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign recursive-inquiry-result --decision-dir /selected/guarded-root/material-policy/decision.origin
```

An ACT intent commits exact draft, configuration, capability and input-origin
identities. A draft can select several registered operations: the configuration
and capability identify exactly one selected operation, and the whole-draft
identity commits every operation and its dependencies. A matching operation
outside the selected wave or an ambiguous match refuses.
Current robust decisions also join the registered scientific work to the exact
selected draft. Renaming an uncertain configuration cannot authorize the same
work. An unknown historical work binding remains uncertain; a distinct
prospective question requires its separately authenticated selected draft.
Every current ACT also checks the full authenticated completed-attempt census,
including completions omitted from a menu. For an explicit REUSE/ADOPT decision,
`recursive-inquiry-result` recovers the original authored wave, complete receipt,
products and census in `reused_completion`; it enters no task or native work.
The API equivalent is `recover_inquiry_completion(decision_directory=PATH,
artifact_writer=PLANE)`. Fresh authoring or execution of that same-work reuse
intent refuses. Distinct later consumer work still uses the contribution route.
For an initial source-only decision, author with `--initial-draft`.
For a later use, select `--supplier-dir` and its authenticated portable
`--contribution-dir`; the registered existing builder supplies the next draft.
Both require `--decision-dir`, `--origins` and a fresh `--output-dir`.
The explicit origin census owns every selected external input as SOURCE or an
exact receipt-bound CONTRIBUTION product. This permits a new instance alongside
an authenticated supplier while rejecting disguised parent-produced bytes.
Execute the admitted directory with `campaign recursive-inquiry-run
--authoring-dir PATH`; it rechecks the complete intent join before using the
existing scheduler or completed recovery. HOLD and STOP have no executable
intent. These development records create no issue, qualification or reveal
authority.

For the selected `investigate-supplier` ACT, author and execute the PURE supplier separately:

```sh
uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign recursive-inquiry-author \
  --decision-dir /selected/guarded-root/material-policy/decision.origin \
  --origins /selected/guarded-root/material-policy/origins.json \
  --initial-draft /selected/guarded-root/material-policy/draft.json \
  --input-binding external.analytic-material-inquiry.supply.source=/selected/guarded-root/material-policy/source.json \
  --output-dir /selected/guarded-root/material-policy/supplier

uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign recursive-inquiry-run --authoring-dir /selected/guarded-root/material-policy/supplier \
  --terminal-product-format compact

uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign recursive-development-result --authoring-dir /selected/guarded-root/material-policy/supplier \
  --terminal-product-format documents
```

Compact output authenticates custody and defers scientific decoding.
The final `documents` read exposes the typed supplier result without another execution.
Independent later use and the physical target remain unresolved.
Later requests require actual completed products, a new specification/state identity and retained previous decision paths.
Use `stage='later'` with the authenticated supplier, contribution parent and exact registered consumer draft.
Use `stage='frontier'` with the actual assessed draft and all four connection findings.
Changing the initial source flag cannot supply those results.
For explicit human direction, set both `human_choice` and its actual nonempty `human_reason` before commitment.
Keep the applicable actor/right and earlier decision packet.

### Substitute the Rubisco source and builder

Select a new `rubisco-policy` directory for Rubisco.
Replace the material adapter import and source-loading block with the following code.
Keep the common origins, packet, state, menu and version-three request steps.
The archived source fixture has zero fresh biological units and no execution receipts.
The code reads two original raw members without extraction, script execution or external access.

```python
from hashlib import sha256
from io import BytesIO
import json
import tarfile
from empirical_lawhood.adapters.methods.rubisco_inquiry import policy_binding as binding
from empirical_lawhood.adapters.methods.rubisco_combinations.source_binding import (
    GENBANK_SOURCE_SHA256, WILSON_SOURCE_SHA256, TeParentGenbankInputV1, WilsonArticleInputV1)

fixture = project / 'tests/fixtures/rubisco/nomination'
census = json.loads((fixture / 'source-census.json').read_bytes())
raw = (fixture / 'source-operands.tar.gz').read_bytes()
if (len(raw) != census['archive_bytes'] or sha256(raw).hexdigest() != census['archive_sha256']
    or census['evidence_role'] != 'EXPOSED_SOFTWARE_CONFORMANCE_ONLY'
    or census['scientific_qualification'] != 'NOT_PERFORMED'
    or census['fresh_independent_units'] != 0 or census['contains_execution_receipts']):
    raise ValueError('original exposed source archive or evidence role differs')
with tarfile.open(fileobj=BytesIO(raw), mode='r:gz') as archive:
    def retained(name):
        member = archive.getmember(name)
        if not member.isfile():
            raise ValueError('selected raw source is not a regular archive member')
        with archive.extractfile(member) as stream:
            payload = stream.read()
        selected = census['members'][name]
        if len(payload) != selected['size_bytes'] or sha256(payload).hexdigest() != selected['sha256']:
            raise ValueError('selected raw source differs from its original census')
        return payload.decode('utf-8')
    source_records = (
        WilsonArticleInputV1('input.exposed-policy.wilson', WILSON_SOURCE_SHA256,
            retained('macro/source.007--wilson2017-jbc.html')),
        TeParentGenbankInputV1('input.exposed-policy.te', GENBANK_SOURCE_SHA256,
            retained('macro/source.008--te-MG000148.gb')),
    )
draft = binding.policy_supply_draft(*source_records)
```

Change every working-directory locator to `rubisco-policy`.
Replace the material input binding with both Rubisco bindings:

```sh
  --input-binding external.rubisco-inquiry.supply.article=/selected/guarded-root/rubisco-policy/article.json \
  --input-binding external.rubisco-inquiry.supply.genbank=/selected/guarded-root/rubisco-policy/genbank.json
```

The typed constructors and builder check the exact original article and GenBank source hashes.
The supplier's conditional arithmetic does not establish mutant kinetics or the paired enzyme target.
Independent later-use assessment retains each endpoint and can falsify specificity.

For a separately selected question beyond an existing provider's successor
builder, the [API authoring route](../../src/empirical_lawhood/api/recursive_inquiry.py)
accepts `human_fork_draft` with the actual `supplier_directory`, portable
contribution and complete origins. It requires an explicitly human-directed,
persisted ACT whose intent already binds that exact new draft. The supplier
must be one of the decision's authenticated completed waves. The new question
preserves the old outcome, contribution role and prior decisions; it supplies
no qualification or authority to execute unselected scientific work. Automatic
successors continue to use the registered existing builder.

The compact pure registrations are `rubisco_inquiry` and
`analytic_material_inquiry`. They reuse the Wilson source/local combination and
analytic material contracts. Their assessments distinguish scoped supply,
compatible later use and adverse or unresolved cases; successful software
execution does not establish biological or physical qualification.

The [reopened results](../../programmes/shared-records/applied-el/reopened-results.md) record completed
acceptance of the selected compact research route: four Rubisco/material supply
and use waves plus eleven direct controls, fifteen pure operations with zero
native contacts. Receipt recovery preserved the completed supplier and prior
failed checkpoints. This is selected route acceptance, not full release or RA8
acceptance. The earlier [allocation closeout](../../programmes/shared-records/applied-el/closeout.md)
retains the first worker's historical 512 MiB failure; the
[active allocation](../development/history/applied-el/limit-removal.md) supersedes that ceiling.

The separate Rubisco conditional supplier and independent consumer also
completed with all 22 original/dependency sources, nineteen Wilson rows, nine
recipes and the complete selected frontier. Their source-bound conditional
calculation and reuse do not supply matched I95M kinetics, biological admission,
a supported nomination or a comparative EL advantage. The first reporting failure
and receipt-backed terminal repair retain their separate original costs and
custody.

The reopened battery D1 acquired the selected 23°C and 27°C Chen2020 traces at
-1.455 A for 900 seconds. Both delivered 0.36375 Ah and passed the independent
full-horizon, sampled voltage/mean-temperature and realized-current checks. This
ordinary premise is solved/non-discriminating at its selected sampled numerical
scope. Missing whole-time certification does not convert it into service failure.
Physical qualification and comparison remain unestablished or unevaluated. Its
two native contacts and two pure assessments belong to one simulated parameter
family, with zero physical independent units. The original technical observation
failure with no receivers remains retained in the
[historical programme closeout](../../programmes/shared-records/applied-el/programme-closeout.md).
Historical continuation examples retain their original isothermal or pouch scope.

## Inspect the separately selected development entries

The following separately identified entries extend the programme. At the earlier
preparation checkpoint, their registered operations were UNENTERED; source
inspection, draft construction and exposed software checks alone did not
constitute execution. The 11 October 2026 Rubisco continuation has now completed
five actual registered pure operations with authenticated receipts and typed
assessments. The first battery thermal supplier contact ended in a retained technical
interruption before a scientific product returned. Its separately selected numerical
repair supplier completed its 36 development forecasts with an UNEVALUABLE
reference-precision result; later uses remain UNENTERED. A distinct twelve-
forecast precision diagnostic entered one native attempt and retained unknown
completion after a kernel-recorded global host OOM kill; no scientific result
or completed subcall census is retained. The Rubisco test-nomination preparation
and audited terminal packet are complete. These entries use development authority; they do not supply qualified
sources or issue/reveal rights for a real prospective study.

| Entry and current status | Exact input and draft owner | Scientific protocol and retained boundary |
|---|---|---|
| Rubisco portfolio — COMPLETED, two pure operations | [`SourceAudit` and `source_audit_from_bytes(raw_sources, candidate_ids=...)`](../../src/empirical_lawhood/adapters/methods/rubisco_portfolio_inquiry/science.py) authenticate all 34 selected original/dependency members; [`supply_draft(source)` and `use_draft(supplier, instance, parent=manifest)`](../../src/empirical_lawhood/adapters/methods/rubisco_portfolio_inquiry/recursive_translation.py) bind source construction and distinct later assessment. | The [portfolio selection](../../programmes/biology/photosynthesis/records/rubisco-portfolio-selection.md) owns the 32 exact biological hypotheses, observed whole-effect support and joint-target queries. Unknown Gp endpoints stay unknown; nonextrapolative support failure does not reject all descendants or mechanisms. |
| Rubisco gas cycle — COMPLETED, three pure operations | [`MechanismSourceAudit` and `source_audit_from_bytes(raw_sources)`](../../src/empirical_lawhood/adapters/methods/rubisco_cycle_constraints/contracts.py) authenticate the two exact primary mechanism files; [`instance_from_source`, `supply_draft`, `use_draft` and `reuse_draft`](../../src/empirical_lawhood/adapters/methods/rubisco_cycle_constraints/recursive_translation.py) bind actual assessed procedures and distinct source-bound queries. | The [broad programme protocol](../../programmes/biology/photosynthesis/records/rubisco-broad-programme-protocol.md) owns the declared reversible topology, complete latent/query census and five selected hypotheses. Hypothetical microscopic rates are mathematical witnesses, not measured candidate effects or biological qualification. |
| Battery thermal inquiry — repair supplier COMPLETED, reference precision UNEVALUABLE | [`BatteryInquirySource`](../../src/empirical_lawhood/adapters/methods/battery_thermal_inquiry/contracts.py) pins the separate protocol and installed native-source bytes; [`supply_draft`, `use_draft` and `reuse_draft`](../../src/empirical_lawhood/adapters/methods/battery_thermal_inquiry/recursive_translation.py) bind the native procedure, later instance and actual prior-use assessment. | The [thermal inquiry selection](../../programmes/energy/battery-charging/records/battery-thermal-inquiry-selection.md) owns the 2.5 Ah operational-SOC endpoint, three guarded CC/CV recipes and development 5/25/35°C. All 36 forecasts returned; all nine reference pairs failed precision. The later 20°C and subsequent 30°C uses remain UNENTERED. One exposed family, zero physical units. |
| Rubisco exploratory nomination — preparation and terminal audit complete | [`NominationPreparationSource`](../../src/empirical_lawhood/adapters/methods/rubisco_nomination_preparation/contracts.py) and [`preparation_draft`](../../src/empirical_lawhood/adapters/methods/rubisco_nomination_preparation/recursive_translation.py) bind the original macro SOURCE and actual earlier cycle-use OUTCOME. | The [nomination selection](../../programmes/biology/photosynthesis/records/rubisco-nomination-preparation-selection.md) records the actual PURE receipt, separate dossier-scope terminal STOP, independent audit and complete eight-section review packet. Exact proposed Gp I95M material, full construction sequences, conditional/adverse rationale and paired assay are prepared. Mutant biology, actual construction, all 24 preparations/assays and external submission remain UNENTERED. |
| Battery component precision — entered, unknown completion | [`DiagnosticSource`](../../src/empirical_lawhood/adapters/methods/battery_dfn_precision_diagnostic/contracts.py) and [`diagnostic_draft`](../../src/empirical_lawhood/adapters/methods/battery_dfn_precision_diagnostic/recursive_translation.py) retain the exact negative procedure as a DESIGN_OPERAND contribution and MODEL input, with an explicit evidential requirement. | The [component selection](../../programmes/energy/battery-charging/records/battery-dfn-precision-diagnostic-selection.md) owns twelve forecasts and nine single-factor precision comparisons. Its actual native attempt retains BLOCKED/unknown-completion after a global host OOM kill, with no returned scientific result. Forecast/subcall counts remain unknown. It does not qualify the full development roster or later use/reuse. |

The actual `rubisco-broad01` continuation completed portfolio supply/use and
cycle supply/use/reuse with zero native contacts. The portfolio retained 32
source-bound hypotheses, 64 candidate/reference views, 27 observed contrasts,
eight joint-support queries and four exposed sentinels. Its six observed
within-background frontier cases led to a five-case unresolved final split.
The cycle passed sixteen independent state-balance probes and 216 release
checks, then assessed two candidates and reused the actual assessed contribution
for three distinct candidates. Each candidate retained both separate reference
views, all 36 latent families and six release samples per family.

The five-finalist challenge was an actual separately measured direct adapter
analysis, not a sixth registered operation. It retained exact recipes and source
means, adverse primary-source specificity methods, conditional mechanism
support and decisive missing evidence. All five source cases lack at least one
joint target margin. The bounded shortlist has no nominee, biological admission
is UNEVALUABLE and comparison remains UNEVALUATED. Its paired-assay proposition
is PROPOSED_NOT_ENTERED; no biological measurements or new physical studies
were acquired. Mathematical families and samples are not biological
probabilities or independent preparations.

All five receipts, operational census and retained products, together with the
complete 1,292-member, 452,882,034-byte custody copy, were verified.
The [programme closeout](../../programmes/shared-records/applied-el/programme-closeout.md) records the public findings, counts, costs and evidence limits.
The complete underlying packet remains external custody; its paths are not packaged inputs.
Source/model scope and hypothetical rate changes remain
attached through the ACT-before-export and later contribution-use lineage.
The battery supplier's completed precision-negative result retained 206
operational members and 172,845,522 bytes with an exact durable copy. Its 36
forecasts used 56 charging subsolves, 36 initial-SOC attempts and 20 transitions.
All nine DFN precision pairs exceeded voltage and temperature gates, so the
selected procedure remains UNEVALUABLE and D3 later use/D4 reuse remain
unentered. This terminal does not relabel a numerical precision failure as a
physical model failure. The separate diagnostic tests the unresolved numerical
components before any new full-roster qualification.

Prepare canonical typed inputs in explicitly selected files. For example, after
creating `/work/thermal-selection`, this battery source/draft preparation is pure
and imports no native simulator:

```bash
uv run --no-sync python - <<'PY'
from pathlib import Path
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import BatteryInquirySource
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.recursive_translation import supply_draft

source = BatteryInquirySource()
selected = Path('/work/thermal-selection')
(selected / 'source.json').write_bytes(source.canonical_bytes())
(selected / 'supply-draft.json').write_bytes(supply_draft(source).canonical_bytes())
PY
```

For Rubisco, provide the selected complete raw-byte mapping to its source builder;
the [portfolio member manifest](../../src/empirical_lawhood/adapters/methods/rubisco_portfolio_inquiry/source_manifest.py)
and cycle source contract own exact member names, sizes and hashes. A summary,
fixture or source-path list cannot replace those bytes. The cycle successor must
also bind its authenticated macroparameter source and exact candidate/reference
instance; a reuse cannot be created by changing only a label.

Use the existing inquiry decision route for each selected entry. Prepare the
strict `InquiryDecisionRequest` and `RecursiveInputOrigins` from the exact draft,
source files, campaign decision right and authenticated prior waves. Freeze the
outcome-to-decision map and selected scientific protocol before execution; the
request is not a caller-supplied favourable score. After persisting its initial
ACT decision, author the selected source-only draft:

```bash
uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign recursive-inquiry-author \
  --decision-dir /selected/guarded-root/initial-decision \
  --initial-draft /work/thermal-selection/supply-draft.json \
  --origins /work/thermal-selection/source-origins.json \
  --input-binding external.battery-thermal-inquiry.supply.source=/work/thermal-selection/source.json \
  --output-dir /selected/guarded-root/thermal-supply

uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign recursive-inquiry-run --authoring-dir /selected/guarded-root/thermal-supply
```

Read the actual result, meter the attempt and persist the next exact ACT decision
with `campaign recursive-inquiry-decide` before optional
`campaign recursive-contribution` export. Preserve the complete immutable
portable packet. The next authoring call selects that actual supplier wave and
portable contribution; the registered builder constructs its compatible draft:

```bash
uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign recursive-inquiry-author \
  --decision-dir /selected/guarded-root/later-decision \
  --supplier-dir /selected/guarded-root/thermal-supply \
  --contribution-dir /selected/guarded-root/thermal-supply-contribution \
  --origins /work/thermal-selection/later-origins.json \
  --input-binding external.battery-thermal-inquiry.use.instance=/work/thermal-selection/later-instance.json \
  --output-dir /selected/guarded-root/thermal-use
```

Execute with `recursive-inquiry-run` only after the exact intent, origins and
producing source archive are frozen. Apply the same decision/export sequence to
the actual later assessment before subsequent reuse. The battery reuse input is
one authenticated instance-product wrapper containing the unchanged original
supplier and actual previous assessment. Its new instance binds that assessment's
exact identity. A refused zero-attempt use cannot be presented as subsequent
reuse; negative or unevaluable attempted use permits only a separate conditional
revalidation. Recovery reads completed receipts and adds no native contact.
The portfolio and cycle translations expose the same contribution, successor,
evidence and outcome callbacks; choose their exact registered input IDs and typed
records rather than substitute battery files.

## Carry a contribution into another investigation

A registered immutable contribution binds assessed scientific content, exact products,
producing receipts, scope and remaining requirements. The supplied battery waves support inspection and export with
`campaign recursive-contribution`. The RC route retains its complete phase evidence and comparison projection; it has no contribution description. Bind the exact selected version into a new
draft, with a declared role. Importing earlier procedure evidence does not apply
the procedure on a later instance: that application needs its own operation and
instance supply assessment.

For the supplied battery example, first copy
`programmes/energy/battery-charging/workflows/recursive-battery/battery-wave-a.json` to `/work/selected-draft.json`
and complete the author/run/read sequence above in its own new authoring
directory. Export that actual completed Wave A:

```bash
uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/operator-profile.json \
  campaign recursive-contribution --authoring-dir /selected/guarded-root/wave-a \
  --output-dir /selected/guarded-root/contribution-a
```

Copy the complete `contribution-a` directory into a separately selected guarded root.
Keep its original custody bytes intact. Inspect it there, then author its supplied next wave:

```bash
uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/second-root-profile.json \
  campaign recursive-contribution --contribution-dir /second/guarded-root/contribution-a

uv run --no-sync empirical-lawhood \
  --project-root /selected/checkout --operator-profile /work/second-root-profile.json \
  campaign recursive-author --input /second/guarded-root/contribution-a/next-wave.json \
  --contribution-dir /second/guarded-root/contribution-a \
  --output-dir /second/guarded-root/wave-b
```

Run and read Wave B with the same development commands shown above.
The portable packet includes its original authoring, source binding, products and receipt closure.
The importer authenticates that closure without visiting the producer directory or running a simulator.

The current development handoff binds one imported contribution parent per wave.
Its transitive receipt closure may retain earlier ancestors; cycles refuse.
There is no fixed ancestry-depth ceiling. Multiple independent parent imports in one wave are outside
this first implementation. Shared suppliers and joins within a wave retain their
separate declared graph contracts.

The battery example first investigates an exact-state continuation procedure.
Its later wave applies that procedure to a new preparation and acquires voltage
responses under different future currents. A consumer permitting full numerical
state can admit the supplied continuation; an observable-only consumer refuses
the same product. Both dispositions remain visible in joined-use accounting.
Equal-charge histories, numerical views and future words are nested observations,
not independent replication. The known restart capability and its assessed local
scope are explicit; this example makes no literature novelty claim.

Candidate/design operands, qualified evidential parents, retained analysis
inputs and instance products have different permissions. An exposed development
result remains non-promotable qualification evidence after export. A developed
procedure may motivate a frozen candidate evaluated on separately eligible new
evidence through the existing prospective lifecycle.

## Author a different topology or retain a stop

Operations select exact code-owned capability versions and strict typed configs.
Links select one producer for each named input. Shared suppliers are acquired
once; multiple consumers and explicit joins preserve that dependence. Drafts can
retain competing proposals and later questions without selecting every branch.
Cycles, ambiguous producers and unsupported selected inputs refuse before native
contact. Explicit finite authority/resource constraints remain enforceable when
selected.

Authoring has no fixed object, link or depth ceiling. The active programme methods
declare memory, wall time, source-scan and output allowances as `None`, meaning
unrestricted; CPU/thread placement remains explicit. Exact finite scientific
rosters, source identities, numerical precision and custody joins remain required.
Configuration cannot
select arbitrary Python imports, shell commands or unregistered evaluators.

The materials example preserves fabrication, instrument response, measurement
resolution and qualification as unresolved physical requirements. Numerical
fixtures cannot supply those conditions. Stop at an unavailable supplier, or
record a new investigation through the existing nomination/authoring machinery.

## Inspect every retained phase product

The CLI report shows the complete task census, connection assessments and terminal scientific products.
Its product index gives the exact path, hash, size, schema and producing receipt for each phase.
Native arrays remain in guarded custody rather than being repeated in terminal stdout.
The public `read_recursive_wave(..., include_products=True)` API returns authenticated typed phase records and receipts.
Use that authenticated read for scientific analysis; an edited summary is not evidence.

## Prepare a prospective study

`campaign recursive-author` also accepts the strict `recursive-prospective` configuration consumer.
Its `RecursiveProspectiveAuthoringSpec` contains a general draft with a genuine prospective root.
It also supplies the standard entry package, formal context, qualifications and exact source operands.
Bind source configurations by their exact SHA and other operands by logical artifact ID.
No development result can replace a required qualified parent.

For a selected qualified-parent connection, declare its exact
`RecursiveQualifiedParentBinding`: prior issued study, run/task/product receipt,
qualification receipt/adjudication and applicable execution/reveal grants. The
reader replays that actual custody before the installed operation's scientific
admissibility check. A source-readiness qualification receipt cannot stand in
for this scientific qualification.

After authoring, select its integration handoff in the ordinary campaign API.
Readiness, issue, package assembly, execution and reveal keep their existing approval and authority requirements.
The supplied RC and battery capabilities permit development execution and refuse direct prospective issue.
Register a genuinely eligible scientific operation and source for a real prospective design.

See the [inquiry readiness map](designing-recursive-inquiry.md) for the construction brief and remaining scientific work.
See [experiment design](designing-and-running-an-experiment.md),
[architecture](../development/architecture.md), [results and failures](results-and-failures.md)
and [extension seams](../development/extending-the-engine.md) for the distinct graphs,
evidence roles and native assessment owners. Prospective studies retain the
existing source, exposure, assignment, issue, execution and reveal requirements.

## Observed execution time

These times describe one development execution of each wave, not a performance guarantee.
The observed Linux environment used Python 3.11.14, with one worker and one numerical thread per invocation.
Guarded custody was on an external VFAT disk.
Independent RC and battery invocations overlapped during preparation; these are operational observations, not an isolated throughput benchmark.
Wall time includes provider checks, worker startup and receipt I/O.
Scientific model clocks and process limits are separate from these times.

| Selected wave | Tasks | Author, seconds | Execute, seconds |
|---|---:|---:|---:|
| Original RC | 100 | 68.0 | 376.9 |
| RC menu-v2 | 100 | 67.6 | 382.5 |
| RC budget-v3 | 100 | 67.3 | 381.2 |
| Battery Wave A | 11 | 16.5 | 66.6 |
| Battery Wave B | 21 | 27.0 | 115.7 |

Authenticated result reads took 16.8 seconds for original RC and 6.3 seconds for battery B.
Both reads made no native acquisition.
Battery contribution exports took 31.2 seconds for A and 75.5 seconds for B.
These exports retain producing receipts and the required evidence ancestry.
Completed recovery reuses those receipts and acquires no further native observations.
Allow additional time for storage, numerical-profile checks and the selected independent audit.
