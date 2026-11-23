# SPDX-License-Identifier: MPL-2.0
"""Paired structural service and passage on all assigned physical handoffs."""

from collections import Counter, defaultdict
from hashlib import sha256

from .records import json_text
from .science import synthesise_roots


def _entry_errors(event, root_seed):
    if event["entry_status"] != "ENTERED":
        return None
    seal = event["entry_forecast"]
    cue = seal["operand"]
    if sha256(json_text(cue).encode()).hexdigest() != seal["sha256"] or (
        cue["root"],
        cue["entry_checkpoint_sha256"],
        cue["handoff_checkpoint_sha256"],
    ) != (root_seed, event["entry_checkpoint_sha256"], event["handoff_checkpoint_sha256"]):
        raise ValueError("Entry forecast differs from its original root or physical checkpoints")
    futures = [p["h1_dwell"] for p in event["futures"]]
    if len({p["replica"] for p in futures}) != len(futures) or any(
        p["replica"] not in range(4) for p in futures
    ):
        raise ValueError("Duplicated or foreign nested future")
    observed = [p["event"] == "target" for p in futures if p["status"] not in ("failed", "truncated")]
    scores = {}
    for name, sign in (
        ("visible", cue["visible_sign"]),
        ("incoming", cue["last_entry_increment"]),
        ("constant", False),
    ):
        if sign is None:
            scores[name] = [0, 4]
        else:
            wrong = sum(target != sign for target in observed)
            scores[name] = [wrong, wrong + 4 - len(observed)]
    return {"signs": [cue["visible_sign"], cue["last_entry_increment"]], "wrong_futures": scores}


def replay_handoffs(definition, assigned, original, handoffs):
    roots = [r["unit_id"] for r in assigned]
    seeds = [r["seed"] for r in assigned]
    if (
        len(roots) != 128
        or len(set(roots)) != 128
        or seeds != sorted(r["seed"] for r in definition["roots"])
        or len(set(seeds)) != 128
        or set(roots) != set(handoffs["roots"])
    ):
        raise ValueError("Frozen assignment, sibling handoffs and assessed population differ")
    population = {}
    for module in ("M1", "M7"):
        observations = [r["modules"][module]["payload"] for r in assigned]
        if any(
            (p["module"], p["seed"]) != (module, seed) for p, seed in zip(observations, seeds, strict=True)
        ):
            raise ValueError("Root analysis supplied under the wrong module or seed")
        population[module] = synthesise_roots(definition["settings"], observations)["modules"][module]
        prior = original["population_summaries"][module]["result"]["modules"][module]
        check = dict(population[module])
        if module == "M7":
            # This same-entry descriptive baseline was added after the issued assessment.
            check["entry_and_passage"] = [
                {k: v for k, v in slot.items() if k != "same_entry_forecast_reference"}
                for slot in check["entry_and_passage"]
            ]
            old_scope = "AFTER_PAID_M1_FIXED_HANDOFF_INCLUDES_ALL_COMPLETED_WAIT_PREFIXES"
            new_scope = "AFTER_PAID_M1_ASSIGNED_HANDOFF_INCLUDES_ALL_COMPLETED_WAIT_PREFIXES"
            for previous, current in zip(prior["entry_and_passage"], check["entry_and_passage"], strict=True):
                if previous["entry_wait_scope"] == old_scope and current["entry_wait_scope"] == new_scope:
                    current["entry_wait_scope"] = old_scope
        if check != prior:
            raise ValueError(
                f"Recomputed {module} population differs from the original scientific assessment"
            )
    census, pairs, reported = defaultdict(Counter), defaultdict(Counter), []
    for root in assigned:
        rows = {}
        structural = {c["case_id"]: c for c in root["modules"]["M1"]["payload"]["cases"]}
        events = {c["case_id"]: c for c in root["modules"]["M7"]["payload"]["cases"]}
        siblings = handoffs["roots"][root["unit_id"]]
        if len(events) != 12 or set(events) != set(siblings):
            raise ValueError("A physical root requires all twelve sibling clock and recipe slots")
        for slot, event in events.items():
            case, clock = slot.rsplit(".", 1)
            measured = structural[case].get("handoffs", {}).get(clock, {})
            delivered = None if measured.get("unknown", True) else measured["delivery"]
            sibling = siblings[slot]
            if sibling["entry_status"] != event["entry_status"] or sibling["handoff_tick"] != measured.get(
                "tick"
            ):
                raise ValueError("Physical entry or observed sibling handoff clock differs")
            errors = _entry_errors(event, root["seed"])
            counts = census[slot]
            counts["assigned"] += 1
            counts["unknown_service"] += delivered is None
            counts["delivered"] += delivered is True
            counts[event["entry_status"]] += 1
            target = sum(p["h1_dwell"]["event"] == "target" for p in event.get("futures", ()))
            counts["target_futures"] += target
            if errors:
                for label, (low, high) in errors["wrong_futures"].items():
                    counts[label + "_wrong_lower"] += low
                    counts[label + "_wrong_upper"] += high
                counts["incoming_calls_competing"] += errors["signs"][1] is False
            rows[slot] = {
                "structural_delivery": delivered,
                "entry": event["entry_status"],
                "target_futures": target,
                "handoff_tick": sibling["handoff_tick"],
                "checkpoint": sibling["handoff_checkpoint_sha256"],
                "forecast_scores": errors,
            }
        for case in structural:
            after = rows[case + ".triggered"]["structural_delivery"]
            for clock in ("fixed", "yoked"):
                before = rows[case + "." + clock]["structural_delivery"]
                category = (
                    "unknown"
                    if None in (before, after)
                    else {
                        (True, True): "both",
                        (False, False): "neither",
                        (False, True): "gain",
                        (True, False): "harm",
                    }[before, after]
                )
                pairs[case + ".triggered_vs_" + clock][category] += 1
        reported.append({"root": root["unit_id"], "seed": root["seed"], "slots": rows})
    return {"population": population, "paired_structural_delivery": pairs, "slots": census, "roots": reported}
