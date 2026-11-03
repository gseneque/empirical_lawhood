# Prospective Rr coupled MM embedding design

SPDX-License-Identifier: CC-BY-4.0

Reviewed **10 October 2026** on `recchain`. This is an implementable,
source-specific **electrostatic-field proposal**, with exposed software checks;
it is not a frozen scientific protocol, admitted enzyme Hamiltonian, native
execution, optimized state or kinetic prediction. Complete the retained
[six-context initial construction](rr-coupled-initial-geometry-protocol-v1.md)
before selecting native relaxation settings and cost. Its original sources,
proton rules and geometry failures remain unchanged.

## Exact sources and assignment scope

Use the closed [WT-HID91 pre-relaxation Amber dry core](rr-amber-core-source.md),
not the old relaxed coordinates. The source contains **13,828 atoms / 920
residues**, two LSUs truncated to residues 2–459, keto substrate and Mg at
both sites, generated H, and explicit modeled H91 repairs. It contains no
water or counterions and does not establish the assay-parent sequence or a
physical protonation ensemble.

| Source witness | SHA-256 |
|---|---|
| Parent core v1a | `bfbaa57a1b9d466e311c23c37616cd54771ac170d7fc361ef7769a4004040c5f` |
| Closed parent register | `a6deb1386faa51e39669208fecb79a68a859888f60c6fcfaf689cfbc8c1c3ec1` |
| Complete Asn donor projection | `bd35c76940c4a727641a315208ef7cc1895c08184ba00dc7edfb1a80162e635e` |
| Frozen initial construction protocol | `00db4578dc01e1e4f53b978f332e54f04e1c80b27493d7c5e3e24266d7ebcb69` |

Preserve the admitted constructor's real-atom IDs, coordinates, components,
both-chain mutations and physical proton identities. The reference and D263N
construct **neutral HID287 in both chains** from the source's HIE287: former
HE2 is the same nucleus relocated/renamed HD1. H287N constructs complete Asn
in both chains. These are modeled chemical choices, not inherited source
tautomers or experimentally observed mutant structures.

The proposed field rule is:

1. Remove **every real chain-A QM atom** from MM: the full substrate, Mg and
   five side chains. Exclude all five synthetic caps independently. A changed
   or moved atom cannot retain a stale source point charge.
2. Keep the **active-A peptide backbone's parent charge/type witnesses** in
   every genotype, including A263/A287 after side-chain replacement. This is
   a common hybrid boundary approximation, not a complete mutant MM force field.
3. Assign **every atom of a changed chain-B residue**, including its retained
   backbone and CG, from a complete same-chain donor by exact atom name:
   B263→ASN9 for D263N; B287→ASN9 for H287N; B287→HID91 for the reference and
   D263N. Preserve each donor's original charge token, Decimal50, element,
   Amber type/index and mass token. Inherited coordinates remain the admitted
   target coordinates; donor charge assignment does not replace them.
4. Keep all other field atoms and witnesses unchanged. B's keto substrate,
   deprotonated KCX and Mg remain source MM components. Both-chain mutation
   and the B287 tautomer are included; B is not an unmutated spectator.

The donor inventory is available in the same authenticated parent core:
**A9/B9** are complete fourteen-atom ASN, with B9 source indices **7029–7042**;
**A91/B91** are complete seventeen-atom HID, with B91 **8249–8265**. B287's
relocated proton uses the HID91 **HD1 index 8258**, charge **0.3649 e** and
native type **H**. Renaming only HE2 while leaving HIE ring charges/types
would be inconsistent; the whole seventeen-atom assignment is required.
HID91 supplies a parameter witness, not evidence that HID287 is the occupied
enzyme state. The original source and donor atoms are not mutated.

Do not apply the complete ASN donor charge set to active A's backbone. That
would add **+0.146600000548778… e** to A263's external charges alongside its
declared **+1 QM charge**, or **+0.0412 e** for H287N. Reassigning the active
HIE backbone to HID would similarly add **+0.029 e**. Keeping the A backbone
fixed makes the chosen relative-charge comparison explicit.

## Five charge-conserving boundary shifts

For each A191/A193/A194/A263/A287 CA–CB cut, set its **MM-side CA charge to
zero**, and add exactly **q_CA/3** to the same residue's **N, C and HA**.
Retain the CA row, coordinate and identity in the complete field census.
Neither cap H nor real QM CB is a recipient. Verify distinct recipients and
their same-residue/backbone membership before assigning the field.

| A position | CA source index | Original CA q / e | N, C, HA source indices |
|---|---:|---:|---|
| 191 | 2875 | +0.0517 | 2873, 2894, 2876 |
| 193 | 2912 | +0.0381 | 2910, 2920, 2913 |
| 194 | 2924 | +0.0397 | 2922, 2935, 2925 |
| 263 | 3961 | +0.0381 | 3959, 3969, 3962 |
| 287 | 4330 | −0.0581 | 4328, 4343, 4331 |

The exact native charge is the original scaled token divided by **18.2223**.
Use rational arithmetic for assignments/transfers, independently verify the
source **50-digit, ROUND_HALF_EVEN Decimal** representation, and retain the
rounding residual when converting final charges to Decimal50 or binary64.
Three rounded decimal thirds need not sum exactly to the original charge.

This rule conserves **each local MM charge sum**, and therefore the full MM
sum. It does **not** preserve each cut's dipole or original electrostatic
potential. The source audit retains the explicit dipole change
`q_CA × ((r_N+r_C+r_HA)/3 − r_CA)` for every cut. Boundary-rule sensitivity
requires a separate selection; it cannot be tuned to the exposed kinetics.

## Full field and formal-charge bookkeeping

The source core's exact partial-charge sum is
**−29.999996494493011310317577912777201560725045685780609… e**.
The **76 original A-QM atoms** removed from the parent field carry
**−5.492898009076790525894096793489296082272819567233554… e**.
Keep this original exclusion ledger separate from the current mutant's
removed/added real atoms. New A amide atoms are QM; their donor partial
charges are not additional MM points.

| Genotype, each V2/V3 | All MM atom rows | Nonzero MM charges | Exact-derived q_MM / e, rounded here | Declared Q_QM | q_MM + Q_QM / e, rounded here |
|---|---:|---:|---:|---:|---:|
| Reference | 13,752 | 13,747 | −24.507098484867442639 | −6 | −30.507098484867442639 |
| Both-chain D263N | 13,754 | 13,749 | −23.507098482123551912 | −5 | −28.507098482123551912 |
| Both-chain H287N | 13,749 | 13,744 | −24.507098482123551912 | −6 | −30.507098482123551912 |

Within each genotype **V2 and V3 have identical MM fields**: their conserved
H_a/H_b movements occur entirely inside QM. Their field fingerprints must
therefore agree. The three genotype fields differ through the declared B
residue inventories/coordinates and charge assignments, rather than outcome
labels. The QM inventory remains **81/83/78 atoms, 382/382/370 electrons**,
with separately declared singlet hypotheses.

For the source's declared components, 56 ASP and 54 GLU contribute −110;
52 ARG and 34 LYS contribute +86; two KCX contribute −2; two keto RUB
contribute −8; two Mg contribute +4. Explicit H1/H2/H3 N termini add +2,
and the two OXT C termini add −2. This yields the **nominal full formal
charges −30/−28/−30** for reference/D263N/H287N. The active enolate–protonated
KCX pair conserves the keto pair's formal charge. These are conditional
chemical inventory assignments, not measurements of an enzyme microstate.

The capped-QM/native-MM total is **fractional**: its residual against these
nominal full formal charges is approximately **−0.50709849 e** in all three
genotypes. It comes chiefly from replacing peptide partial-charge fragments
with integer-charge capped QM groups; it is not a precision error. Preserve
that approximation without an arbitrary global compensation. Charge
conservation claims concern the **MM boundary transfers**, not exact recovery
of the whole physical system's integer formal charge. The relative hybrid
contrast is approximately **+2 e for D263N / 0 for H287N**, with explicit
native-token rounding differences below **3×10⁻⁹ e**.

## Admission checks and native-use limits

The proposed cold owner derives fields from an exact typed immutable
`RrInitialContextV1`; it accepts no separately supplied output charge table.
Require the complete physical/QM/environment partition, exact source seals,
complete B name/element/donor joins, literal native charge/type witnesses,
five unique cut transfers, finite bounded coordinates, no duplicate field
IDs, no real-QM/cap point-charge duplication and exact rational sum identities.
Retain all CA=0 rows. Report nearest **physical** QM/environment separation
separately from nearest **nonzero-charge** separation: excluding zero charges
does not remove the physical CA atoms or their short cap contacts.

The work uses ordinary development records and a deterministic field SHA;
neither creates a registered scientific-product identity or execution receipt.
The owner is
[rr_coupled_embedding.py](../../../../src/empirical_lawhood/adapters/physical/rubisco_kinetics/rr_coupled_embedding.py),
SHA-256 `4edcd851c019826f0822079c45b28675fdbeee4bb529b26aefd0e26b1267f2ba`;
its [focused checks](../../../../tests/test_rubisco_rr_coupled_embedding.py) have
SHA-256 `bab25c93b14d7a617257e1366662dbbc63df749b9d2ec611cbc05a9eb8fcd6df`.
Both were staged outside the package snapshot at
`/tmp/rubisco-coupled-embedding-work` until the initial six-context retained
packet closed and its independent immutable verification passed. The current
package now has **2,368 source members**; the closed initial construction
keeps its original **2,367**. The existing
[local relaxation feasibility audit](rr-coupled-relaxation-feasibility.md)
identifies installed PySCF/SciPy operations; no dependency change is needed
for this bookkeeping.

A future native protocol must select and freeze basis, functional, numerical
grid/response, SCF/stability checks, point-charge representation, fixed/mobile
chemical roles, constraints, convergence/evaluation limits and full measured
cost. Retain unready/failed geometry and positive-HOMO/confinement problems.
The field has no dielectric, explicit solvent, counterion compensation,
polarization, MM self-energy, van der Waals or verified QM–MM bonded terms.
Native Amber types are provenance for an electrostatic-field assignment,
not a selected complete mechanical force field. Fixed dry outer geometry,
missing waters, substrate/phosphate charge, boundary dipoles and truncated
tails can dominate absolute energies or binding. Constrained electrostatic
repair does not establish a stable proton well, a branch barrier, rate or
coupled turnover/specificity response.

## Retained documentary calculation

Independent source bookkeeping is at
`/tmp/rubisco-coupled-embedding-work/native-charge-proposal-audit-v1.json`,
**28,325 bytes**, SHA-256
`3e0753fb86dba442c5f148790feb6f98869d9cf5381089c353567d694e7c3a71`.
Its stdlib helper is `audit_native_charge_proposal.py`, SHA-256
`5fc265bb696ff22ba584cf2e4bba0385eb276d3d174843533e3692d5563d11dc`.
The JSON binds all inspected input paths/hashes, full donor charge/type rows,
original A-QM exclusion indices, exact rational sums and source cut dipole
changes. The measured read/hash/bookkeeping window was **0.216547115 CPU /
0.216553932 wall seconds**; interpreter startup, prior interactive checks
and final write/hash are unmeasured, not zero. It has **zero constructor,
native, endpoint-fitting or ArtifactPlane calls**. A separate independent
original-core rational check agrees with all sums and shifts. These are
documentary source checks, not a selected embedding realization.

The initial retained construction's prior-software count remains **43**.
Embedding development contributed **18** of those constructor copies: three
six-case fixtures, including an initial seven-pass/one-failure run whose
failure was only an expected-error-message mismatch after correct nonfinite
refusal. The settled staged suite passed **eight checks**; the final
immutable-transfer/cold selection passed **three checks**. Porting the unchanged
owner/tests after initial closure selects **six additional exposed software
copies**, accounted separately from that historical count. All these copies
are standard-library construction/field checks, with zero native engines,
endpoint fits or retained scientific-task receipts; none makes outcomes fresh.
