# SPDX-License-Identifier: MPL-2.0
"""Independently join the four selected startup and geometry returns, including failed trials."""

import json
from pathlib import Path
import time

from empirical_lawhood.adapters.rubisco.rubisco_response.forecast_core import (
    CASES,
    digest,
)
from empirical_lawhood.api.domain_composition.rubisco_response.molprobity_read import (
    COMPONENTS,
    assess_component,
    dimensions,
)
from empirical_lawhood.domains.rubisco.rubisco_prediction.interface_transfer import (
    classify_joint_bounds,
)
from empirical_lawhood.api.domain_composition.rubisco_response.kcx_backbone_read import (
    assess_supplement,
    ramalyze_summary,
)


def read(path):
    return json.loads(path.read_bytes())


def costs(path):
    if not path.exists():
        return None
    raw = path.read_text()

    def get(label):
        return next(
            line.strip().split(": ", 1)[1]
            for line in raw.splitlines()
            if line.strip().startswith(label)
        )

    elapsed = get("Elapsed (wall clock)").split(":")
    return {
        "cpu_s": float(get("User time")) + float(get("System time")),
        "wall_s": sum(float(t) * 60**i for i, t in enumerate(reversed(elapsed))),
        "maximum_RSS_KiB": int(get("Maximum resident set size")),
        "exit": int(get("Exit status")),
    }


def verify_case(root, evidence, name):
    build, sim, check = [
        root / (k + name) for k in ("amber-", "relaxed-", "qualified-")
    ]
    b, s, v = (
        read(build / "built.json"),
        read(sim / "conditioned.json"),
        read(check / "validation.json"),
    )
    exp = read(check / "export.json")
    for parent, key, path in (
        (s, "build_sha256", build / "built.json"),
        (s, "final_sha256", sim / "final.npz"),
        (s, "checkpoint_sha256", sim / "final.chk"),
        (v, "export_sha256", check / "export.json"),
        (exp, "mmcif_sha256", check / "model.cif"),
        (exp, "atom_map_sha256", check / "atom-map.json"),
    ):
        if parent[key] != digest(path):
            raise ValueError(f"Changed original native result {path}")
    if (
        any(record["case"] != name for record in (s, v, b, exp))
        or s["final_sha256"] != exp["final_sha256"]
    ):
        raise ValueError("Validation and force material disagree")
    for filename, commitment in b["files"].items():
        if digest(build / filename) != commitment:
            raise ValueError("Changed original Amber topology, coordinates or deck")
    exact = read(root / f"relaxed-read-{name}.json")
    force = read(evidence / f"independent-force-{name}.json")
    table, meta = read(check / "atom-map.json"), read(check / "components.json")
    if (
        exact["case"] != name
        or force["case"] != name
        or len(exact["final_sites"]) != 8
        or force["particles"] != exp["atom_count"]
        or meta["input_mmcif_sha256"] != exp["mmcif_sha256"]
        or meta["input_atom_map_sha256"] != exp["atom_map_sha256"]
    ):
        raise ValueError(
            "Independent read differs from the submitted exact array or eight-site population"
        )
    idx = dimensions(table)
    native, ramalyze_rows = {}, {}
    for component in COMPONENTS:
        obs = assess_component(
            check,
            component,
            meta["components"][component],
            meta["input_census"],
            table,
            idx,
            ramalyze_rows=ramalyze_rows if component == "ramalyze" else None,
        )
        native[component] = {
            k: v
            for k, v in obs.items()
            if k
            in (
                "status",
                "raw_rows",
                "categories",
                "expected",
                "joined",
                "protected_scope",
                "clashscore",
                "probe_source_nonwater_atoms",
                "detail",
            )
        }
        for key in (
            "outliers",
            "missing_native_keys",
            "additional_organic_heavy_terms",
        ):
            native[component][key] = len(obs.get(key, []))
    summary = ramalyze_summary(table, meta["components"]["ramalyze"], ramalyze_rows)
    extra = assess_supplement(
        table, read(check / "supplement.json"), ramalyze_rows, summary
    )
    return {
        "material": name,
        "disposition": "Finite short conditioned keto-RuBP starting complex; reactive ensemble and kinetics unresolved.",
        "selection_sha256": b.get("selection_sha256"),
        "build": b,
        "condition": s,
        "force_reconstruction": force,
        "independent_read": exact,
        "geometry": native,
        "cctbx_score": meta["cctbx_molprobity_score"],
        "KCX_supplement": extra,
        "validation": v,
        "native_directory": str(root),
        "flexible_minimum": read(sim / "flexible-minimization.json"),
        "thermodynamics": [
            json.loads(line) for line in (sim / "stages.jsonl").read_text().splitlines()
        ],
        "validation_resource": costs(root / f"qualified-{name}.resource"),
        "conditioning_resource": costs(root / f"relaxed-{name}.resource"),
        "native_read_sha256": digest(root / f"relaxed-read-{name}.json"),
        "raw_geometry_sha256": digest(check / "components.json"),
        "supplement_sha256": digest(check / "supplement.json"),
        "peak_force_kJ_mol_nm": exact["peak_force_component_kJ_mol_nm"],
    }


def read_forecast_returns(root: Path, evidence: Path):
    """Join every conditioned material, failure and process receipt in the selected original return."""
    start, cpu = time.monotonic(), time.process_time()
    cases = [verify_case(root, evidence, name) for name in CASES]
    failures = {}
    for p in sorted(root.glob("*")):
        if p.is_dir():
            retained = {
                f.name: read(f)
                for f in p.iterdir()
                if f.name
                in (
                    "build-failure.json",
                    "conditioning-failure.json",
                    "benchmark-stop.json",
                )
            }
            if retained:
                failures[p.name] = retained
    resources = {
        p.stem: costs(p) for p in sorted(root.glob("*.resource")) if p.is_file()
    }
    status = classify_joint_bounds(
        {view: {"turnover": None, "specificity": None} for view in ("M1", "V1")}
    )
    return {
        "schema": "gp-conditional-forecast-native-review/1",
        "four_materials": cases,
        "superseded_or_failed": failures,
        "all_process_resource_receipts": resources,
        "prior_protocol_successes": {
            p.parent.name: read(p) for p in root.glob("condition-*/conditioned.json")
        },
        "native_scope": "Captured carbohydrate is keto-RuBP. Activated enediolate, gas transition-state and productive-commitment ensembles unmeasured.",
        "empirical_transfer_disposition": status,
        "new_paid_compute_USD": "0",
        "review_wall_s": time.monotonic() - start,
        "review_cpu_s": time.process_time() - cpu,
    }
