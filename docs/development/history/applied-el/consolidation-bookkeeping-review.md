# Consolidation bookkeeping review

SPDX-License-Identifier: CC-BY-4.0

This review retains historical setup measurements and the
[current shared-reader controls](#current-shared-reader-controls-18-october).
The early E3 checkpoint below stopped after128 successful native prefix tasks
and one PURE fitting failure; it is not the current scientific status.
The authenticated programme report owns scientific status;
the [coverage map](../../../release/implementation-coverage.md#matrix-phases) describes the implemented routes.
Scientific completion, software conformance and scientific qualification remain separate acceptance claims.
This dated review retains earlier measurements without prescribing a continuation or current release gate.

## Why the metadata reached 3.65 GB

The standard issue's atomic publication has 2,211 members. Each sidecar embeds
the complete publication roster, about 1.65 MB, instead of a reference to it.
Together with the separately published receipt, its 2,212 sidecars occupy
3,651,222,145 bytes. The complete roster is also already in the durable commit.
Repeating it in every member adds no cryptographic protection over an exact
commit reference with validated membership and complete sibling verification.

The implementation also reconstructed and hashed that roster for each sibling,
retained each encoded sidecar during staging, and loaded the base repeatedly
during extension issuance. These were implementation choices. A04 explicitly
requires removing repeated embeddings and redundant closure verification; the
earlier component checks did not establish that acceptance at the selected size.

## Necessary checks and redundant work

| Boundary | What must remain | What can be removed or simplified |
| --- | --- | --- |
| Scientific interpretation | Original equations, Decimal values, canonical scientific records, independent units, complete denominators and adverse or unevaluable outcomes. | Repeated physical representations of those same facts. Metadata volume is not additional scientific evidence. |
| Prospective entry | Actual source/input binding, reservation before TRAIN, separate model and calibration freezes, both forecasts before future acquisition. | Manual maintenance of generated task/resource rosters. Derive them from the selected specification. |
| Authority | Genuine applicable acquisition, execution, reveal and publication authority; current expiry and scope checks at their existing boundaries. | Approval ceremonies for ordinary reversible code repairs, or caching a grant verdict with immutable metadata. |
| Immutable publication | Exact payload and logical identities, one complete committed member roster, collision checks, durability and interrupted-publication recovery. | The complete roster in every sidecar, repeated full-roster decoding, and retaining unused encoded sidecar copies in memory. |
| Verification lifetime | Fresh transport/input checks, complete sibling and payload validation, mutation guards and checks at the end of the owning operation. | Rebuilding an unchanged base four times inside that same guarded operation. Later invocations still authenticate it afresh. |
| Execution and recovery | Actual worker/source evidence, reservation and launch charges, original receipts, conservative UNKNOWN handling and no repeated acquisition. | Requiring an unchanged executing checkout to read completed evidence, inventing a resource STOP that was never declared, or scheduling unused tasks merely to close failed history. |
| Storage admission | Selected bounds and early refusal when actual capacity is insufficient. | Discovering descriptor exhaustion after staging, staging an already committed replay, or silently imposing a scientific population limit to accommodate metadata duplication. |

The full-checkout identity requirement also coupled operational engine repair to
unchanged scientific workers. The explicit continuation route retains the
original native source and charges while permitting reviewed PURE/operational
repairs. It does not allow source relabelling, native retry or spent-attempt reset.
Its implementation and actual selected execution still need separate acceptance.

## Implemented and measured

The historical sidecar reader now compares the exact known publication bytes
and decodes only each member's own metadata. Its ordinary strict decoder remains
available, and every original byte is retained. The publisher no longer holds
an unused full sidecar payload for every staged member. Extension issuance uses
one guarded base-load lifetime, without retaining an authority verdict.

The decoder has 31 focused controls; publication and integrity integration has 70
controls; guarded base reuse has 13 controls. Two-size measurements demonstrate
fewer roster constructions and lower traced allocation. Commands, source pins,
earlier failures and measurement limits are retained under the selected external
evidence root in `publication-known-binding-codec-01`,
`publication-bookkeeping-owner-controls-02`, `bookkeeping-optimisation-01` and
`publication-bookkeeping-scaling-01`.

A real read-only load of the original composite issue passes in 57.34 seconds,
with 55.28 CPU seconds and about 1.0 GiB process peak RSS. All 4,426 selected primary
file identities remain unchanged; all 2,212 original sidecars and both markers
match the earlier terminal audit's hashes. This measures the composite reader,
not issuance, worker execution or numerical computation. The earlier 112-minute
issuance is a different operation and is not a like-for-like timing baseline.
The extra comparison change did not establish a whole-reader speedup over the
first 58.52-second measurement.

New issue publications use compact physical sidecars referring
to the existing commit. Normalisation returns the original typed manifest;
scientific records, issue payloads, commit identities and legacy readers retain
their contracts. Existing sidecars keep their original representation during
replay and interrupted recovery. Ordinary run inputs, receipts and native-worker
sidecars retain the legacy representation for source compatibility.

Compact transport and legacy codec integration have 85 controls. Publication and
integrity integration has 57 passing controls; the final new publication file
separately passes 13 controls with stable source, including stream replay. Public issue routing has 17,
including a 257-member inventory, immutable replay and corruption; fresh public
provider reconstruction passes with zero worker execution. Six public
receipt-only reconciliation controls also pass with the integrated format.
The retained packets are `compact-sidecar-transport`,
`compact-publication-owner-02`, `compact-publication-new-controls-03`, `compact-issue-routing-02`,
`compact-provider-reconstruction-02` and `compact-public-provider-reconcile-01`.
The latter preserves the initial new provider test's incorrect extension filename
and its correction; its six reconciliation and two stream controls passed.

The 16/64-member software measurements show approximately fourfold physical
metadata and read-volume growth for a fourfold population increase. They also
verify exact replay without staging. The 2,211-member software storage/setup
measurement passes: the same roster requires 2,871,129,968 legacy metadata bytes
versus 6,209,030 compact bytes, a 462.4-fold footprint reduction. The legacy size
is computed exactly and checked against three canonical expansions, without
writing another multi-gigabyte copy. All 4,423 new primary files remain unchanged
after exact replay, which performs zero staging calls. These controls use exposed
software fixtures, including synthetic authority where explicitly declared.

Full-size publication takes 610.95 seconds, read/verification 44.87 seconds and
replay 20.81 seconds. The retained release is
`publication-bookkeeping-scaling-01/compact-full2211-01-release.json`. Timing
includes allocation tracing and a shared disk; it is not an isolated throughput
benchmark or the earlier complete issue operation. The full-size measured source
is retained. A subsequently identified repeated construction of the same owned
path set has been hoisted outside the publication loop; focused regression checks
are separate from that timing result.

Physical-byte scaling is distinct from CPU scaling. The earlier measurement
included the original sorted-tuple membership scan. The current owner uses
binary search over the same immutable roster, with exact canonical identities
and substitution refusals preserved. That change has comparison-count controls;
the earlier timing is still the original measurement. Unscoped provider and
catalog verification costs require whole-operation measurements. Current compact
ISSUE consumers have been independently checked for format coverage.

The backup/filesystem-change hold applied at this checkpoint. On 17 October the
researcher selected EL as the default external/run artifact storage, superseding
the artifact prohibition for work there; use the
[current storage guidance](../../maintainer-environment.md#storage-and-retained-evidence).
Bookkeeping acceptance does not close the selected run's failed-history
reconciliation, mixed-source continuation or assessment/read/recovery acceptance.

Existing 3.65 GB of historical metadata will not be rewritten to manufacture a
storage reduction. No setup measurement establishes fresh scientific results or
closes S1–S6/A01–A10 acceptance.

## Current shared-reader controls, 18 October

The original E2 metadata census was interrupted after four hours, retaining child
exit143 and creating no census publication or new native contact. Its completed
public scientific read on source `0990954a` remains unchanged:96 assigned roots,
28 usable adverse,64 numerically unevaluable and4 missing, with zero successes.
A fresh custody check on the next committed source remains required before TRAIN.
Custody completion cannot promote scientific outcomes.
The [coverage map](../../../release/implementation-coverage.md#matrix-phases) owns the current
scientific and release status.

The later source `54e00cb3` retains 441 distinct passing software controls across
five source-attributed cohorts, including 23 compact output and 42 receipt/event
controls. Earlier failed attempts remain retained. The actual default public
E2 compact read was deliberately interrupted after 1,229.186 seconds; its
supervisor retained exit 143, identical original custody snapshots and unchanged
source and plan documents. This is an incomplete read, not a passing performance
or scientific result. The interruption and quiescence proof is
`repetition18/public-e2-compact-acceptance02-source54e0/actual-acceptance01/coordinator-interruption01-completion.json`
under the external release-preparation remediation root, SHA-256
`b14e30a76987d67894fd53428f66b56400cc4dddb334497cc9e117668bb0eb2d`.

Tracing that real consumer found remaining per-input and per-reused-receipt
whole-snapshot checks before the already repaired batches, plus second hashes of
freshly authenticated bodies. The selected run has 1,735 imported inputs and
761 successful receipts. These are structural counts, not measured CPU cost
attributions. The bounded repair passes the 39 new public-consumer controls
within a source-stable 349-case cohort on `abb95349`. Actual 4/6-task comparisons
preserve exact serial reports: snapshot calls fall from 26/42 to 9/9 and duplicate
body hashes from 11/18 to zero. Code-entry and declared hashing-byte counters do
not establish total disk I/O, assessment memory or whole-E2 speed.
The existing immutable canonical-record cache already makes repeated plan and
index fingerprints inexpensive; no additional identity cache is warranted.

The earlier applied source passed45 focused artifact/custody controls without skips.
They cover plural publication verification, scoped reuse, selected header reuse,
ancestor substitutions and changed bodies. Three release-profile controls also
retain both passed and deliberately failed byte-only fixture evidence; the
current workflow-inventory control passes. The expanded release check found stale
integration examples. Explicit version 6 successors preserve all 44 historical
files; 19 succession controls and all nine owning-generator checks now pass,
alongside lint and documentation. These remain exposed examples and create no scientific qualification;
source-bound consumer and complete release acceptance remain separate.
That source also passed60 focused codec, forecast, response, future,
selected-worker and retained-source controls without failures or skips. These
retain Decimal parity, adverse outcomes, complete denominators and fresh reads;
the controls entered no native work. Actual public lifecycle acceptance remains
separate from these disclosed software fixtures.

Current V12 generation preserves all 98 earlier files and 88 deep scientific
comparisons, adding zero scientific units. Its nine owning-generator checks,
affected lint and documentation checks pass. The 39 new runtime controls above
exercise actual public consumers, inherited method/descriptor hooks, customized
output readers and adversarial mutations. The separate pure constructor check
validates both workloads and nine metadata forgeries; it creates no authority.

A complete two-root metadata comparison on source `0990954a` retained the same
18 tasks, 56 authored members and exact original records. Baseline versus staged
owner times were 21.092 versus 18.549 seconds for loading and 2.236 versus 2.847
seconds for retained plans: 23.328 versus 21.396 seconds together. The complete
instrumented process took 36.24 versus 34.63 seconds. Shared storage, cProfile,
audit and staging differences preclude a whole-workflow speedup claim.

Strict selected-member header scans remained 55. Generic canonical scans rose
from 62 to 74 and authored-file opens from 368 to 404 across both owners, exposing
missing reuse of successful publication keys inside the existing read scope.
The separate scoped-key repair is applied and its installed controls pass;
its measurement remains pending. Baseline
read-volume and memory counters were absent; after-only counters establish no
reduction. Generic validation and strict headers retain their distinct guarantees.

| Repeated work or integrity defect | Shared owner and retained boundary | Current evidence and remaining acceptance |
| --- | --- | --- |
| Per-member publication verification during authored construction | The plural artifact consumer authenticates complete publications; custom policy hooks retain their original admission route. | Installed focused controls pass. The complete two-root metadata comparison above is measured; selected-size read/recovery acceptance remains open. |
| Repeated publication scans after a successful callback | Existing read-scope keys remain bound to validator and semantic contexts and are retained only after the final snapshot guard. Failed callbacks do not warm the scope. | Six installed controls pass. A measurement of this repair remains pending. |
| Per-input whole-snapshot checks before product reading | `_external_inputs` batches only stock readonly lazy inputs. Full reads close an input-only verification scope before typed products; compact reads reuse their existing scope. Original specification, access, profile, media, lineage and size checks remain. | Verified by 39 new public-consumer, two-size and adversarial controls within the 349-case cohort above. Custom, writing, eager and out-of-bound routes retain serial verification. Selected-size measurement remains open. |
| Per-successful-receipt snapshot scans and second hashes of freshly verified bodies | The stock compact receipt window uses an initial snapshot and the existing plural output guard. Exact authenticated physical/logical equality removes only the duplicate hash. Full typed-output and custom-hook paths retain their original checks. | Focused public-consumer and mutation controls pass in the cohort above. Selected-size acceptance remains open. No persistent proof, authority cache or scientific result is introduced. |
| JSON parsing before the typed consumer | Authenticated payloads retain exact member/header proofs; every get still checks current custody, schema/version and body identity. | Six installed controls pass, including mutation and changed codec/registry paths. Installed scientific-read acceptance remains open. |
| Ancestor-link substitution in unscoped final verification | Scoped and unscoped verification share guarded path resolution and complete snapshot checks. | The original source reproduces the gap with unchanged leaf identities; nine installed ancestor controls and four scope controls pass. |
| Repeated mechanical archive expansion in forecast and response scoring | One closed decoded input binds exact received bytes and the complete descriptor within the worker invocation. Independent cold science and final byte/record comparisons remain. | The installed60-control batch above passes, including Decimal and adverse-result parity. Actual public lifecycle acceptance and assessor memory/timing remain open. |
| Discarded protected handoff decodes | The handoff reuses decoded roots while its loader authenticates all 14 members and independently required proofs. | Twenty installed retained-source controls pass, including mutation, omission, decode parity and fresh-source admission. Public scientific lifecycle acceptance remains separate. |
| Repeated metadata loading in TRAIN export, source certification, E4 and nomination reads | Corrected read-context02 shares one guarded metadata lifetime and repeats the complete original admission block before target products. Custom policy and oversized requests keep fresh fallback admission. | Twenty-one committed-source read controls pass, including actual TRAIN support mutations before target inputs. The follow-up28 controls pass, including all four real parent/origin mutations and authored-only source refusal. Actual scientific-consumer acceptance remains separate. |
| Indirect repeated complete E4 acquisition reads during input derivation | One complete selected reader supplies the locator and observations. Original locator and scientific-observation checks remain shared private finishers; partial derivation retains its separate replay. | Exact-tail and interface review and seven focused software controls pass, including malformed scope, config, callback and missing-entry refusals. Actual DEV source acceptance remains required. |
| Repeated full TRAIN and E5 DEV validation during prepared-source assembly | One guarded derivation supplies exposure facts and certificate construction. The early TRAIN metadata check remains, initial and current FILE supports stay fresh, and later calls reconstruct independently. | Independent review preserves the exact scientific certificate and source-root tails. Nine disclosed composition controls pass, including real FILE mutations; actual E5/E6 source acceptance remains pending. |
| Duplicated development/issued product assembly | One private assembler preserves both public outer admissions and the two original issued receipt rules. No scientific record, schema or cache is added. | Both selected mode bodies match the original core AST exactly. Actual PURE development reads pass with identical reports; issued scientific-consumer acceptance remains pending. |
| Completion receipts decoded again after the operational census | The assembler can reuse its existing typed attempt map only under the stock active verification scope, with a fresh complete snapshot before each use and unchanged receipt identity/static checks. Other policies retain their original reads. | Seventeen committed-source PURE controls pass. Successful receipts are read once under the stock scope and twice under the original fallback, with exact reports and mutation refusals. Stock compact output/event traversals now use the separately tested guarded batches; full typed-output and custom paths retain their original checks. |
| Deferred binary validation missing from public readout | The assembler and API share the existing raw-bytes status constant. Exact binary custody still requires its domain-specific consumer join. | Six committed-source report-propagation controls pass, using real PURE custody with a disclosed product-state seam. The historical status value is unchanged; these controls do not establish completed binary or native acceptance. |
| Consumer refusal reported as missing custody | Artifact verification wraps its own I/O failures; consumer exceptions retain their exact type and identity. Final snapshot guards and failed-read cleanup still run. | The corrected owner passes53 artifact/custody controls, including eight exception and mutation cases. Its committed-source public PURE refusal control also passes. Actual native-consumer acceptance remains separate. |
| Incomplete release-test retention | One release option owner selects packet-owned fixture/cache destinations and retains passed and failed evidence. | Three installed profile-wiring controls retain both passing and failing fixture bytes. The complete settled-source release gate remains open. |
| Candidate evidence rejected by stale release reuse checks | The candidate producer and reuse verifier share the current retention policy and exact pytest options. Copies preserve the original destinations and source/log/coverage bindings. | All104 focused release controls pass, including copied packets and altered-policy, filtered-suite and failed-check refusals. No full portable suite, artifact build or scientific qualification is claimed. |
| Repeated source hashing in example generation | Sibling source templates share one local package digest and dependency-lock read; each historical file is retained from its single authenticated read. | Other unchanged helper calls still compute their own digests. Their cost is unmeasured; no persistent cache or change to scientific source records is introduced. |
| Knowable baseline/request refusal after a complete E2 custody read | The next publisher authenticates both typed operands before its one complete E2 read and retains the original later checks inside the same verification scope. | Actual baseline/request preflight and final scope exit pass. The source11 census05 main read completed in 386.772 seconds before RAW sibling identity refusal; its failed operation remains retained. No persistent resumable proof or E2 reacquisition is introduced. |
| Plain historical RAW registration differs from the installed codec group | Integration composition binds only the exact historical schema/profile/version/digest to the target resolved by the current registry. The core validator, codec contracts and physical guards remain unchanged. | Eleven new controls pass within the committed-source 255-case cohort; two separate actual API/CLI root controls also pass. The genuine baseline's complete atomic batch authenticates. Changed observations, sibling bytes, claims/media and explicit limits still refuse. |

No persistent scientific, source or authority cache is introduced.
The original canonical and historical bytes, full publication rosters and fresh
authority boundaries remain required.
The earlier 1,425 selected E2 outputs implied 2,850 per-output snapshot boundaries.
The applied whole-output batch now performs metadata and lineage preflight before
body access and passes the 23 controls above. Receipt/event batching passes its
separate 42 controls. The input and receipt-reuse repairs have the focused public acceptance above;
selected-size completion and whole-workflow speed remain unestablished.
The selected-size read, recovery and source-stable workflow still need their
actual measurements after source integration.
The separate independent paired-refinement assessment passes on `abb95349`
over 24+24 actual coarse/fine branches, with exact canonical NPZ/framed parity.
Its fixture's actual native use remains disclosed; it supplies no study result.
The final portable suite remains required.

Further repeated numerical work is removed in `9f922cae`: truth extraction falls
from 240 cells to 48 view/panel/action/horizon values, and each fixed-action
response batch constructs its common reduced operator once. Independent
exact-original, Decimal and adverse controls pass. The
[implementation evidence](../../../release/implementation-coverage.md)
distinguishes the source-attributed cohorts and their measurement limits.
The corrected unsampled-step fixture and original failures remain preserved.

Both source-certificate APIs on `02c1c826` authenticate current raw FILE supports
before cold scientific replay, then retain their original final and warm-cache
freshness guards. Twelve focused controls and the retained native certificate,
custody-only recovery and full read pass without reacquisition. The original
public control's late-order failure stays retained. No persistent authority or
scientific cache is added.

Two residual in-memory scans remain: native-contact expectations rebuild a
per-root map and selected E4 input derivation searches its product index. Their
cost is unmeasured and neither repeats a payload decode; no speculative cache
is introduced. The existing checkpoint binds the actual results and exposures.
The critical path now performs one guarded E2 census read. A separate standalone
default-CLI selected-size compact acceptance remains POST_MATRIX_RELEASE_OPEN,
alongside installed-wheel positive read/recovery, full workflow measurements,
critical coverage, artifact checks, retirement and RA8.
