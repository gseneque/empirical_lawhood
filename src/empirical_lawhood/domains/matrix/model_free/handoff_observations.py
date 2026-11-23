# SPDX-License-Identifier: MPL-2.0
"""Read structural and passage observations at the same recorded policy checkpoint."""

from decimal import Decimal

from .records import Product


def paired_policy_handoffs(specification, products):
    """Read each assigned M7 clock against its original M1 supplier."""
    settings = specification.settings
    if "handoff_clocks" not in settings.get("receiver_study", {}).get("M7", {}):
        return {}
    from .receiver_equilibrium_events import case_ids

    assigned = case_ids(settings, "M7")
    formation = settings["formation"]
    step = Decimal(str(settings["native"]["timestep"]))
    definition = specification.identity
    roots = set(specification.assignments)
    acquired = {}
    for product in products:
        config = product.config
        if config.phase != "acquire" or config.module not in ("M1", "M7"):
            continue
        (root,) = config.assignments
        key = config.module, root
        if (
            root not in roots
            or key in acquired
            or config.specification != definition
            or config.settings_json != specification.settings_json
        ):
            raise ValueError("Duplicate or foreign native policy acquisition")
        acquired[key] = product
    output = {}
    for root in specification.assignments:
        if "M7" in root.modules:
            structural = acquired.get(("M1", root))
            passage = acquired.get(("M7", root))
            output[root.unit_id] = (
                None
                if structural is None or passage is None
                else _root_handoffs(structural, passage, assigned, formation, step)
            )
    return output


def _verify_first_trigger(samples, tick, formation):
    deadline = formation["trigger_deadline"]
    cutoff = deadline if tick is None else tick
    if cutoff > deadline or any(
        t not in samples for t in range(0, cutoff + 1, formation["observation_stride"])
    ):
        raise ValueError("The causal clock lacks its observation grid through decision")
    first = start = None
    for time, admitted in sorted(samples.items()):
        if time > cutoff:
            break
        if admitted is not True:
            start = None
            continue
        if start is None:
            start = time
        if time - start >= formation["trailing_ticks"]:
            first = time
            break
    if first != tick:
        raise ValueError("The causal clock must take the first trailing admission window")


def _root_handoffs(structural: Product, passage: Product, assigned, formation, step):
    width = formation["trailing_ticks"]
    stride = formation["observation_stride"]
    if passage.dependencies != (structural.identity,):
        raise ValueError(
            "The passage must consume the same root's structural acquisition"
        )
    sources = structural.metadata["cases"]
    outcomes = passage.metadata["cases"]
    preparations = {case["case_id"]: case for case in sources}
    events = {case["case_id"]: case for case in outcomes}
    if (
        len(preparations) != len(sources)
        or len(events) != len(outcomes)
        or set(events) != set(assigned)
    ):
        raise ValueError("The native policy handoff census changed")
    observations = {
        case["case_id"]: {
            sample["tick"]: sample["present"] for sample in case.get("observations", ())
        }
        for case in sources
    }
    rows = {}
    for slot in assigned:
        case_id, clock = slot.rsplit(".", 1)
        event = events[slot]
        if case_id not in preparations:
            raise ValueError("An assigned M7 case lacks its M1 preparation")
        checkpoint = preparations[case_id].get("checkpoints", {}).get(clock) or {}
        state = checkpoint.get("state")
        previous = checkpoint.get("incoming_state")
        tick = checkpoint.get("tick")
        state_id = None if state is None else state["sha256"]
        status = event.get("entry_status", "UNKNOWN")
        observed = "handoff_checkpoint_sha256" in event
        if observed and (
            event["handoff_clock"],
            event["handoff_tick"],
            event["handoff_checkpoint_sha256"],
        ) != (clock, tick, state_id):
            raise ValueError(
                "The passage used another structural handoff or physical clock"
            )
        if (state is not None and state["step_index"] != tick) or (
            previous is not None
            and (state is None or previous["step_index"] + 1 != tick)
        ):
            raise ValueError(
                "The structural state and its preceding sample must share the assigned physical clock"
            )
        if (
            (not observed and status != "UNKNOWN")
            or (state is None and status not in ("UNKNOWN", "NO_HANDOFF"))
            or (status == "NO_HANDOFF" and state is not None)
        ):
            raise ValueError(
                "An observed entry requires the original structural checkpoint"
            )
        window = [tick - width, tick] if state is not None and tick >= width else None
        ticks = range(window[0], tick + 1, stride) if window else ()
        samples = observations[case_id]
        complete_window = bool(window) and all(t in samples for t in ticks)
        if (
            state is not None
            and clock == "triggered"
            and (not complete_window or not all(samples[t] is True for t in ticks))
        ):
            raise ValueError(
                "The causal handoff lacks its observed trailing admission window"
            )
        if clock == "triggered" and (state is not None or status == "NO_HANDOFF"):
            _verify_first_trigger(samples, tick, formation)
        wait = (
            event.get("wait_ticks")
            if status in ("ENTERED", "NO_INTERIOR_BEFORE_DEADLINE")
            else None
        )
        rows[slot] = {
            "entry_status": status,
            "handoff_observed_by_both": observed and state is not None,
            "handoff_tick": tick,
            "handoff_time": None if tick is None else str(step * tick),
            "handoff_checkpoint_sha256": state_id,
            "preceding_checkpoint_sha256": None
            if previous is None
            else previous["sha256"],
            "preceding_sample_tick": None
            if previous is None
            else previous["step_index"],
            "trailing_window_ticks": window,
            "trailing_window_observed": complete_window,
            "observed_admission_streak_start": checkpoint.get("trailing_start"),
            "entry_search_ticks": wait,
            "entry_search_time": None if wait is None else str(step * wait),
            "entry_tick": tick + wait if status == "ENTERED" else None,
            "entry_checkpoint_sha256": event.get("entry_checkpoint_sha256"),
        }
    return rows
