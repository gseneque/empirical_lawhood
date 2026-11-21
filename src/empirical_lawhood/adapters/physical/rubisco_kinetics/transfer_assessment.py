# SPDX-License-Identifier: MPL-2.0
"""Read held-out primary assay tables and compare them with frozen predictions."""

import json
from pathlib import Path
import re
from statistics import mean
import tarfile

from empirical_lawhood.domains.rubisco.rubisco_prediction.interface_transfer import (
    ENDPOINTS,
    log_ratio,
    score_forecasts,
)
from .transfer_sources import ALA, DONOR, hashed
from .wilson2017 import _TableParser


def table(raw, locator, doi):
    parser = _TableParser(target_section_id=locator)
    parser.feed(raw.decode("utf-8"))
    parser.close()
    if (
        parser.target_sections != 1
        or parser.target_tables != 1
        or parser.dois != [doi]
        or parser.stack
    ):
        raise ValueError("Primary table identity differs")
    return {
        r.texts[0]: list(r.texts)
        for r in parser.rows
        if r.cells[0].native_tag == "td" and r.texts[0]
    }


def pair(row, parent, col, unit, n):
    def estimate(x):
        match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*±\s*(\d+(?:\.\d+)?)[*,\s]*", x)
        if not match:
            raise ValueError("Unrecognized primary mean and SD: " + x)
        return match.groups()

    m, sm = estimate(row[col])
    p, sp = estimate(parent[col])
    return {
        "mutant": m,
        "parent": p,
        "mutant_SD": sm,
        "parent_SD": sp,
        "reported_biological_n": n,
        "native_tokens": [row[col], parent[col]],
        "unit": unit,
    }


def observations(evidence, archive):
    with tarfile.open(archive) as t:
        raw = t.extractfile(
            "macro/source.003--martin-avila2020-primary-original.html"
        ).read()
    potato = table(raw, "tbl2", "10.1105/tpc.20.00288")
    ala_raw = (evidence / "sources/ala-primary.html").read_bytes()
    hybrid_raw = (evidence / "sources/hybrid-primary.html").read_bytes()
    ala = table(ala_raw, "T2", "10.1074/jbc.M109.044081")
    screen = table(ala_raw, "T1", "10.1074/jbc.M109.044081")
    hybrid = table(hybrid_raw, "T1", "10.1074/jbc.M110.124230")
    result = {}
    for name in ("pS2", "pS3", "pST"):
        mutant = potato["tobpL" + name]
        parent = potato["tobpLpS1"]
        result["potato-" + name] = {
            "study": "potato",
            "role": "intrinsic matched pairs",
            "primary": True,
            "turnover": pair(mutant, parent, 1, "s^-1", "5–6"),
            "specificity": pair(mutant, parent, 4, "mol/mol", "10–11"),
        }
    for name in ALA:
        row = {"study": "alga", "primary": name in ala}
        if name in screen:
            row["Table_I_specificity"] = pair(
                screen[name], screen["Wild-type SS1"], 1, "mol/mol", "3"
            )
            row["Table_I_activity_high_bicarbonate"] = pair(
                screen[name], screen["Wild-type SS1"], 2, "umol CO2/h/mg", "3"
            )
        if name in ala:
            row.update(
                role="Table II specificity and mass-based Vc",
                specificity=pair(ala[name], ala["Wild-type"], 1, "mol/mol", "3"),
                mass_activity=pair(ala[name], ala["Wild-type"], 2, "umol/h/mg", "3"),
            )
        elif name in screen:
            row.update(
                role="Table I supplementary specificity and fixed-condition activity only",
                specificity=row["Table_I_specificity"],
            )
        else:
            row["role"] = (
                "L18A holoenzyme could not be isolated. Both endpoints unavailable."
            )
        result["alga-" + name] = row
    for name, material in (
        ("spinach", "Mutant SSSO"),
        ("arabidopsis", "Mutant SSAT"),
        ("sunflower", "Mutant SSHA"),
    ):
        parent, mutant = hybrid["Chlamydomonas SS1"], hybrid[material]
        result["hybrid-" + name] = {
            "study": "hybrid",
            "role": "Table I specificity and mass-based Vc",
            "primary": True,
            "specificity": pair(mutant, parent, 1, "mol/mol", "3"),
            "mass_activity": pair(mutant, parent, 2, "umol/h/mg", "3"),
        }
    return {
        "potato": hashed(raw),
        "alga": hashed(ala_raw),
        "hybrid": hashed(hybrid_raw),
    }, result


def summarize(scored, obs, methods):
    result = {}
    for study in ("potato", "alga", "hybrid", "all"):
        selected = [
            k for k, v in obs.items() if study in ("all", v["study"]) and v["primary"]
        ]
        by_method = {}
        for method in methods:
            pairs = [scored[k]["methods"][method] for k in selected]
            stats = {}
            for ep in (*ENDPOINTS, "mass_activity"):
                data = [r[ep] for r in pairs if r.get(ep) is not None]
                if data:
                    stats[ep] = {
                        "n": len(data),
                        "MAE": mean(x["absolute_error"] for x in data),
                        "mean_signed_error": mean(x["signed_error"] for x in data),
                        "max_abs_error": max(x["absolute_error"] for x in data),
                        "direction_matches": sum(x["direction_matches"] for x in data),
                        "within_donor_margin": sum(
                            x["within_donor_margin"] for x in data
                        ),
                    }
            both = [r for r in pairs if all(r.get(k) for k in ENDPOINTS)]
            stats["joint"] = {
                "n": len(both),
                "within_both_margins": sum(
                    all(r[k]["within_donor_margin"] for k in ENDPOINTS) for r in both
                ),
                "joint_gain_call_matches": sum(
                    (
                        r["turnover"]["forecast_log_ratio"] > 0
                        and r["specificity"]["forecast_log_ratio"] >= 0
                    )
                    == (
                        r["turnover"]["observed_log_ratio"] > 0
                        and r["specificity"]["observed_log_ratio"] >= 0
                    )
                    for r in both
                ),
            }
            by_method[method] = stats
        result[study] = by_method
    return result


def assess(evidence: Path, archive: Path):
    import numpy as np

    raw = (evidence / "forecast.json").read_bytes()
    freeze = dict(
        line.split()[::-1]
        for line in (evidence / "frozen-inputs.sha256").read_text().splitlines()
    )
    if hashed(raw) != freeze["forecast.json"]:
        raise ValueError("Predictions changed after freezing")
    frozen = json.loads(raw)["result"]
    retained, obs = observations(evidence, archive)
    queries = {
        k: v for k, v in frozen["predictions"].items() if not k.startswith("Gp-")
    }
    margins = [float(log_ratio(*x)) for x in DONOR]
    results = score_forecasts(queries, obs, margins)
    max_diff = 0.0
    training = frozen["training"]
    y = [[float(log_ratio(*r["responses"][ep])) for ep in ENDPOINTS] for r in training]
    tests = frozen["queries"]
    for model, width in (("sequence", 5), ("interface", 10)):
        x = np.array([r["features"][:width] for r in training])
        coef = np.linalg.lstsq(
            np.vstack((x, np.eye(width))),
            np.vstack((y, np.zeros((width, 2)))),
            rcond=None,
        )[0]
        pred = np.asarray([r["features"][:width] for r in tests]) @ coef
        max_diff = max(
            max_diff,
            float(
                np.max(
                    np.abs(
                        pred - [frozen["predictions"][r["id"]][model] for r in tests]
                    )
                )
            ),
        )
    if max_diff > 1e-10:
        raise ValueError("Independent augmented least-squares reconstruction disagrees")
    return {
        "prediction_sha256": hashed(raw),
        "design_sha256": frozen["design_sha256"],
        "assay_sources": retained,
        "observations": obs,
        "scored": results,
        "summary": summarize(results, obs, ("zero", "sequence", "interface")),
        "independent_prediction_max_abs_diff": max_diff,
        "margins": dict(zip(ENDPOINTS, margins, strict=True)),
        "disposition": "UNRESOLVED. No independent red-type matched homologous edit, joint preparation covariance or target-transfer error bound.",
    }
