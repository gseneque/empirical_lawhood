"""Registered SPMe primitives and pure independent scientific reducers.

PyBaMM and NumPy are imported only after exact scientific preflight. No function
in this module executes the whole construction or authenticates custody itself.
"""

from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from importlib.metadata import distribution, version

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import (
    AssessmentDisposition as Disposition, AssessmentPhase, RequirementSupplyAssessment,
    ScientificConditionScope,
)
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest
from empirical_lawhood.kernel.serialization import canonical_json_bytes

from .contracts import (
    BatteryAdmission, BatteryCheckpoint, BatteryCheckpointSummary,
    BatteryFurtherProduct, BatteryOperation, BatteryOperationConfig,
    BatteryProcedureContribution, BatteryRestartAssessment, BatterySourceContract,
    BatteryTrace, BatteryVoltageContrast, OBSERVABLE_CHANNELS, REQUIRED_CHANNELS,
)

D = Decimal
CONTEXT = Context(prec=50, rounding=ROUND_HALF_EVEN)
CLOCKS = tuple(D(t) for t in range(300, 601, 10))


def identity(record):
    for name in ("checkpoint_id", "summary_id", "trace_id", "assessment_id", "procedure_id", "admission_id", "product_id"):
        if hasattr(record, name):
            return ObjectIdentity.from_record(getattr(record, name), record)
    raise ValueError("battery scientific record has no registered identity")


def source_preflight(source: BatterySourceContract):
    """Check installed source bytes without importing the solver or acquiring evidence."""
    for package, expected in (("pybamm", source.pybamm_version), ("casadi", source.casadi_version),
                              ("numpy", source.numpy_version), ("scipy", source.scipy_version)):
        if version(package) != expected:
            raise ValueError(f"battery frozen {package} version differs before contact")
    package = distribution("pybamm")
    for locator, expected in (
        ("pybamm/input/parameters/lithium_ion/Chen2020.py", source.parameter_sha256),
        ("pybamm/models/full_battery_models/lithium_ion/spme.py", source.model_sha256),
        ("pybamm/solvers/casadi_solver.py", source.solver_sha256),
    ):
        if sha256(package.locate_file(locator).read_bytes()).hexdigest() != expected:
            raise ValueError("battery installed source bytes differ before contact")


def _runtime(source, initial_soc, *, tighter=False):
    import pybamm

    model = pybamm.lithium_ion.SPMe(options={"thermal": "isothermal", "cell geometry": "pouch",
                                          "calculate heat source for isothermal models": "true"})
    parameters = pybamm.ParameterValues("Chen2020")
    if D(str(parameters["Nominal cell capacity [A.h]"])) != D(5):
        raise ValueError("installed nominal capacity differs from the frozen 5 Ah operand")
    parameters.update({"Current function [A]": "[input]", "Ambient temperature [K]": "[input]",
                       "Initial temperature [K]": 293.15})
    solver = pybamm.CasadiSolver(
        mode="safe", rtol=float(source.tighter_rtol if tighter else source.coarse_rtol),
        atol=float(source.tighter_atol if tighter else source.coarse_atol),
        extra_options_setup={"max_num_steps": source.integrator_max_steps},
        max_step_decrease_count=source.max_step_decreases, dt_max=600,
    )
    simulation = pybamm.Simulation(model, parameter_values=parameters, solver=solver,
                                  var_pts={name: source.mesh_points for name in ("x_n", "x_s", "x_p", "r_n", "r_p")})
    simulation.build(initial_soc=float(initial_soc), inputs=_inputs(D(0)))
    return pybamm, simulation


def _layout(model):
    entries = tuple(sorted((variable.name, tuple((part.start, part.stop, part.step) for part in slices))
                           for variable, slices in model.y_slices.items()))
    return sha256(canonical_json_bytes(entries)).hexdigest()


def _model_id(model):
    return sha256(canonical_json_bytes((model.name, int(model.len_rhs), int(model.len_alg), _layout(model)))).hexdigest()


def _inputs(current):
    return {"Current function [A]": float(current), "Ambient temperature [K]": 293.15}


def _phase(simulation, start, stop, current, *, starting_solution=None):
    import numpy as np

    return simulation.step(float(stop - start), t_eval=np.arange(0, float(stop - start) + 1, 10),
                           inputs=_inputs(current), starting_solution=starting_solution)


def _prefix(simulation, history, on_phase=None):
    currents = (D(1), D(0)) if history == "early" else (D(0), D(1))
    for start, stop, current in zip((D(0), D(150)), (D(150), D(300)), currents, strict=True):
        if on_phase is not None:
            on_phase()
        _phase(simulation, start, stop, current)
    return simulation.solution


def _state(solution):
    import numpy as np

    value = solution.last_state.all_ys[0]
    if hasattr(value, "full"):
        value = value.full()
    values = np.asarray(value, dtype="<f8").reshape(-1)
    if not len(values) or len(values) > 4096 or not np.isfinite(values).all():
        raise ValueError("native checkpoint state violates the finite f8 census")
    return values


def _scalar(solution, variable, time):
    import numpy as np

    value = float(np.asarray(solution[variable](float(time))).reshape(-1)[0])
    if not np.isfinite(value):
        raise ValueError("native battery quantity is nonfinite")
    return D(str(value))


def capture_checkpoint(config: BatteryOperationConfig):
    if config.operation is not BatteryOperation.CHECKPOINT:
        raise ValueError("checkpoint acquisition received another operation config")
    source_preflight(config.source)
    _, simulation = _runtime(config.source, config.initial_soc)
    solution = _prefix(simulation, config.history)
    if float(solution.t[-1]) < 300 - 1e-8:
        raise ValueError("native prefix terminated before the assigned checkpoint")
    return BatteryCheckpoint(
        f"{config.config_id}.checkpoint", config.source, config.unit_id, config.history, config.initial_soc,
        D(300), _scalar(solution, "Discharge capacity [A.h]", 300),
        _scalar(solution, "Volume-averaged cell temperature [K]", 300),
        D(0) if config.history == "early" else D(1),
        (("Ambient temperature [K]", D("293.15")), ("Current function [A]", D(0) if config.history == "early" else D(1))),
        _layout(simulation.built_model),
        _model_id(simulation.built_model), _state(solution).tobytes().hex(), 2,
    )


def project_checkpoint(checkpoint):
    with localcontext(CONTEXT):
        soc = checkpoint.initial_soc - checkpoint.capacity_Ah / D(5)
    return BatteryCheckpointSummary(
        f"{checkpoint.checkpoint_id}.observable-summary", identity(checkpoint), checkpoint.source,
        checkpoint.unit_id, checkpoint.history, checkpoint.checkpoint_seconds, soc, checkpoint.capacity_Ah,
        checkpoint.temperature_K, checkpoint.state_layout_sha256, checkpoint.model_sha256,
        tuple(sorted((*REQUIRED_CHANNELS, *OBSERVABLE_CHANNELS))),
    )


def checkpoint_preflight(config, checkpoint):
    if checkpoint.source != config.source or checkpoint.unit_id != config.unit_id or checkpoint.history != config.history or checkpoint.initial_soc != config.initial_soc:
        raise ValueError("checkpoint source, assigned instance or history differs before contact")
    with localcontext(CONTEXT):
        if abs(checkpoint.capacity_Ah - D(150) / D(3600)) > D("0.00000001") or abs(checkpoint.temperature_K - D("293.15")) > D("0.00000001"):
            raise ValueError("checkpoint conservation controls differ before contact")


def _future(word):
    currents = {"hold": (0, 0, 0), "early1": (1, 0, 0), "late1": (0, 1, 0), "early3": (3, 0, 0)}[word]
    return tuple(zip((D(300), D(420), D(540)), (D(420), D(540), D(600)), map(D, currents), strict=True))


def expected_capacity(checkpoint_capacity, word, clock):
    with localcontext(CONTEXT):
        return checkpoint_capacity + sum((max(D(0), min(clock, stop) - start) * current / D(3600)
                                          for start, stop, current in _future(word)), D(0))


def _starting(pybamm, checkpoint, state, model):
    # Reuse the installed repository's known restart primitive. The source input
    # applies at the checkpoint; later step inputs supply the declared future.
    from empirical_lawhood.adapters.simulators.pybamm_exact_restart import _starting_solution
    # PyBaMM stacks Solution input dict values; its solver uses alphabetical
    # names. The canonical ledger preserves this required order explicitly.
    return _starting_solution(pybamm, checkpoint_s=300, state=state, model=model,
                              inputs=dict(checkpoint.source_input_ledger))


def continue_checkpoint(config, checkpoint, admission=None):
    if config.operation not in {BatteryOperation.REFERENCE, BatteryOperation.FULL, BatteryOperation.SOC, BatteryOperation.TIGHTER}:
        raise ValueError("native continuation received another registered config")
    checkpoint_preflight(config, checkpoint)
    if config.wave == "B":
        if admission is None or admission.consumer_id != "C1" or admission.supply.disposition is not Disposition.SATISFIED:
            return _empty_trace(config, checkpoint, ("C1_ADMISSION_NOT_SATISFIED",))
        if admission.checkpoint_summary.object_fingerprint != project_checkpoint(checkpoint).fingerprint():
            raise ValueError("admission is bound to another checkpoint before native contact")
        if config.contribution_sha256 != admission.contribution_sha256:
            raise ValueError("continuation changed its committed contribution before native contact")
    elif admission is not None:
        raise ValueError("Wave A cannot receive a later admission")
    source_preflight(config.source)
    tighter = config.operation is BatteryOperation.TIGHTER
    route = config.operation.value
    pybamm, simulation = _runtime(config.source, config.initial_soc, tighter=tighter)
    if _layout(simulation.built_model) != checkpoint.state_layout_sha256 or _model_id(simulation.built_model) != checkpoint.model_sha256:
        raise ValueError("checkpoint layout or model differs before integration")
    phase_calls = 0
    exact = False
    try:
        import numpy as np

        if route == "REFERENCE":
            def entered_prefix_phase():
                nonlocal phase_calls
                phase_calls += 1
            solution = _prefix(simulation, config.history, entered_prefix_phase)
            exact = _state(solution).tobytes().hex() == checkpoint.state_hex
            starting = None
        else:
            if route == "SOC":
                with localcontext(CONTEXT):
                    soc = checkpoint.initial_soc - checkpoint.capacity_Ah / D(5)
                pybamm, simulation = _runtime(config.source, soc)
                state = np.asarray(simulation.built_model.concatenated_initial_conditions.evaluate(inputs=_inputs(checkpoint.source_current_A)), dtype="<f8").reshape(-1)
                capacity_slices = [slices for variable, slices in simulation.built_model.y_slices.items() if variable.name == "Discharge capacity [A.h]"]
                if len(capacity_slices) != 1 or len(capacity_slices[0]) != 1:
                    raise ValueError("SOC capacity state has no unique native bookkeeping coordinate")
                state[capacity_slices[0][0]] = float(checkpoint.capacity_Ah)
            else:
                state = np.frombuffer(bytes.fromhex(checkpoint.state_hex), dtype="<f8").copy()
                exact = state.tobytes().hex() == checkpoint.state_hex
            starting = _starting(pybamm, checkpoint, state, simulation.built_model)
        for start, stop, current in _future(config.future_word):
            phase_calls += 1
            solution = _phase(simulation, start, stop, current, starting_solution=starting)
            starting = None
            if float(solution.t[-1]) < float(stop) - 1e-8:
                return _trace(config, checkpoint, solution, exact, False, ("NATIVE_EARLY_TERMINATION",), phase_calls)
        return _trace(config, checkpoint, solution, exact, True, (), phase_calls)
    except (pybamm.SolverError, RuntimeError, ValueError) as error:
        # Preserve finite data actually returned before a scientific native stop.
        reason = (f"NATIVE_{type(error).__name__.upper()}",)
        solution = simulation.solution
        if solution is not None and hasattr(solution, "t") and len(solution.t) and float(solution.t[-1]) >= 300:
            return _trace(config, checkpoint, solution, exact, False, reason, phase_calls)
        return _empty_trace(config, checkpoint, reason, phase_calls)


def _empty_trace(config, checkpoint, reasons, calls=0):
    return BatteryTrace(f"{config.config_id}.trace", identity(checkpoint), checkpoint.unit_id, checkpoint.history,
                        config.future_word, config.operation.value, "tighter" if config.operation is BatteryOperation.TIGHTER else "coarse",
                        (), (), (), (), False, False, reasons, calls, config.source)


def _trace(config, checkpoint, solution, exact, completed, reasons, calls):
    last = D(str(float(solution.t[-1])))
    retained = []
    for clock in (t for t in CLOCKS if t <= last + D("0.00000001")):
        try:
            values = tuple(_scalar(solution, variable, clock) for variable in
                           ("Terminal voltage [V]", "Discharge capacity [A.h]", "Volume-averaged cell temperature [K]"))
        except ValueError:
            completed = False
            reasons = tuple(sorted(set((*reasons, "NATIVE_INVALID_QUANTITY"))))
            break
        retained.append((clock, values))
    clocks = tuple(t for t, _ in retained)
    channels = tuple(tuple(values[index] for _, values in retained) for index in range(3))
    return BatteryTrace(f"{config.config_id}.trace", identity(checkpoint), checkpoint.unit_id, checkpoint.history,
                        config.future_word, config.operation.value, "tighter" if config.operation is BatteryOperation.TIGHTER else "coarse",
                        clocks, *channels, exact, completed, reasons, calls, config.source)


def _assessment(config, phase, disposition, evidence, reasons):
    return RequirementSupplyAssessment(
        f"{config.config_id}.supply-assessment", ObjectIdentity.from_record(config.requirement.requirement_id, config.requirement),
        ObjectIdentity.from_record(config.connection.connection_id, config.connection), phase, disposition, config.unit_id,
        tuple(sorted((identity(record) for record in evidence), key=lambda value: value.object_id)), tuple(sorted(set(reasons))),
    )


def assess_restart(config, checkpoint, reference, full, soc=None):
    if config.operation is not BatteryOperation.ASSESS:
        raise ValueError("restart reducer received another operation config")
    checkpoint_preflight(config, checkpoint)
    traces = (reference, full) if soc is None else (reference, full, soc)
    expected_routes = ("REFERENCE", "FULL") if soc is None else ("REFERENCE", "FULL", "SOC")
    if any(trace.checkpoint != identity(checkpoint) or trace.unit_id != config.unit_id or trace.history != config.history or trace.future_word != config.future_word or trace.source != config.source or trace.route != route
           for trace, route in zip(traces, expected_routes, strict=True)):
        raise ValueError("restart assessment substituted checkpoint, route, source or future word")
    errors = (None, None, None)
    soc_error = None
    capacity_control = temperature_control = False
    soc_capacity = soc_temperature = None
    reasons = []
    complete = reference.completed and full.completed
    with localcontext(CONTEXT):
        if complete:
            errors = tuple(max(abs(a - b) for a, b in zip(getattr(reference, name)[1:], getattr(full, name)[1:], strict=True))
                           for name in ("voltage_V", "capacity_Ah", "temperature_K"))
            if soc is not None and soc.completed:
                soc_error = max(abs(a - b) for a, b in zip(reference.voltage_V[1:], soc.voltage_V[1:], strict=True))
            capacity_control = all(abs(q - expected_capacity(checkpoint.capacity_Ah, trace.future_word, t)) <= D("0.00000001")
                                   for trace in (reference, full) for t, q in zip(trace.clocks_seconds[1:], trace.capacity_Ah[1:], strict=True))
            temperature_control = all(abs(t - D("293.15")) <= D("0.00000001") for trace in (reference, full) for t in trace.temperature_K)
        if soc is not None and soc.completed:
            soc_capacity = all(abs(q - expected_capacity(checkpoint.capacity_Ah, soc.future_word, t)) <= D("0.00000001")
                               for t, q in zip(soc.clocks_seconds[1:], soc.capacity_Ah[1:], strict=True))
            soc_temperature = all(abs(t - D("293.15")) <= D("0.00000001") for t in soc.temperature_K)
    if not complete:
        disposition = Disposition.UNEVALUABLE
        reasons.append("INCOMPLETE_NATIVE_CONTINUATION")
    else:
        if not full.exact_state_roundtrip:
            reasons.append("EXACT_STATE_ROUNDTRIP_FAILED")
        for error, limit, name in zip(errors, (D("0.000001"), D("0.00000001"), D("0.00000001")), ("VOLTAGE", "CAPACITY", "TEMPERATURE"), strict=True):
            if error > limit:
                reasons.append(f"FULL_RESTART_{name}_DEFECT")
        if not capacity_control:
            reasons.append("CURRENT_INTEGRAL_CONTROL_FAILED")
        if not temperature_control:
            reasons.append("TEMPERATURE_CONSTANCY_CONTROL_FAILED")
        disposition = Disposition.FALSIFIED if reasons else Disposition.SATISFIED
    soc_state = "NOT_ASSIGNED" if soc is None else ("UNEVALUABLE" if soc_error is None or not soc_capacity or not soc_temperature else
                "INADEQUATE" if soc_error > D("0.001") else "ADEQUATE_WITHIN_TESTED_SCOPE")
    supply = _assessment(config, AssessmentPhase.PROCEDURE if config.wave == "A" else AssessmentPhase.INSTANCE,
                         disposition, (checkpoint, *traces), reasons)
    return BatteryRestartAssessment(f"{config.config_id}.restart-assessment", supply, identity(reference), identity(full),
                                    None if soc is None else identity(soc), *errors, soc_error, soc_state,
                                    capacity_control, temperature_control, soc_capacity, soc_temperature)


def construct_procedure(config, checkpoints, assessments):
    if config.operation is not BatteryOperation.PROCEDURE or config.wave != "A":
        raise ValueError("procedure synthesis requires Wave A")
    if len(checkpoints) != 2 or {p.history for p in checkpoints} != {"early", "late"} or len(assessments) != 2:
        raise ValueError("Wave A procedure must retain both assigned histories")
    for checkpoint in checkpoints:
        if checkpoint.source != config.source or checkpoint.unit_id != "battery-preparation-a":
            raise ValueError("procedure changed its preparation or source")
    if len({(p.state_layout_sha256, p.model_sha256) for p in checkpoints}) != 1:
        raise ValueError("procedure histories have incompatible state layouts")
    expected_checkpoint_ids = {identity(p) for p in checkpoints}
    assessed_checkpoints = [expected_checkpoint_ids.intersection(a.supply.evidence) for a in assessments]
    if any(assessment.supply.phase is not AssessmentPhase.PROCEDURE for assessment in assessments) or any(len(values) != 1 for values in assessed_checkpoints) or set.union(*assessed_checkpoints) != expected_checkpoint_ids:
        raise ValueError("procedure assessments do not assess the actual assigned checkpoints")
    states = {a.supply.disposition for a in assessments}
    disposition = (Disposition.SATISFIED if states == {Disposition.SATISFIED} else
                   Disposition.FALSIFIED if Disposition.FALSIFIED in states else Disposition.UNEVALUABLE)
    checkpoint = checkpoints[0]
    scope = ScientificConditionScope(
        "chen2020-spme", "battery-recursive-numerical-world", config.source.source_id,
        ("capacity", "temperature", "voltage"), ("A.h", "K", "V"), "spme-native-terminal", "model-seconds",
        "Known exact-state restart procedure assessed on one exposed preparation with two nested histories; hold future only.",
        source_config_sha256=config.source.fingerprint(), instance_id="battery-preparation-a", valid_from=D(300), valid_until=D(600),
    )
    finding = ("Both assigned hold histories supplied faithful full-state continuations; SOC-only findings retained separately."
               if disposition is Disposition.SATISFIED else "Assigned hold histories did not establish the full-state procedure contract; negative or unevaluable products retained.")
    return BatteryProcedureContribution(f"{config.config_id}.procedure", disposition, scope, config.source,
                                         checkpoint.state_layout_sha256, checkpoint.model_sha256, REQUIRED_CHANNELS, ("hold",),
                                         tuple(sorted((identity(a) for a in assessments), key=lambda v: v.object_id)),
                                         ("changed-future-fidelity", "new-instance-supply"), finding)


def admit_procedure(config, manifest: ContributionManifest, procedure, summary):
    if config.operation not in {BatteryOperation.ADMIT_C1, BatteryOperation.ADMIT_C2} or config.wave != "B":
        raise ValueError("procedure admission requires its registered Wave B consumer")
    if manifest.fingerprint() != config.contribution_sha256:
        raise ValueError("imported scientific contribution differs from committed bytes")
    procedure_identity = identity(procedure)
    if not any(p.record == procedure_identity for p in manifest.products) or tuple(manifest.assessments) != procedure.assessments or manifest.scope != procedure.scope:
        raise ValueError("contribution does not bind the actual procedure and assessment scope")
    if summary.unit_id != config.unit_id or summary.history != config.history or summary.checkpoint_seconds != D(300):
        raise ValueError("admission received another instance or causal cutoff")
    consumer = "C1" if config.operation is BatteryOperation.ADMIT_C1 else "C2"
    permitted = tuple(sorted((*REQUIRED_CHANNELS, *OBSERVABLE_CHANNELS))) if consumer == "C1" else OBSERVABLE_CHANNELS
    reasons = []
    if procedure.disposition is not Disposition.SATISFIED:
        reasons.append("PROCEDURE_NOT_ESTABLISHED")
    if procedure.source != config.source or summary.source != config.source or procedure.state_layout_sha256 != summary.state_layout_sha256 or procedure.model_sha256 != summary.model_sha256:
        reasons.append("SOURCE_OR_LAYOUT_OUTSIDE_PROCEDURE")
    if not set(procedure.required_channels) <= set(permitted):
        reasons.append("REQUIRED_LATENT_CHANNEL_FORBIDDEN")
    if not set(procedure.required_channels) <= set(summary.offered_channels):
        reasons.append("REQUIRED_CHANNEL_NOT_SUPPLIED")
    disposition = Disposition.REFUSED if reasons else Disposition.SATISFIED
    supply = _assessment(config, AssessmentPhase.ADMISSION, disposition, (procedure, summary), reasons)
    return BatteryAdmission(f"{config.config_id}.admission", supply, manifest.fingerprint(), procedure_identity,
                            identity(summary), consumer, permitted)


def import_procedure(config, manifest, procedure):
    """Check the role of already authenticated imported bytes, without freshening them."""
    if config.operation is not BatteryOperation.IMPORT or config.wave != "B" or config.contribution_sha256 != manifest.fingerprint():
        raise ValueError("procedure import differs from its committed contribution")
    if not any(product.record == identity(procedure) for product in manifest.products) or manifest.scope != procedure.scope or manifest.assessments != procedure.assessments:
        raise ValueError("procedure import is missing its exact assessed scientific members")
    return procedure


def _contrast(contrast_id, coarse, tighter, boundary, evaluable):
    if not evaluable or coarse is None or tighter is None:
        finding = "UNEVALUABLE"
    elif coarse > boundary and tighter > boundary:
        finding = "RESOLVED_POSITIVE"
    elif coarse < -boundary and tighter < -boundary:
        finding = "RESOLVED_NEGATIVE"
    else:
        finding = "BOUNDED_NULL_OR_NONDISCRIMINATING"
    return BatteryVoltageContrast(contrast_id, coarse, tighter, boundary, finding)


def assess_voltage(config, c1, c2, traces, assessments):
    if config.operation is not BatteryOperation.VOLTAGE or config.wave != "B":
        raise ValueError("further voltage reducer requires Wave B")
    expected_words = ("early1", "early3", "hold", "late1")
    census = {(trace.future_word, trace.route): trace for trace in traces}
    expected = {(word, route) for word in expected_words for route in ("REFERENCE", "FULL", "TIGHTER")}
    if len(traces) != 12 or set(census) != expected or len(assessments) != 4:
        raise ValueError("further product is missing or duplicates assigned nested controls")
    checkpoint_ids = {trace.checkpoint for trace in traces}
    if len(checkpoint_ids) != 1 or any(trace.unit_id != config.unit_id or trace.history != config.history or trace.source != config.source for trace in traces):
        raise ValueError("further product substituted instance, checkpoint, history or source")
    if c1.consumer_id != "C1" or c2.consumer_id != "C2" or c1.checkpoint_summary != c2.checkpoint_summary:
        raise ValueError("joined assessment changed its shared consumer instance")
    if c1.contribution_sha256 != c2.contribution_sha256:
        raise ValueError("joined consumers imported different scientific contributions")
    if {a.reference for a in assessments} != {identity(census[(w, "REFERENCE")]) for w in expected_words} or {a.full for a in assessments} != {identity(census[(w, "FULL")]) for w in expected_words}:
        raise ValueError("further product substituted actual restart assessments")
    for assessment in assessments:
        words = [word for word in expected_words if identity(census[(word, "REFERENCE")]) == assessment.reference]
        if len(words) != 1 or assessment.full != identity(census[(words[0], "FULL")]):
            raise ValueError("further product crosses assigned restart-assessment histories")
    reasons = []
    complete = all(t.completed for t in traces)
    restarts = all(a.supply.disposition is Disposition.SATISFIED and a.supply.phase is AssessmentPhase.INSTANCE for a in assessments)
    if not complete:
        reasons.append("INCOMPLETE_FORWARD_CENSUS")
    if not restarts:
        reasons.append("INSTANCE_RESTART_NOT_SATISFIED")
    if c1.supply.disposition is not Disposition.SATISFIED:
        reasons.append("C1_ADMISSION_NOT_SATISFIED")
    disagreement = None
    with localcontext(CONTEXT):
        if complete:
            disagreement = max(abs(a - b) for w in expected_words for a, b in zip(census[(w, "FULL")].voltage_V[1:], census[(w, "TIGHTER")].voltage_V[1:], strict=True))
            if disagreement > D("0.0001"):
                reasons.append("FORWARD_NUMERICAL_AGREEMENT_FAILED")
            if any(not t.exact_state_roundtrip for t in traces if t.route in {"FULL", "TIGHTER"}):
                reasons.append("FORWARD_STATE_ROUNDTRIP_FAILED")
            if any(abs(q - expected_capacity(D(150) / D(3600), t.future_word, clock)) > D("0.00000001")
                   for t in traces for clock, q in zip(t.clocks_seconds[1:], t.capacity_Ah[1:], strict=True)):
                reasons.append("FORWARD_CURRENT_INTEGRAL_CONTROL_FAILED")
            if any(abs(value - D("293.15")) > D("0.00000001") for t in traces for value in t.temperature_K):
                reasons.append("FORWARD_TEMPERATURE_CONTROL_FAILED")
        def quantity(route, word, time):
            trace = census[(word, route)]
            if D(time) not in trace.clocks_seconds:
                return None
            return trace.voltage_V[trace.clocks_seconds.index(D(time))]
        values = []
        for route in ("FULL", "TIGHTER"):
            history_values = (quantity(route, "early1", 600), quantity(route, "late1", 600))
            proportional_values = (quantity(route, "early3", 410), quantity(route, "early1", 410), quantity(route, "hold", 410))
            history = None if None in history_values else history_values[0] - history_values[1]
            proportional = None if None in proportional_values else proportional_values[0] - D(3) * proportional_values[1] + D(2) * proportional_values[2]
            values.append((history, proportional))
    evaluable = complete and restarts and not reasons
    contrasts = (
        _contrast("current-proportionality", values[0][1], values[1][1], D("0.0016"), evaluable),
        _contrast("equal-charge-history", values[0][0], values[1][0], D("0.0012"), evaluable),
    )
    c1_state = (Disposition.REFUSED if c1.supply.disposition is not Disposition.SATISFIED else
                Disposition.SATISFIED if evaluable else Disposition.FALSIFIED if complete else Disposition.UNEVALUABLE)
    # A bounded/null scientific finding is still a completed assessed product.
    joint = Disposition.SATISFIED if c1_state is Disposition.SATISFIED and c2.supply.disposition is Disposition.SATISFIED else Disposition.REFUSED
    supply = _assessment(config, AssessmentPhase.JOINED, c1_state, (c1, c2, *traces, *assessments), reasons)
    return BatteryFurtherProduct(f"{config.config_id}.further-product", supply, identity(c1), identity(c2), c1_state, joint,
                                  contrasts, disagreement, (config.unit_id,), expected_words,
                                  tuple(sorted((identity(t) for t in traces), key=lambda v: v.object_id)),
                                  tuple(sorted((identity(a) for a in assessments), key=lambda v: v.object_id)),
                                  sum(t.native_phase_calls for t in traces) + 2, tuple(sorted(reasons)))
