# SPDX-License-Identifier: MPL-2.0
"""Periodic donor, proton and solvent observations for the gas-free Rubisco precursor."""

import numpy as np

from empirical_lawhood.domains.rubisco.rubisco_response.active_model_preparation import minimum_image
from empirical_lawhood.domains.rubisco.rubisco_response.gp_active_scaffold import proper_rigid_fit
from empirical_lawhood.domains.rubisco.rubisco_response.oxygen_encounter import oxygen_source_roles
from empirical_lawhood.domains.rubisco.rubisco_response.oxygen_source_geometry import prepare_oxygen_source_projection


CUTOFFS = (2.5, 2.7, 3.0)
GROUPS = (
    ("ligand.O2",),
    ("ligand.O3",),
    ("protein.210.OQ1", "protein.210.OQ2"),
    ("protein.212.OD1", "protein.212.OD2"),
    ("protein.213.OE1", "protein.213.OE2"),
)
PROTONS = (
    ("ligand.HC3", "ligand.O2"),
    ("ligand.HO3", "protein.210.OQ2"),
    ("protein.302.HE2", "protein.302.NE2"),
)


def oxygen_motif(original_pdf: bytes, extracted_text: bytes):
    source = prepare_oxygen_source_projection(
        original_pdf_bytes=original_pdf, extracted_text_bytes=extracted_text
    )
    anchors, _ = oxygen_source_roles(source)
    g = source.geometries[0]
    for donor in (g, source.geometries[12]):
        coords = np.asarray([a.coordinate_tokens for a in donor.atoms], dtype=float)
        hydrogens = np.asarray(
            [i for i, a in enumerate(donor.atoms) if a.element == "H"]
        )
        groups = [donor.atoms[j - 1].element for j in (63, 64, 79, 82, 164, 165)]
        nearest = [
            np.min(np.linalg.norm(coords[hydrogens] - coords[j - 1], axis=1))
            for j in (63, 64, 79, 82, 164, 165)
        ]
        if (
            groups != ["O", "O", "N", "N", "O", "O"]
            or min(nearest[:2]) <= 1.25
            or not all(0.8 < d < 1.25 for d in nearest[2:5])
            or nearest[-1] <= 1.25
        ):
            raise ValueError(
                "Published carbamate, histidine or substrate proton assignment changed"
            )
    ids = (anchors[-1], anchors[2], anchors[3], 64, 68, 74, 209, 210, 211)
    atoms = [g.atoms[i - 1] for i in ids]
    if (
        g.ordinal != 1
        or "enediolate" not in g.native_state_label.lower()
        or [a.element for a in atoms] != ["Mg", "O", "O", "O", "O", "O", "O", "H", "H"]
    ):
        raise ValueError("Changed reference precursor")
    pos = np.array([a.coordinate_tokens for a in atoms], dtype=float)
    return pos - pos[0]


def geometry(x, box, spec, waters, owners):
    if x.shape != (spec["atom_count"], 3) or not np.isfinite(x).all():
        raise ValueError("Invalid native coordinates")
    ids = spec["labels"]
    mg = ids["magnesium.MG"]

    def vector(a, b):
        return minimum_image(x[a] - x[b], box)

    def distance(a, b):
        return float(np.linalg.norm(vector(a, b)))

    water_d = np.linalg.norm(vector(waters, mg), axis=1)
    wi = int(np.argmin(water_d))
    near = int(waters[wi])
    donor_ids = [
        min((ids[key] for key in g), key=lambda i: distance(i, mg)) for g in GROUPS
    ]
    donor_ds = [distance(i, mg) for i in donor_ids]
    oh = [distance(near + j, near) for j in (1, 2)]
    hosts = spec.get("proton_hosts", PROTONS)
    hydrogen = [distance(ids[a], ids[b]) for a, b in hosts]
    cc = distance(ids["ligand.C2"], ids["ligand.C3"])
    other_owners = []
    for a, b in hosts:
        hd = np.linalg.norm(vector(owners, ids[a]), axis=1)
        hd[owners == ids[b]] = np.inf
        j = int(np.argmin(hd))
        other_owners.append([int(owners[j]), float(hd[j])])
    chem = all(0.8 < d < 1.25 for d in hydrogen) and 1.15 < cc < 1.53
    water_ok = all(0.75 < d < 1.25 for d in oh)
    longest = max(*donor_ds, float(water_d[wi]))
    observed = dict(
        mg_donors_A=donor_ds,
        donor_native_indices=donor_ids,
        nearest_water_A=float(water_d[wi]),
        tagged_water_A=distance(spec["water"][0], mg),
        nearest_water_native_index=near,
        water_OH_A=oh,
        protons_A=hydrogen,
        other_proton_partners=other_owners,
        C2_C3_A=cc,
        precursor=chem,
        water_intact=water_ok,
        maximum_contact_A=longest,
    )
    hosts_to_compare = ("protein.210.OQ2", "protein.302.ND1", "ligand.O3")
    if all(k in ids for k in hosts_to_compare):
        observed["HO3_host_distances_A"] = {
            k: distance(ids["ligand.HO3"], ids[k]) for k in hosts_to_compare
        }
    if "reference_motif" in spec:
        shape = vector([mg, *donor_ids, near], mg)
        observed["source_shape_RMS_A"] = float(
            proper_rigid_fit(spec["reference_motif"][:7], shape)[2]
        )
        heavy = spec["heavy_native_indices"]
        clearance = np.linalg.norm(vector(heavy, near), axis=1)
        clearance[(heavy == near) | (heavy == mg)] = np.inf
        nearest = int(np.argmin(clearance))
        observed["water_clearance_A"] = float(clearance[nearest])
        observed["water_nearest_heavy_index"] = int(heavy[nearest])
    return observed


def joint(row, cutoff=2.7):
    return (
        row["precursor"] and row["water_intact"] and row["maximum_contact_A"] <= cutoff
    )


def first(values, times, state, after=-1, span=0):
    begin = None
    for i, value in enumerate(values):
        if times[i] <= after:
            continue
        if value != state:
            begin = None
        elif begin is None:
            begin = times[i]
        if begin is not None and times[i] - begin >= span:
            return begin
    return None


def summarize(rows, cutoff):
    ts = [r["time_fs"] for r in rows]
    values = [joint(r, cutoff) for r in rows]
    enter = first(values, ts, True)
    loss = first(values, ts, False, after=enter) if enter is not None else None
    recovered = first(values, ts, True, after=loss) if loss is not None else None
    runs = []
    for t, v in zip(ts, values, strict=True):
        if runs and runs[-1][0] == v:
            runs[-1][2] = t
        else:
            runs.append([v, t, t])
    stable = [v for v, a, b in runs if b - a >= 6]
    stable = [v for i, v in enumerate(stable) if i == 0 or v != stable[i - 1]]
    geo = [r["maximum_contact_A"] <= cutoff for r in rows]
    strict = [
        v
        and all(
            d + 0.1 < alt[1]
            for d, alt in zip(r["protons_A"], r["other_proton_partners"], strict=True)
        )
        for r, v in zip(rows, values, strict=True)
    ]
    result = dict(
        entry=values[0],
        endpoint=values[-1],
        occupied=sum(values[1:]),
        frames=len(values) - 1,
        second_half_occupied=sum(
            v for v, t in zip(values, ts, strict=True) if t > ts[-1] / 2
        ),
        second_half_frames=sum(t > ts[-1] / 2 for t in ts),
        first_entry_fs=enter,
        first_loss_after_entry_fs=loss,
        return_after_loss_fs=recovered,
        sustained_entry_fs=first(values, ts, True, span=6),
        sustained_round_trips=max(0, (len(stable) - 1) // 2),
        longest_joint_span_fs=max((b - a for v, a, b in runs if v), default=0),
        six_contacts_at_entry=geo[0],
        six_contacts_at_endpoint=geo[-1],
        first_six_contact_entry_fs=first(geo, ts, True),
        first_six_contact_exit_fs=first(geo, ts, False),
        geometry_frames=sum(geo[1:]),
        unique_proton_assignment_frames=sum(strict[1:]),
        precursor_frames=sum(r["precursor"] for r in rows[1:]),
        water_intact_frames=sum(r["water_intact"] for r in rows[1:]),
    )
    if "water_clearance_A" in rows[0]:
        shape = [
            v and r["water_clearance_A"] >= 2.4 and r["source_shape_RMS_A"] <= 0.75
            for r, v in zip(rows, values, strict=True)
        ]
        result["shape_and_clearance"] = dict(
            entry=shape[0],
            endpoint=shape[-1],
            occupied=sum(shape[1:]),
            first_entry_fs=first(shape, ts, True),
            sustained_entry_fs=first(shape, ts, True, span=6),
        )
    return result
