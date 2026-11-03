# Open electronic pilot recovers the exposed carbon-site ordering

SPDX-License-Identifier: CC-BY-4.0

Recorded **10 October 2026, Australia/Sydney**, on `recchain`. All **eight
fixed-geometry SCF jobs converge**. The four anion cases pass the complete
primary Löwdin carbon-ordering criterion in the
[frozen successor protocol](enolate-electronic-protocol-v2.md). Both primary
Löwdin and secondary Mulliken populations also recover all eight displayed
site-change directions. This is a successful, exposed reduced-substrate
electronic-method assessment. It supplies no enzyme mutation, reaction rate,
kinetic prediction, biological qualification, consequential EL result or
nomination; no additional programme phase closes.

The [actual reaction-input/preparation result](reactive-preparation-result.md)
supplies the source context. The original
[Douglas-Gallardo et al. study](https://doi.org/10.1021/acscatal.2c01677) and
[released geometries](https://zenodo.org/records/6791151) use a frontier-orbital
Hirshfeld-I partition. The declared successor populations below are different
observables, rather than a quantitative reproduction of that partition.

## Complete scientific result

The four authenticated C4H7O3 geometries retain their native atom order and
coordinates. B2/B3 use source-labelled B3LYP/6-31G(d) geometries with the
declared B3LYPG/6-31g* realization; W2/W3 use omega-B97X/def2-SVP. Each has
an anion singlet and a vertical neutral doublet calculation, with 56/55
electrons. These charge/spin choices remain explicit successor chemical
hypotheses, not authenticated original XYZ job cards. There is no optimization,
retry, fitting, state switch or substituted population method.

All anions converge in thirteen SCF cycles; neutral cases take 17/17/17/16.
Each realized grid has 309,168 points at level 4. The basis census is 112 AOs
for B and 133 for W. Full coefficients, occupations, overlap matrices, density
matrices, logs and electronic states are retained. The HOMO density is normalized
to **one electron**, without multiplying by its closed-shell occupation of two.

| Case | Primary C2 | Primary O2 | Primary C3 | Primary O3 | Frozen carbon criterion |
|---|---:|---:|---:|---:|---|
| B2 | 0.106689734 | 0.255329935 | 0.355348729 | 0.177841336 | C3 > C2, pass |
| B3 | 0.322766301 | 0.140374625 | 0.116256062 | 0.333017345 | C2 > C3, pass |
| W2 | 0.105436219 | 0.256997872 | 0.373864013 | 0.167316403 | C3 > C2, pass |
| W3 | 0.345264346 | 0.141534322 | 0.132778865 | 0.300009830 | C2 > C3, pass |

All four carbon margins have the required sign; their magnitudes range from
0.206510239 to 0.268427794. Both functional pairs pass. From enolate 2 to 3,
C2 and O3 increase while O2 and C3 decrease in both families: **8/8 directions**.
The secondary Mulliken partition independently retains **4/4 carbon orderings
and 8/8 site directions**. Complete fourteen-atom vectors for both partitions
remain in the anion job records; all selected-site differences from the matching
native table points and assessment summaries remain in `assessment.json`. These are
descriptive cross-partition differences, not reproduction errors or calibrated
intervals. The criterion compares C2 with C3; it does not establish C2 as the
largest-weight atom overall. B3's O3 weight is slightly larger than its C2 weight.

| Case | Anion HOMO, Ha | Adjacent occupied gap, Ha | Vertical ionization, Ha | Neutral ⟨S²⟩ |
|---|---:|---:|---:|---:|
| B2 | **+0.052063559** | 0.071944822 | +0.033848478 | 0.760937310 |
| B3 | **+0.058838702** | 0.067648719 | +0.028276392 | 0.760807179 |
| W2 | −0.038651259 | 0.084840294 | +0.035057629 | 0.767682944 |
| W3 | −0.030112920 | 0.086050322 | +0.027693497 | 0.765841173 |

All four neutral-minus-anion vertical energies are positive. Neutral spin
contamination relative to 0.75 is retained, rather than silently replaced with
a pure-doublet value. The occupied frontier is separated in these solutions;
no alternate orbital average was selected after inspection.

**The positive B-family anion HOMOs are a material limitation.** Finite-basis
convergence and a positive total-energy ionization difference do not establish
a stable gas-phase anion or adequate diffuse-electron description. The W-family
HOMOs are negative. Neither family has a separately qualified diffuse-basis,
solvent, metal or protein environment. No rescue calculation changes this result.

The local C2 weight rises by factors **3.02528 / 3.27463**, but the vertical
ionization diagnostic falls by **0.005572086 / 0.007364132 Ha** from state 2 to
3. Thus an increased local carbon-site descriptor does not establish unchanged
electron-transfer chemistry, improved carbon/oxygen discrimination or higher
turnover. Connecting the separate descriptors to gas reaction barriers and
enzyme-state populations requires a new assessed hypothesis. They are not two
independent biological observations or an identified kinetic map.

## Exact realization and authentic custody

The selected EL-owned `rubisco-electronic` lock realizes CPython 3.11.14,
PySCF 2.14.0, NumPy 2.4.6, SciPy 1.17.1, h5py 3.14.0 and Libxc 7.0.0 on
Linux x86-64 CPU. Thread-capable BLAS and PySCF OpenMP pools use two; the
bundled serial OpenBLAS remains at one with threading disabled. Scratch is
explicitly selected. PySCF's empty temporary checkpoint is allowed and counted;
no checkpoint content or retained restart is written.

The pre-SCF runtime retains Libxc composite IDs **402 / 464** and their parsed
descriptions. Their zero explicit hybrid-override tuple is not a zero effective
Hartree–Fock fraction. A separate post-run metadata-only read, with molecule
construction and SCF entry disabled, confirms B3LYPG's 0.2 hybrid coefficient
and WB97X's range-separation tuple `(0.3, 1.0, -0.842294)`; the latter has a
0.157706 short-range and 1.0 long-range fraction. This read observes library
metadata and performs no molecular calculation. It is separate from the
pre-SCF captured fields and does not establish equivalence with absent ORCA
source settings.

The actual packet is
`/tmp/empirical-lawhood-rubisco-20261009/retained-execution/enolate-electronic-v2`.
The existing guarded `ExternalArtifactPlane` publishes six preparation operands before
the first native contact, then a persisted contact, exact log and result for each assigned job,
followed by assessment and closure products: **34 authenticated publications**.
All eight native contacts have one completed result and one convergence marker;
none is retried. This direct native component has **zero recursive task receipts**.
Its fixed roster is not another registered operation.

| Retained identity | SHA-256 |
|---|---|
| Frozen protocol | `e85ad4d2ad9f05aca8e6d573550ba45e82802ff8e49ac0c7fbb50c1572166e84` |
| Producing package | `94cc6a6a2db9b7de7ae3189e920ac86351deff3c906e9e7c80185fdb5a232f36` |
| Dependency lock | `ea491f9e8789d6cd5a18d89908d16ef7db4ee3c9ed4729e32354bc713b135f24` |
| Producing archive | `6345ea9956b26df1e6f343e88af44084996903caff1c6cec963ed2067533eada` |
| Source snapshot | `eb862044b0ad5af2cc9612b721e00ec7f0a48d9a9365469f9f00fd08ef77ce1d` |
| Native runtime | `7fe9a384b0c806a08cb7c6f539022c70f144663f53024e36d64bd0859942da74` |
| Assessment | `a02eb081af8e779b9d47152e5fe382db78e1571162e2014419d647ab15f3297b` |
| Closed census | `99945125b171ec6da559c658896511483d836615689bd9179511d17aa56ba2fd` |

The source archive, SI, accepted manuscript, all selected XYZ members, full
package, lock, protocol and producing helpers are bound before SCF. The archive
has **2,393 members / 33,511,616 bytes**, expanding to 71,484,484 bytes. All
CRC checks and snapshot member hashes pass. The observed dirty checkout remains
at base `9c670a3127cb652f839e56463758226749b07c73`; the producing archive
identifies actual bytes without claiming that a clean HEAD produced them.

Independent retained replay verifies all **171 read-only files / 51,061,400
bytes**, manifests, commit markers, locks and 156 native-file hashes. Recomputing
every full MO metric, density, electron trace, spin value and HOMO population
from retained operands gives maximum residuals respectively **3.741e−13,
2.082e−17, 1.421e−13, 1.421e−14 and 2.776e−16**. The complete primary,
secondary, direction and ionization assessments agree. This review invokes
NumPy arithmetic without PySCF imports or new SCF calls.

## Retained refusals and costs

Three earlier implementation launches stopped before persisted native contact
or molecular calculation. Their complete packets remain unchanged:

| Packet | Cause | Files | Bytes | SCF contacts/jobs |
|---|---|---:|---:|---:|
| `enolate-electronic-v1` | Unsupported raw-source JSON media type | 31 | 33,570,782 | 0 / 0 |
| `enolate-electronic-v1a` | Serial BLAS rejected by an overstrict thread check | 36 | 34,466,496 | 0 / 0 |
| `enolate-electronic-v1b` | Uppercase operational artifact identifier | 41 | 34,514,184 | 0 / 0 |

Their source/producer archives and censuses are authenticated before the v2
native run. They are not excluded outcomes, fresh evidence or failed SCF jobs.
The unchanged eight-job scientific roster first enters SCF in v2. Its selected
packet plus all three refusals totals **153,612,862 bytes**, below the v2
256-MiB aggregate ceiling by **114,822,594 bytes**. This direct allowance does
not change the engine's 128-MiB portable-contribution limit. A future registered
transport must meet its own complete member/ancestry contracts.

The supervisor measures **699.325837 CPU / 319.282016 wall seconds** through
its summary point, with peak RSS **1,077,809,152 bytes** and zero observed/end
scratch bytes. These measurements precede final census hashing, writing and
read-only closure; that tail is not timed. The worker's own measured window is
689.416987 CPU / 315.110779 wall seconds. Known later refusal measurements
remain separate; complete elapsed/CPU costs for the first refusal are unknown,
not zero. Do not claim a fully measured all-development resource total.

The frozen supervisor has a Boolean fixed-point defect at the exact aggregate
storage boundary: its second size loop does not recompute the cap Boolean.
Independent arithmetic confirms the actual result's large margin, so this
defect does not affect its measured storage disposition. Correct it before
future reuse; do not alter the retained producing helper or repeat this run.

The native owner and source/population arithmetic have **43 focused tests**;
the maintained geometry owner has fourteen. Their synthetic analytic oracles
and cold-import checks pass. Software conformance and exact retained numerical
replay support this narrow method result, without supplying reaction kinetics,
mutation-sensitive transport or an EL comparison.

The next substantive task remains the mutation-sensitive joined response:
construct or acquire an applicable coupled environment, identify matched branch
observables, freeze a provisional mapping, and assess both endpoints against
complete exposed mutant controls and strong same-opportunity conventional
methods. Further population-only checks cannot replace that task.
