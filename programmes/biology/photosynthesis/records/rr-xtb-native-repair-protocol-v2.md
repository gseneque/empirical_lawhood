# Rr native L-ANC fixed-boundary repair successor v2

SPDX-License-Identifier: CC-BY-4.0

**FROZEN before successor control contact.** This is an explicitly
exposed successor to the [frozen v1 protocol](rr-xtb-native-repair-protocol-v1.md),
SHA-256 `03106fdc3eef9fd9dac9a3ddb080da80e3e433cbb5c54c5ce77586168ed00cf0`.
It inherits every source, six-case inventory, field, proton, geometry,
stationarity, custody and scientific-scope requirement in v1 except the
specific optimizer, control accounting and execution bindings replaced below.
Role remains **DEVELOPMENT_VISIBLE / DEVELOPMENT_ONLY / NON_PROMOTABLE**.
Neither this successor nor its software tests admit a native calculation.

## Retained trigger and source-supported correction

The first native control operation retained **16 actual native processes**:
fifteen controls passed, the fixed optimization was refused, and its final
gradient remained unentered. All six enzyme cases remained unentered. Native
RF convergence after eight cycles did not preserve H1: its x coordinate changed
by **−0.03490786441185 Bohr = −0.0184724480419142945310 Å**, using the unchanged
legacy conversion. H2 moved equally in the opposite direction. The trajectory
records that motion during optimization; this is not a common display shift.
The **1e−10 Å** anchor tolerance is unchanged.

Both authenticated source trees contain the same defect in the selected RF
path. `src/optimizer.f90` unpacks the model's packed `fc` into dense `h` at
lines 473–480. The fixing projection subsequently modifies `fc` at lines
513–514, while `anc%new` at line 534 receives the unchanged `h`. There is no
intervening unpack of the projected array. Zeroing fixed gradients therefore
does not guarantee that the RF displacement preserves fixed coordinates.
This source diagnosis explains the observed failure; it does not certify every
possible failure of that upstream implementation.

Use the **existing native `engine=lbfgs` / L-ANCopt** path in the same admitted
executable. `geoopt_driver.f90` dispatches that selection to `l_ancopt`.
`relaxation_engine.f90` projects the packed Hessian first and then unpacks it
for mode construction. No executable patch, rebuild, Python optimizer, new
package installation or change to the GFN2 energy/gradient model is selected.
The upstream [optimizer documentation](https://xtb-docs.readthedocs.io/en/latest/optimization.html)
describes this existing selection; exact admitted source bytes determine the
protocol rather than the current documentation's examples.

| Exact source operand, common to admitted publisher/tag trees | Bytes | SHA-256 |
|---|---:|---|
| `src/optimizer.f90` | 43,855 | `3abe677b8b6ca333d85a69dca220910083118a75a16c9f4d60dd396c96d73b3b` |
| `src/relaxation_engine.f90` | 54,234 | `071317db3b064114d424734aa9c632a3e11c962de3f50708582703d2d1c13e97` |
| `src/geoopt_driver.f90` | 6,670 | `ed1249cb7a14bdf80f38599388a7c13f73b280734ce5dcd29a190546259d86ff` |
| `src/freq/project.f90` | 8,860 | `a81aec30f942c46fad9e32beed4d9e16b7094c151a298ff25fa0437070b49430` |
| `src/type/anc.f90` | 14,329 | `78be2335890c89dffbae5b40e91538b6d47388f317ec9b5fc6c643febd3b194c` |
| `src/detrotra.f90` | 4,229 | `37c4c0400e3854638a613abd9ba3dfd548e63c83308ac481bd7808b5793e422e` |
| `src/set_module.f90` | 92,524 | `c205d72cc1f842b5538072380eb1f5fc7b088956b576c3e289c82b841a7f1346` |
| `src/xtb/calculator.f90` | 16,945 | `95c0f402779a6c7ffbf355c8297a7161bed259f7cb2d3ef9739f909c8131ae00` |

Source inspection also bounds the two-H fixing control. The projection's
dependent and zero columns are handled by its orthogonalization routine;
the fixed H1 coordinates and rotational vectors leave a single H2 bond
direction. L-ANC also projects rotational directions in the enzyme cases.
In an external field those directions need not be force-free. Consequently,
the independent **unmasked Cartesian mobile L2 ≤3e−4 Hartree/Bohr** requirement
remains mandatory; a small projected L-ANC norm cannot replace it.

## Scientific selection and unchanged rejection rules

Only the fixed optimizer changes to `engine=lbfgs`. Retain GFN2, exact official
binary and parameters, charge/spin, 300 K, accuracy 0.05, SCC maximum 250,
hardness 99 and the complete held field with only exact zeros omitted.
Retain the same six ordered cases and all 31 fixed anchors, with Ha/Hb mobile.
Use `--opt vtight --cycles 60`, microcycle 20 and no averaged convergence.
There is no solvent, alternative model, DFT arm, new proton restraint or
alternative initial guess. Failed or escaped cases remain in the denominator.

The held v1b coordinate/field/control encodings are historical RF products.
Authenticate and compare those bytes under their original identities. Derive
an explicitly selected **new L-ANC stage plan** from those same admitted
primitive coordinates, field and fixed IDs. Bind its new control bytes and
plan identity before its native entry. Do not relabel old RF control bytes as
L-ANC inputs, reconstruct a new chemical context, or rewrite old fingerprints.
Default RF software behavior remains available solely to interpret its history.

Native result admission must verify the actual `L-ANC optimizer` path, exact
selected native arguments, microcycle/Hessian-reset and memory settings,
complete ordered cycle headings, initial/final SCC convergence, finite final
coordinates and unchanged anchors. The L-ANC convergence line reports
**CYCLES**, whereas the historical RF line reports **ITERATIONS**. Its printed
setup does not use every RF label; source-derived joins must not fabricate
absent native reports. Inner SCC iteration counts remain unidentified when
the native print level suppresses them. Complete normally converged cycle
headings allow source-inferred objective accounting; interrupted counts remain
unidentified where the evidence does not identify them.

Each enzyme optimization enters at most once and reserves the unchanged
conservative **101 objectives**: at most 99 realized source-bounded cycles
plus initial/final singlepoints. Its one separately cold unfixed gradient
reserves one further objective, within the unchanged **120 hard cap per case**.
No final gradient follows a refused optimization. All final energy, force,
proton, contact, bond, chirality and enolate thresholds in v1 remain unchanged.
No Hessian/frequency or kinetic inference is selected.

## Finite successor controls and cumulative accounting

Select a separate `rr-xtb-native-controls-v2` packet and execute the same
seventeen-command menu, in the same order and with the same H2 coordinates,
asymmetric field, finite-difference steps, common translation, full D263N V2
capacity field and acceptance criteria. Only the fixed optimization uses the
new native engine. The subsequent gradient remains unfixed and independent.
All six enzyme rows remain unentered until the complete successor passes.
The exposed v1 refusal is separately retained and charged; a successor label
does not erase a process or create fresh evidence.

For this control only, keep requested maximum 20 and microcycle 1. L-ANC uses
**ceiling** when growing a microcycle: 1 becomes 2. It can finish at cycle 21
after crossing the requested boundary. Reserve **23** objectives for that
optimization, including its initial/final singlepoints. The other sixteen
commands reserve one each: **39 source-bound objectives**, within a **48 hard
control cap**. No call is selected to fill unused reserve. The preceding
operation retains its admitted count 15 and conservative entered reservation
37; independent raw/source review identifies eight converged cycles and hence
25 source-inferred objectives. These distinct accounting statements are not
interchanged. Carry its conservative 37 into the inquiry's combined control
hard bound **85**, and the six case caps into the whole hard bound **805**.
At most **33 control processes** can have started across the two control
operations, plus at most twelve enzyme commands; the two metadata probes
remain separate prior processes. Actual use must be reported.

Keep the original whole-operation monotonic start **647960.547165464** and
deadline **652160.547165464**: total 4200 seconds, with no reset for this
successor. The original complete control worker cost **1.213371 CPU seconds**
is charged against the shared 20-second control CPU allowance. Select an
18-second CPU cap for the successor's complete cold worker and native children.
Its separate wall cap remains 120 seconds within the same whole deadline.
The preceding full outer launcher measurement reports rounded **8.02 CPU /
8.28 wall seconds**. Charge a conservative **8.04 CPU seconds** against the
shared 200-second parent allowance and cap the successor parent at **191 CPU
seconds**. Charge its actual complete outer cost too before allocating the
case caller; counting child cost again in this parent reserve is conservative.
Case caps remain **300 CPU / 600 wall seconds for each complete cold case
worker**, including setup, self time, all waited native children, checks and
the final diagnostic. The six-case roster has **1800 aggregate case-worker CPU
seconds**. Outer caller/custody costs use the separately shared parent allowance.
Memory remains 4 GiB with one native thread. There is no compute-budget
reset or hidden uncharged recovery run. These allocations remain within the
original conservative 2020 CPU / 4200 wall whole envelope.

The new control and case packets share the original **64 MiB** physical cap,
16 MiB member cap and 1 GiB scratch cap. The closed v1 predecessor is immutable
ancestry: **328 files / 19,698,076 bytes**, census SHA
`a45181c3b890e5dc641e7910cd32a237d26a102c688e3b1660e8d90592f77397`.
Count it separately, including its archives and duplicated physical members.
Reserve 64 KiB for each complete outer-launcher witness. Thus the cumulative
selected packet scope is bounded by **64 MiB + 19,698,076 bytes + 128 KiB**;
the older source/profile/software packets retain their separately declared
ancestral footprints. Do not silently fold predecessor bytes into, or hide
them from, the new control/case budget.

Monitor whole elapsed time and waited CPU before native entry, during polling
and **after wait**, including a process that exits between polls. Re-read its
complete stdout for actual cycle headings and apply final CPU/wall/storage
checks. Setup/hash/input-write time belongs to the selected stage window.
Preserve genuine custody, every raw byte and all refusal/no-entry rows under
new locators. Native execution, independent replay and complete closure must
all pass before enzyme entry. An additional failure does not select another
optimizer, retry or relaxed criterion.

## Execution bindings to freeze before contact

The following selected bindings precede successor control contact. The
configuration binds this protocol's resulting exact bytes, these operands,
the full package inventory and all inherited source/profile/input censuses.
The caller prepublishes them through genuine local artifact custody before
starting its worker. No native control has entered at this freeze.

| Selected operand | Bytes | SHA-256 |
|---|---:|---|
| Additive maintained `rr_xtb_repair.py` | 43,562 | `04633934f8222f8641466dd4c180bf8a864b80d02cd1617ae47fbd4d7b380238` |
| Maintained focused test owner | 24,818 | `0be7c21980ed47754eb4f8c2996e827d6e87201b0b0485b0c362e38389936abe` |
| `/tmp/rubisco-xtb-control-work-v2/launcher.py` | 32,030 | `fad9e838981c35800df0e6417c9de204017e23e864f29abcbd7cd8cb7b2f76e1` |
| `control_worker.py` in that directory | 24,821 | `8562eeea2f49d16607b32ee9e0a0d0d0984c31c4ea80d7c7ae01734c94075393` |
| `control_oracle.py` in that directory | 26,457 | `5de75075eb1b3cffd298c0f81811a9839e64f231510cdb06819acc207ae1463b` |
| Source-only fixing audit | 13,299 | `b7e4edfc42c320f8dc3e5d30ff8b0e550acfa82e3818cda6044fe1eb684ba0d7` |
| `uv.lock` | 995,920 | `ea491f9e8789d6cd5a18d89908d16ef7db4ee3c9ed4729e32354bc713b135f24` |
| `pyproject.toml` | 3,660 | `56876d8834198793534e56c8bbb8ff9dcd36dd4aeee68a326b6271fdefe06649` |

The canonical full-package inventory has **2,369 members**, fingerprint
`260bd1c2002009d10851b42b2223054918e7e36b1b2525d7abe5390ebcf22db1`.
The producing archive retains every member and the selected private helpers.
The additive owner retains historical default RF plan identities; explicit
L-ANC stage identities and exact native program-call joins are separate.
Maintained checks pass **29** cases; private control tests pass **18**, and
case API/runtime tests pass **13**. These are exposed software checks.

The eventual six-case caller/worker/replay helpers require a separate binding
before enzyme entry, under selected packet `rr-xtb-native-repair-v2`. That
binding may not alter any scientific criteria above. Development, review and
software-check windows retain their own measured or unidentified costs;
the 2020 CPU / 4200 wall envelope bounds the selected control/case execution
and custody allocation, rather than all historical agent or inspection work.
