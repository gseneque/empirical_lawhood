# Operational limits audit

SPDX-License-Identifier: CC-BY-4.0

**Removed from active work by user instruction on 11 October 2026.**
The tables below document the original selections and their effects. See the
[removal record](limit-removal.md) for that historical unrestricted allocation.
Later selected profiles and frozen task budgets retain their own limits.

The **512 MiB Rubisco ceiling was selected by the coordinator**, not required by
Rubisco science or prescribed by the adopted refined plan. It was an uncalibrated
estimate for small pure source/table computations. That selection did not account
for the Python interpreter and composed runtime imports. The handoff explicitly
requires measurements and decision tolerances to justify numerical allowances
(the archived operational handoff, excluded from distributions).

The executor interprets `memory_bytes` as **virtual address space, `RLIMIT_AS`**,
although the RA0 table called it peak RAM. The later engineering import probe
measured 650,208 KiB / **634.97 MiB virtual space**, versus **318.78 MiB RSS**,
before a scientific task. The isolated Rubisco operation import used 151.93 MiB
virtual space. Thus the selected ceiling was below the measured composed startup
footprint. This supports an unsuitable allocation/startup combination; the
original caught failure did not retain a stack or exact memory measurement.
See the [memory audit](memory-stop-audit.md). The limit provides no biological
finding and should not have obstructed routine implementation repair.

## Numbers added by the coordinator

The original plans require bounded work but do not prescribe the following
absolute RAM, CPU, wall or storage values. Unless indicated otherwise, they lack
a cited pilot workload or quantitative headroom calculation. Their historical
selection and failures remain preserved; approval to reopen does not rewrite
those bytes.

| Selection | Imposed values | Basis and practical effect |
|---|---|---|
| Pure compact operation | 512 MiB address space; 60 CPU s; 120 wall s; one core; 4 MiB output; 16 MiB scan; one attempt | Small-workload guess. Memory proved inadequate for composed imports; one attempt made the startup failure terminal. [actual closeout](../../../../programmes/shared-records/applied-el/closeout.md) |
| Whole compact pair | 600 CPU s; 1,200 wall s; 1 GiB; 256 MiB retained; 24 operations; two waves/domain; depth three; zero scientific repairs | Coordinator programme ceilings, without a cost derivation. The reopened 2 GiB worker proposal must also replace the incompatible original 1 GiB whole-process declaration. [actual closeout](../../../../programmes/shared-records/applied-el/closeout.md) |
| Shared engineering/checks | 7,200 measured CPU s; eight coordinator hours; 16 summed worker hours; 4 GiB/check; 1 GiB output; two repair cycles per failed focused check | Coordinator choices. Fixture work required additional amendments despite ordinary software defects and unchanged scientific claims. [completed software checks](../../../../programmes/shared-records/applied-el/programme-closeout.md#changes-and-software-checks) |
| Read-only battery audit | 300 CPU s; 600 wall s; 1 GiB; 5 MiB output; zero native contacts and setup repairs | Coordinator limits. Audit CPU/wall/RSS were unmetered, so adequacy and actual expense were not demonstrated. [Audit](../../../../programmes/energy/battery-charging/records/battery-entry-audit.md) |
| Battery D1 | 300 CPU s; 600 wall s; 2 GiB address space; one worker; each task one core, 100 wall s and one attempt; 64 MiB custody, 4 MiB scientific output/task, 64 MiB scan; zero native retries/setup repairs | The **2 GiB** value has an import-headroom rationale: measured composed peak virtual mapping 989,216 KiB left only about 58 MiB under the earlier 1 GiB proposal. Full solving adequacy was still untested. Other exact values are coordinator estimates. [Entry](../../../../programmes/energy/battery-charging/records/battery-d1-entry.md) |
| D1 numerical investigation | At most three solves: 23/27 °C primary and one optional tighter 23 °C view; 20 mesh points; primary rtol/atol 1e-5/1e-6, 10 s outputs; tighter 1e-7/1e-8, 1 s outputs; solver dt_max 10 s | Selected numerical design, without an accuracy-derived convergence allocation. It admits a time/tolerance refinement but no mesh-convergence study. [Service selection](../../../../programmes/energy/battery-charging/records/battery-service-selection.md) |
| Proposed fresh Rubisco programme | 900 CPU s; 1,800 wall s; two engineering/review hours; zero GPU; 64 MiB output; 16 MiB scans; eight operations; two waves; depth three; zero native contacts/new source acquisitions; 15 minutes setup; zero scientific repairs; one check repair; 60 CPU/120 wall s per operation | Coordinator proposal, not a plan-prescribed allocation. No pilot derivation supplied; its two-wave scope is narrower than the original four-wave programme. [Proposal](../../../../programmes/biology/photosynthesis/records/rubisco-scientific-selection.md) |
| Proposed Rubisco panel/model scope | Four hypotheses; nine full recipes; frozen 5 × 3 transport sensitivity grid; no grid expansion/new parent/new acquisition/rescoring-control expansion | Designer-selected restriction; these are scenarios, not measured transport probabilities or biological coverage guarantees. [Exact selection](../../../../programmes/biology/photosynthesis/records/rubisco-scientific-selection.json) |
| Storage and preservation | 256 MiB free-space floor; one worker; 64 MiB producing-source archive ceiling | Operational choices. The floor ensures writable custody; no scientific result depends on these exact numbers. [closeout](../../../../programmes/shared-records/applied-el/programme-closeout.md) |

Two restrictions actually blocked work: **512 MiB address space** stopped compact
acceptance, and **zero setup repairs** made the first D1 programming defect a stop
despite only 12.85 of 300 measured CPU seconds used. Neither failure revealed a
Rubisco or charging limitation. Software repair needs its own bounded engineering
allowance; it must not be conflated with changing a scientific endpoint or
inventing fresh experimental evidence.

## Original design recommendations and existing software restrictions

The archived refined Rubisco plan described these choices as **design recommendations**.
They were not coverage guarantees or experimental findings.
The following list records those historical choices without requiring the external plan:

- 12–24 starting candidates; up to six parents, eight singles/parent, six
  assemblies, twelve combinations and 72 total candidates; roughly 8–12 active
  candidates and 3–5 finalists.
- Four waves; at most two targeted investigation rounds, four investigations per
  round and one newly prepared physical study. Further variants need a justified
  decision-value argument within the remaining allocation.
- Effort shares 20% routing, 40% investigations, 20% assessment/challenge,
  10% dossier and **10% setup/repair reserve**, expressly reallocatable. The
  coordinator's zero-repair choice was stricter than this recommendation.
- The historical molecular route's 200 cumulative parent CPU seconds and
  18.936673 seconds remaining are a historical operational budget. They are not a
  biochemical limit or the automatic allowance for new search. Molecular PARK
  remains a separately adopted scope decision.

The archived TOP5 plan selected one active battery change, one supplier, one distinct later
charging decision and one subsequent reuse test; normally two explanations,
with a third when needed for discrimination. These are programme-design choices,
not scientifically necessary maximums. Expanded studies were explicitly deferred
by that historical scope.
The [programme closeout](../../../../programmes/shared-records/applied-el/programme-closeout.md) records the selected studies and their actual limits.
The [Rubisco programme contract](../../../../programmes/biology/photosynthesis/records/programme-contract.md) states the biological targets.
Current storage and environment instructions are in
[environment reuse](../../maintainer-environment.md).

Existing portable export limits of 64 MiB/member and 128 MiB aggregate are
software transport restrictions. The new inquiry implementation additionally
caps state sources and ancestry at 24 waves, measurement paths and previous
decisions; 32 MiB decision packets; 16 MiB decoded members and 1 MiB manifest
controls. These keep I/O bounded; their exact values are implementation choices,
not scientific limits. The separate selected depth-three policy is more
restrictive. RECURARCH already identifies a historical 478,155,048-byte material
output that exceeds portable transport, and defers its production extension.

## Criteria that define the scientific question

These must be distinguished from compute/repair guesses:

- Rubisco's two target endpoints, same exact candidate, compatible assay/reference
  conditions, no compensation of one endpoint by the other, and preservation of
  unknown kinetics define the nomination claim. Changing them after seeing data
  would change the question. Neither arbitrary RAM nor an arbitrary candidate
  count establishes those endpoints.
- Battery SOC 0.30, 23/27 °C preparations, 900 s top-up and 0.36375 A·h target
  define the selected service. **900 s is explicitly a researcher choice**, not
  an OEM mandate. The target is exactly 1.455 × 900 / 3,600. Manufacturer/source
  current, voltage and temperature constraints have their own documentary basis.
  They are not memory or execution-time budgets.
- Scientific negative outcomes, independent-unit accounting, source/preparation
  identity, outcome cutoffs and the absence of whole-time certification remain
  evidential requirements. A successful numerical trace cannot create physical
  replication or continuous-time safety proof.

Reopening was approved by the user, who subsequently removed the operational
ceilings. Active declarations now use explicit unrestricted budgets and record
actual expense; ordinary software repairs have no count or duration ceiling.
Scientific endpoints, original records and separately deferred campaigns retain
their declared meanings.
