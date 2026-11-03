# Rr complete QM/MM: retained native coupling attempt v4

SPDX-License-Identifier: CC-BY-4.0

Reviewed **10 October 2026** on `recchain`. State:
**DEVELOPMENT_VISIBLE / DEVELOPMENT_ONLY / NON_PROMOTABLE**.

The v4 attempt passed C1 and retained a complete, independently checked
**total coupled C2 finite-difference control**. C3 reserved its first callback
but refused on ten unbound loaded source paths before publishing a native
plan or starting xTB. **Capacity and enzyme source admission, construction and
repair remained unentered.** This synthetic control result supplies no enzyme
geometry, kinetic response, qualification, candidate nomination or consequential
EL capability. Scientific phase gates remain open.

The [frozen v4 protocol](rr-qmmm-native-repair-protocol-v4.md) defines this
attempt. The [v3 result](rr-qmmm-native-coupling-result-v3.md), including its
missing total coupled C2 witnesses, remains unchanged. The separately selected
[v5 protocol](rr-qmmm-native-repair-protocol-v5.md) prospectively authenticates
and reuses completed v4 C1/C2 witnesses and enters only C3 as the next control;
this note reports no v5 native result, capacity result or enzyme outcome.

## Retained source and custody

The immutable execution packet is
`/tmp/empirical-lawhood-rubisco-20261009/retained-execution/rr-qmmm-native-repair-v4`.
The independent read-only witness is `/tmp/rubisco-qmmm-v4-audit`.
The outer resource witness is
`/tmp/rubisco-qmmm-work-v4/outer-resource-v4.txt`. These are exact local external
evidence locators, not shipped public assets.

| Exact retained identity | Bytes | SHA-256 |
|---|---:|---|
| `closed-census.json` | 99,721 | `1837e1a03995ec8b2a52e9bbbd97d466114c743f3fcc0543661eca04764606d8` |
| `sources/frozen-protocol.md` | 17,251 | `34b745062eef868695bc1c072a6c8ec4ee9fa08f00f801aa90e6dcd1df84eb58` |
| Complete producing ZIP, two ordered source chunks | 11,550,746 | `365ca2ac1725a53ab18420b1e15f86536266edae19bec0630830b08f5584283e` |
| `measured-summary.json` | 172,746 | `4762db66cca64481b7bfafa071dea43a038116be78248c51d4c62ecc7eb5ee53` |
| `native-work/worker-report.json` | 163,949 | `c1f9bc3d5db3f8c7346c9e58777505538420d1617c48d20e2c629a56353c1780` |
| Independent `audit-result.json` | 23,579 | `0fb5fc87ebad7949fbf54877ebd213c630c40c673bc38ec5c446e8e11f94265a` |
| Independent `audit.py` | 16,079 | `54954014095706d305448124c128501800991673d70614f6095110815095b4bd` |

The complete denominator is **467 physical files / 52,176,172 bytes**,
including the census, and **53 genuine ArtifactPlane publications**. The
independent audit verifies every physical member's hash, size and read-only
mode, all 28 read-only directories, all actual manifests through
`LocalFilesystemInspector` and `GuardedExternalRoot`, and every member of the
**2,390-member** producing ZIP. It also authenticates the **18 actual C2
input/raw publications**, nine pairs, including original ZIP members,
manifest/commit-marker joins and acknowledgement sidecars. Ordinary JSON
observations retain source-byte custody and acquire no canonical scientific
authority.

The complete C1/C2/C3 stage snapshots under
`native-work/native-controls/stage-observations/` join exactly to both the
control and worker reports:

| Stage snapshot | Bytes | SHA-256 |
|---|---:|---|
| `c1-openmm-reference-lj.json` | 2,002 | `863cacf5ba70b91a269d26b82464c947c7198ff98e3f7851f12c2d859d996e1a` |
| `c2-ethane-coupled-gradient.json` | 31,923 | `2d1a90ebadd7fd8c06933b293128b30e6b5604ae1f8c4f15bf922eb77040e0d4` |
| `c3-ethane-fixed-optimization.json` | 1,994 | `d7ab6cbc088eb7507063cbbe07defa6adfaecb98d079228c5f48608634d77dcd` |

## Completed controls and first refusal

| Assigned stage | Retained outcome |
|---|---|
| C1: neutral two-particle LJ | PASS: one OpenMM Reference Context and three force evaluations; independent analytic energy, force and central finite-difference checks pass. |
| C2: ethane baseline plus eight probes | PASS: nine started, normally waited xTB processes, all exit zero; complete total coupled energies and gradients retained and independently checked. |
| C3: two active H atoms, six fixed atoms | REFUSED: reservation 10 entered the source guard; no native plan publication or process followed. |
| Largest-field capacity control | UNENTERED. Small-field C2 does not establish largest-field capacity. |
| Authentic enzyme admission, construction and repair | UNENTERED. No source admission, reference construction or enzyme objective occurred. |

C1 uses two neutral particles with **σ = 0.3 nm**, **ε = 0.2 kJ/mol** and
**r = 0.4 nm**. Its independent analytic energy is
`−0.1170417308807373046875 kJ/mol`; the retained native value is
`−0.1170417308807373`. The source unit conversion and force/central-difference
check pass the declared bound.

C2 uses the declared synthetic eight-physical-atom ethane model, four real QM
atoms and one generated 1.09 Å link. Its four ordered field sites include two
actual nonzero sites and two exact-zero omissions. Every call retains five
finite QM gradient rows and two finite native field-gradient rows; restoring
the omitted rows preserves the full four-site field order. The baseline total
coupled energy is **−4.175132028506971 Eh**. The baseline field-gradient L2
is **2.8091759532779213e−5 Eh/ASH-Bohr**, exercising a nonzero field derivative.
Native gradients use **0.52917726 Å/Bohr**; ASH uses
**0.5291772109303 Å/Bohr**, with the retained source conversion checked.

The independently recomputed central differences below use all nine retained
**total coupled energies** and the full eight-physical-atom coupled gradients,
with **h = 0.0001 Å**. Raw gradient and input/source joins are checked separately.

| Physical probe | Total coupled FD, Eh/Å | Coupled analytic gradient, Eh/Å | Absolute discrepancy, Eh/Å |
|---|---:|---:|---:|
| C0 x | −0.0013970500001292407 | −0.001397027799588743 | `2.2200540497748986e-8` |
| C1 x | 0.003869016573787576 | 0.0038690181560251335 | `1.582237557553462e-9` |
| H2 y | −0.0005496208377309131 | −0.0005496133655690199 | `7.472161893135737e-9` |
| H5 y | 0.0031073822448490773 | 0.003107378930080153 | `3.314768924188999e-9` |

The maximum **2.2200540497748986e−8 Eh/Å** lies below the frozen
**4e−5 Eh/Å** control criterion. Independent replay authenticates existing
coupled outputs and recomputes their arithmetic; it executes no fresh OpenMM,
ASH or xTB Hamiltonian evaluation. This finite synthetic check does not validate
reactive substrate parameters, the complete enzyme field or biological transport.

C3 has active physical H3/H4 indices **3/4**, fixed indices **0/1/2/5/6/7**,
and only H4 initially stretched by **0.02 Å**. Its callback first reserved
objective 10, then the loaded-profile guard refused these ten exact paths under
`/home/chevre/gs-ml/icf-yolo/.venv/lib/python3.11/site-packages/`:

- `ada92cb5d92a588d1b93__mypyc.cpython-311-x86_64-linux-gnu.so`
- `charset_normalizer/__init__.py`
- `charset_normalizer/api.py`
- `charset_normalizer/cd.cpython-311-x86_64-linux-gnu.so`
- `charset_normalizer/constant.py`
- `charset_normalizer/legacy.py`
- `charset_normalizer/md.cpython-311-x86_64-linux-gnu.so`
- `charset_normalizer/models.py`
- `charset_normalizer/utils.py`
- `charset_normalizer/version.py`

The guard precedes native-plan publication and process creation. There is no
`call-0010.request.json`, call-0010 directory or tenth entered/started native
marker. Actual process audit events, started processes and normally waited
successful processes all total **nine**. The final source-profile failure
leaves later stages `UNENTERED_AFTER_OPERATIONAL_FAILURE`. Reservation 10 stays
charged; it supplies no optimizer convergence, gradient or geometry result.

## Costs, carry and prospective reuse

Complete normally waited worker/descendant CPU is **9.894591 seconds**.
The full outer resource witness records **23.39 CPU / 19.36 wall seconds**
and exit **2**, including caller, worker, descendants and closure. The original
**2400-second monotonic clock** remains unchanged. The approximately
**1329.781335-second** whole-operation elapsed value includes preparation and
prior attempts and differs from this attempt's 19.36-second outer window.

Across v1–v4, exact complete worker CPU is **24.716728 seconds**, carried
conservatively as **25**. Rounded full outer CPU totals **64.76 seconds**;
subtracting the complete workers leaves **40.043272 parent CPU seconds**,
carried as **41**. The original v4 report's literal conservative worker charge
of **24.894591** remains preserved and is distinct from the reconstructed exact
cumulative cost.

The v3/v4 QM/MM attempts carry **19 reserved callbacks / 18 actual started
native processes**: v3 contributes 9/9, v4 contributes 10/9. Thus **21** of the
original 40 control reservations and **125** of the original 144 global
reservations remain. A source refusal consumes its reservation and measured
cost. Neither the wall clock nor native exposure resets for a successor.

The independent audit measured **2.770361 CPU / 1.738984 wall seconds** through
verification, excluding interpreter startup, report serialization and closure
tail. Its first software preflight blocked NumPy required by actual EL manifest
verification and refused; that draft and reason remain retained. The corrected
read-only audit uses the real infrastructure verifier and executes no scientific
source constructor or native calculation.

Completed C1/C2 may be reused only through their exact hash-bound source,
Hamiltonian, inputs, snapshots, original process counters and custody. The
prospective v5 C3 control preserves that model, closes the newly observed source
paths and requires its own actual retained result. Capacity and authentic
reference construction remain subsequent gates. No enzyme or two-endpoint
response capability follows from these completed synthetic controls.
