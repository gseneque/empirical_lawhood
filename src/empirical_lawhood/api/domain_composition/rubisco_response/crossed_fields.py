# SPDX-License-Identifier: MPL-2.0
"""Reconstruct the signed field predictions and independent returns for the original Val1 panel."""

import json
import math
from pathlib import Path

from empirical_lawhood.domains.rubisco.electronic.field_contrast import (
    STATE_SIGNS,
    four_state_field_contrast,
)
from empirical_lawhood.storage.checksum_manifest import selected_checksum_members


def read_crossed_fields(root: Path, *, manifest_sha256: str):
    """Read the sixteen primary cells and any recorded recovery from authenticated original bytes."""
    from empirical_lawhood.adapters.rubisco.rubisco_response.crossing_orbitals import (
        require_orbital_runtime,
    )
    from empirical_lawhood.adapters.rubisco.rubisco_response.field_energy import (
        observed_field_shift,
    )

    with selected_checksum_members(root, manifest_sha256) as (
        roster,
        original,
        consumed,
    ):

        def document(name, *, claimed=None):
            return json.loads(original(name, claimed=claimed))

        def sealed_predictions(folder, states_digest):
            release = document(folder + "/audit-complete.json")
            pin = original(folder + "/prediction.sha256").decode("ascii").strip()
            if release["prediction_sha256"] != pin:
                raise ValueError(
                    "the original field audit refers to another prediction"
                )
            selected = document(folder + "/prospective-predictions.json", claimed=pin)
            if selected["states_sha256"] != states_digest:
                raise ValueError("the field prediction selects another preparation")
            return selected, pin

        field_name = "crossed-fields-01/states.json"
        fields = document(field_name)
        cards = document(
            "prepared-02/states.json", claimed=fields["original_states_sha256"]
        )["states"]
        originals = {c["name"]: c for c in cards}
        fields_by_name = {c["name"]: c for c in fields["states"]}
        names = {
            f"{host}-{water}-{state}"
            for host in ("V1-WT", "V1-I95M")
            for water in ("dry", "wet")
            for state in STATE_SIGNS
        }
        if (
            len(fields["states"]) != len(names)
            or set(fields_by_name) != names
            or len(originals) != len(cards)
        ):
            raise ValueError(
                "the primary field roster must contain every assigned material, hydration and state once"
            )
        main_dir = "crossed-results-01"
        primary, primary_pin = sealed_predictions(main_dir, roster[field_name])
        if (
            set(primary["rows"]) != names
            or primary["worker_sha256"] != roster["measure_gp_edit_fields.py"]
        ):
            raise ValueError(
                "the primary field prediction has another source or state roster"
            )
        original("measure_gp_edit_fields.py", claimed=primary["worker_sha256"])
        for name, card in fields_by_name.items():
            before = originals.get(name)
            if (
                before is None
                or name != f"{card['case']}-{card['hydration']}-{card['state']}"
                or any(
                    card[key] != before[key]
                    for key in (
                        "case",
                        "hydration",
                        "state",
                        "charge",
                        "elements",
                        "xyz_A",
                        "core_labels",
                        "gas_indices",
                        "water_indices",
                        "environment_sha256",
                    )
                )
            ):
                raise ValueError(
                    "the crossed field substitutes the original host coordinates or state"
                )

        # The original prospective CPU calculation selected four threads in its authenticated worker.
        runtime = require_orbital_runtime(4)
        field_inputs = {}

        def reconstruct(name, frozen, output, parent, *, reference_pin=None):
            card = fields_by_name[name]
            kind = "triplet" if card["state"].startswith("O-") else "closed"
            base = f"{parent}/{name}/{name}-pbe0-{kind}"
            rr = document(base + ".json", claimed=reference_pin)
            if (
                rr["id"] != base.split("/")[-1]
                or (
                    rr["case"],
                    rr["hydration"],
                    rr["state"],
                    rr["kind"],
                    rr["basis"],
                    rr["xc"],
                )
                != (
                    card["case"],
                    card["hydration"],
                    card["state"],
                    kind,
                    "def2-svp",
                    "pbe0",
                )
                or rr["density_file"] != base.split("/")[-1] + ".npz"
                or rr["density_sha256"] != frozen["original_density_sha256"]
            ):
                raise ValueError(
                    "native PBE0 reference substituted its original state, basis or density"
                )
            density = original(base + ".npz", claimed=rr["density_sha256"])
            eligible = rr["converged"] is True and rr["verified"] is True
            if (
                eligible != frozen["original_reference_converged"]
                or (rr["E_Eh"] if eligible else None) != frozen["original_energy_Eh"]
            ):
                raise ValueError(
                    "the original reference changed its energy or convergence disposition"
                )
            field = "crossed-fields-01/" + card["crossed_environment"]
            if (
                roster.get(field) != card["crossed_environment_sha256"]
                or roster.get(field) != frozen["field_sha256"]
            ):
                raise ValueError(
                    "field source differs from the signed preparation and prediction"
                )
            if field not in field_inputs:
                field_inputs[field] = original(field)
            row = observed_field_shift(
                card, field_inputs[field], density if eligible else None
            )
            row.update(
                state=card["state"],
                host=card["case"],
                water=card["hydration"],
                original_reference_converged=eligible,
                original_energy_Eh=rr["E_Eh"] if eligible else None,
                original_density_sha256=rr["density_sha256"],
                field_sha256=roster[field],
            )
            directory = output + "/" + name
            if not eligible:
                missing = document(directory + "/missing.json")
                if directory + "/audit.json" in roster:
                    raise ValueError("the missing reference also has a native audit")
                return dict(
                    **row,
                    observed_audit={"status": "MISSING_REFERENCE", "original": missing},
                )
            audit = document(directory + "/audit.json")
            original(directory + "/audit-density.npz", claimed=audit["density_sha256"])
            if (
                audit["state"] != name
                or not math.isfinite(audit["E_Eh"])
                or not math.isclose(
                    audit["E_Eh"] - rr["E_Eh"],
                    audit["shift_Eh"],
                    abs_tol=1e-10,
                    rel_tol=0,
                )
                or audit["prediction_Eh"] != frozen["frozen_density_shift_Eh"]
            ):
                raise ValueError(
                    "the crossed-field audit substituted its reference, shift or frozen prediction"
                )
            return dict(
                **row,
                observed_audit={
                    "status": "CONVERGED" if audit["converged"] else "UNCONVERGED",
                    "shift_Eh": audit["shift_Eh"],
                    "original_sha256": roster[directory + "/audit.json"],
                },
            )

        primary_rows = {
            name: reconstruct(name, primary["rows"][name], main_dir, "results-01")
            for name in sorted(names)
        }

        def contrasts(rows):
            return {
                f"{host}-{water}": four_state_field_contrast(
                    {s: rows[f"{host}-{water}-{s}"] for s in STATE_SIGNS}
                )
                for host in ("V1-WT", "V1-I95M")
                for water in ("dry", "wet")
            }

        recovery = None
        if any(name.startswith("cold-recovery-01/field/") for name in roster):
            entry = document("cold-recovery-01/entered.json")
            update_dir = "cold-recovery-01/field"
            update, update_pin = sealed_predictions(update_dir, roster[field_name])
            correction = update["recovery"]
            name = correction["new_density_for"]
            original(
                "stock-worker-05/measure_gp_edit_fields.py",
                claimed=update["worker_sha256"],
            )
            if (
                name != entry["target"]
                or name not in names
                or primary_rows[name]["original_reference_converged"]
                or update["worker_sha256"]
                != entry["source_sha256"]["measure_gp_edit_fields.py"]
                or correction["original_prediction_sha256"] != primary_pin
                or set(update["rows"]) != names
                or any(update["rows"][n] != primary["rows"][n] for n in names - {name})
                or entry["cold_density_sha256"]
                != update["rows"][name]["original_density_sha256"]
                or entry["initial_missing_sha256"]
                != roster[f"{main_dir}/{name}/missing.json"]
            ):
                raise ValueError(
                    "recovery must preserve the sealed predecessor and select exactly its missing reference"
                )
            updated = reconstruct(
                name,
                update["rows"][name],
                update_dir,
                "direct-results-01",
                reference_pin=entry["cold_reference_sha256"],
            )
            recovery = {
                "original_prediction_sha256": primary_pin,
                "prediction_sha256": update_pin,
                "name": name,
                "state": updated,
                "blocks": contrasts({**primary_rows, name: updated}),
            }
        return {
            "manifest_sha256": manifest_sha256,
            "runtime": runtime,
            "primary_prediction_sha256": primary_pin,
            "primary": primary_rows,
            "blocks": contrasts(primary_rows),
            "recovery": recovery,
            "consumed_members": dict(sorted(consumed.items())),
            "new_scf_evaluations": 0,
            "scope": "Signed one-electron field work at fixed cluster geometry and selected spin. Global electronic minima and enzyme rates remain unmeasured.",
        }
