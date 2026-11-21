# What persists at the Galdieria Rubisco magnesium site after preparation?

SPDX-License-Identifier: CC-BY-4.0

In the gas-free simulations of 20 November 2026, the initially coordinated water
left the first shell in all four matched *Galdieria partita* constructions. A
water initially outside the shell failed to establish the joint precursor in
all four matched outer histories by 60 fs. The preparation therefore still
determined which local structures the simulations sampled. The direction of
the I95M effect on turnover and on CO₂/O₂ specificity remains unresolved for
both small-subunit processing assignments. [Numerical record](gp-precursor-release.json)

## Comparison and observations

The material was the activated L₈S₈ assembly, with one construction for each
combination of WT or I95M and a Met1 or Val1 start. Each mutant construction
contained the edit in all eight small subunits. The readout followed one active
site per assembly. Each inner/outer pair shared its underlying construction
and velocity draw. The repeated 2 fs observations are nested within those paths.

The test required the substrate and donor proton assignments, an intact water
and six Mg contacts within 2.7 Å. The stricter geometry check also required
2.40 Å water clearance and a seven-centre fitted RMS displacement of at most
0.75 Å. With the proton initially on the carbamate, the selected proton
assignment was lost within 4–6 fs in the returned direct-release trajectories.
With the proton assigned to His302, the substrate and donor chemistry persisted
at all 240 postrelease observations in the eight electronic-control paths.

| Construction | First loss from the inner start | Inner observations meeting the 2.7 Å joint criterion | With clearance and shape | Outer observations meeting the joint criterion |
| --- | ---: | ---: | ---: | ---: |
| Val1 WT | 34 fs | 16/30 | 12/30 | 0/30 |
| Val1 I95M | 28 fs | 13/30 | 13/30 | 0/30 |
| Met1 WT | 32 fs | 15/30 | 15/30 | 0/30 |
| Met1 I95M | 34 fs | 16/30 | 16/30 | 0/30 |

The mutant lost the water earlier for Val1 and later for Met1 in these
constructions. Each inner start had one outward transition, with zero observed
returns. The biological population fraction remains compatible with the full
interval from zero to one for each material. At fixed Met1 I95M inner nuclei,
changing only the electronic iteration limit changed the reported energy by
2,218.1185 kcal/mol. The proton potential and the relative frequencies of
exchanging preparations still need independent evidence. The downstream
US$100 gas calculation remains on hold.

## Denominators, costs and custody

The full campaign recorded 132 native calls, 100 wrapper successes and 32
wrapper failures. Of 72 launches on the five main release rosters, 57 reached
their assigned horizons. The other 15 returned finite prefixes, including
zero-frame cases. Ten continuations reused their original paths. Sixteen
launcher attempts and one rejected geometry ended before native entry.

The native calls used 10.34053 CPU-hours and US$0 in new remote rental. Twelve
metered preparations consumed 161.23 additional CPU-seconds and six metered
readers consumed 69.81 CPU-seconds. Two earlier reads have wall-time
measurements only. Electricity, labour and installation costs were unpriced.
The equal-reliability cost reduction and the biological kinetic ratio remain
unmeasured.

The public data file includes time zero and all 30 later observations on every
60 fs path, original restart and trajectory digests, and the cost-ledger
identities. Select positive times, the intact-water and precursor flags, and
the maximum Mg contact to reproduce the primary table. The immutable original
study is `gp-coupled-release-20261120`. Its `campaign-summary.json` has SHA-256
`50cc71f1bb8a2d89f84023177988b054b95cce9cf7f8847218defb433e5bb029`.
The original eight-path readout has SHA-256
`fcf812d3c69764f5568b623125ee680612c09111ff84bde3a0b34dfae2dcb148`.
The primary molecular arrays remain in the study's original custody. [Frame data and source digests](gp-precursor-release.json)
