# SPDX-License-Identifier: MPL-2.0
"""PURE admission and terminal objective reductions for selected real models."""

from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
import math
import json
from pathlib import Path
import struct
import xml.etree.ElementTree as ET

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_contracts import DurablePreparationPlan
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.status import OperationalStatus

from . import control_contracts as c
from . import science

REQUIRED_ASSET_NAMES = frozenset(("model.prmtop", "model.inpcrd", "complete-heavy.pdb",
    "atom-origin-provenance.json", "complete-assigned-parameters.json"))


class UnsupportedNativeXML(ValueError):
    """Complete retained bytes whose actual serializer shape is not supported."""


def _fraction_decimal(value):
    return Decimal(value.numerator)/Decimal(value.denominator)


def _square_root(value):
    # Binary64 exact squares have finite power-of-two denominators. Precision
    # follows their actual representation; this is no scientific-data ceiling.
    with localcontext() as context:
        context.prec = max(80,value.denominator.bit_length()*30103//100000+40)
        return _fraction_decimal(value).sqrt()


def validate_operands(plan, source, preparation, integrity, geometry, assets, custody):
    """Require exact independent selected admission, not a producer's broad positive.

    Custody rows carry original canonical records and their authenticated artifact
    identities: (unit, definition, completion identity, completion, return identity,
    return). The actual caller verifies original manifests/receipts before supplying
    these bytes. This PURE function creates no contact or execution authority.
    """
    for record in (plan, source, preparation, integrity, geometry, *assets):
        record.__post_init__()
    if (plan.source, plan.preparation, plan.assignment_integrity, plan.mathematical_geometry) != tuple(
            p.identity(record) for record in (source, preparation, integrity, geometry)):
        raise ValueError("control substitutes independently assessed source/preparation")
    if ((preparation.source, preparation.structural_inventory, preparation.structural_coordinates,
            preparation.nomination) != (p.identity(source), source.structural_inventory,
            source.structural_coordinates, source.nomination)
            or (integrity.source, integrity.preparation) != (plan.source, plan.preparation)
            or (geometry.source, geometry.preparation, geometry.assignment_integrity) != (
                plan.source, plan.preparation, plan.assignment_integrity)):
        raise ValueError("control changes original source or independent assessment joins")
    selected = tuple((c.model_id((row.construct_id, row.joint_view_id, row.parameter_view)), p.identity(row))
        for row in assets)
    if selected != plan.selected_assets or tuple(row[0] for row in custody) != tuple(name for name, _ in selected):
        raise ValueError("control changes its explicit genuine selected subset or custody")
    models = {row.model_id:row for row in preparation.models}
    assignments = {row[0]:row[1] for row in integrity.model_dispositions}
    diagnostics = {row.model_id:row for row in geometry.models}
    actual_custody = []
    for (name, asset_identity), asset, row in zip(selected, assets, custody, strict=True):
        _, definition, completion_identity, completion, return_identity, returned = row
        for record in (definition, completion, returned):
            record.__post_init__()
        for identity, record in ((completion_identity, completion), (return_identity, returned)):
            if type(identity) is not ObjectIdentity or ObjectIdentity.from_record(identity.object_id, record) != identity:
                raise ValueError("control substitutes original canonical completion/return bytes")
        if (definition.subwork_id != name or definition.operation_id != "rubisco.durable-preparation.unit"
                or definition.configuration.object_schema != DurablePreparationPlan.SCHEMA
                or plan.source not in definition.sources
                or completion.definition != definition.identity
                or completion.operational_status is not OperationalStatus.SUCCEEDED
                or completion.omitted_output_ids or completion.unknown_streams
                or completion.output_ids != tuple(sorted(output.output_id for output in definition.outputs))
                or returned.unit_id != name or returned.plan != definition.configuration
                or not returned.known_return or not returned.preparation_succeeded or returned.error_text is not None):
            raise ValueError("control needs authentic complete successful original preparation custody")
        model, diagnostic = models[name], diagnostics[name]
        if (asset.source != plan.source or model.assets != asset_identity or model.disposition is not A.SATISFIED
                or assignments[name] is not A.SATISFIED
                or diagnostic.assets != asset_identity or diagnostic.assignment_disposition is not A.SATISFIED
                or diagnostic.diagnostic_disposition is not A.SATISFIED or diagnostic.diagnostic is None):
            raise ValueError("selected model lacks independent assignment and hard mathematical geometry admission")
        names = tuple(row.evidence.relative_path.rsplit("/",1)[-1] for row in asset.files)
        if (len(set(names)) != len(names) or not REQUIRED_ASSET_NAMES.issubset(names)
                or any(row.evidence.byte_count <= 0 or row.evidence not in returned.files
                       or row.evidence not in model.files for row in asset.files)):
            raise ValueError("selected model omits genuine full original prepared assets")
        actual_custody.append((name, definition.identity, completion_identity, return_identity))
    if tuple(actual_custody) != plan.preparation_custody:
        raise ValueError("control relabels original independent model custody")
    return plan


def _finite_binary64(value):
    import numpy as np
    original = np.asarray(value)
    if original.dtype.kind != "f" or original.dtype.itemsize != 8:
        raise ValueError("native receiver needs actual binary64 real arrays; no silent conversion")
    if not np.isfinite(original).all():
        raise ValueError("native receiver omits complete finite native arrays")
    return original


def _same_binary64_bits(left, right):
    """Normalize byte order/layout, preserving every finite binary64 bit."""
    import numpy as np
    left,right = _finite_binary64(left),_finite_binary64(right)
    return left.shape == right.shape and np.array_equal(
        np.ascontiguousarray(left,dtype="<f8").view("<u8"),
        np.ascontiguousarray(right,dtype="<f8").view("<u8"))


def terminal_objective_reduction(x, gradient, final_positions, constraints, *, atom_count,
                                 constraint_tolerance):
    """Recompute terminal objective norm per particle and every System constraint.

    x is the native minimizer objective point, not a force-field surrogate. A
    last callback that does not describe the final Context cannot establish final
    convergence. Missing terminal data is handled as UNEVALUABLE by the caller.
    """
    point,grad,final = (_finite_binary64(value) for value in (x,gradient,final_positions))
    if (type(atom_count) is not int or atom_count <= 0 or point.shape != (3*atom_count,)
            or grad.shape != point.shape or final.shape != (atom_count,3)):
        raise ValueError("terminal objective omits complete finite native arrays")
    joined = _same_binary64_bits(point.reshape(atom_count,3), final)
    squared_gradient = Fraction(0)
    for value in grad:
        actual = Fraction.from_float(float(value))
        squared_gradient += actual*actual
    # The selected installed OpenMM source scales minimizer tolerance using
    # numParticles, not 3*numParticles. The independent numerical gate uses
    # ||g||/sqrt(N) over all 3N components. This is no claim about unexposed
    # internal L-BFGS termination or a gradient after native constraint projection.
    rms = _square_root(squared_gradient/atom_count)
    errors = []
    constraints_met = True
    seen = set()
    for left, right, distance in constraints:
        if (type(left) is not int or type(right) is not int or not 0 <= left < atom_count
                or not 0 <= right < atom_count or left == right or tuple(sorted((left,right))) in seen):
            raise ValueError("terminal constraint census duplicates/substitutes native particles")
        seen.add(tuple(sorted((left,right))))
        distance = Decimal(str(distance))
        if not distance.is_finite() or distance <= 0:
            raise ValueError("terminal constraint omits a finite positive native distance")
        exact_squared = sum(((Fraction.from_float(float(final[left,axis]))
            -Fraction.from_float(float(final[right,axis])))**2 for axis in range(3)),Fraction(0))
        d,tol = Fraction(distance),Fraction(constraint_tolerance)
        if not 0 < tol < 1:
            raise ValueError("terminal constraint gate requires an explicit positive relative precision")
        constraints_met = constraints_met and (d*(1-tol))**2 <= exact_squared <= (d*(1+tol))**2
        with localcontext() as context:
            context.prec = max(80,exact_squared.denominator.bit_length()*30103//100000+40)
            actual = _square_root(exact_squared)
            errors.append(abs(actual-distance)/distance)
    maximum = max(errors, default=Decimal(0))
    if not joined:
        return rms, maximum, A.UNEVALUABLE, ("FINAL_CONTEXT_DIFFERS_FROM_TERMINAL_OBJECTIVE_POINT",)
    if squared_gradient > atom_count*Fraction(Decimal("10"))**2 or not constraints_met:
        return rms, maximum, A.REFUSED, ("DECLARED_OBJECTIVE_OR_CONSTRAINT_PRECISION_FAILED",)
    return rms, maximum, A.SATISFIED, ()


def state_geometry_from_xml(raw):
    """Read full actual OpenMM State positions/box in its nanometer convention."""
    import numpy as np
    root = ET.fromstring(raw)
    positions, box = root.find("Positions"), root.find("PeriodicBoxVectors")
    if (root.tag != "State" or root.get("type") != "State" or root.get("version") != "1"
            or positions is None or box is None or tuple(row.tag for row in box) != ("A","B","C")
            or any(row.tag != "Position" for row in positions)
            or any(row.get(axis) is None for row in (*positions,*box) for axis in ("x","y","z"))):
        raise UnsupportedNativeXML("unsupported/incomplete actual full relaxed State XML")
    point = np.asarray([[float(row.get(axis)) for axis in ("x","y","z")] for row in positions],dtype=np.float64)
    vectors = np.asarray([[float(row.get(axis)) for axis in ("x","y","z")] for row in box],dtype=np.float64)
    if not np.isfinite(point).all() or not np.isfinite(vectors).all():
        raise ValueError("actual relaxed State contains nonfinite geometry")
    return point,vectors


def constraints_from_system_xml(raw):
    """Complete actual System constraints, without trusting a producer's subset."""
    root = ET.fromstring(raw)
    particles, constraints = root.find("Particles"), root.find("Constraints")
    if (root.tag != "System" or root.get("type") != "System" or root.get("version") != "1"
            or particles is None or constraints is None or any(row.tag != "Particle" for row in particles)
            or any(row.tag != "Constraint" for row in constraints)
            or any(row.get(key) is None for row in constraints for key in ("p1","p2","d"))):
        raise UnsupportedNativeXML("unsupported/incomplete actual System XML constraint census")
    return len(particles),tuple((int(row.get("p1")),int(row.get("p2")),Decimal(row.get("d"))) for row in constraints)


def state_force_energy_from_xml(raw):
    import numpy as np
    positions,box = state_geometry_from_xml(raw)
    root = ET.fromstring(raw)
    forces,energies = root.find("Forces"),root.find("Energies")
    if (forces is None or energies is None or any(row.tag != "Force" for row in forces)
            or energies.get("PotentialEnergy") is None or energies.get("KineticEnergy") is None
            or any(row.get(axis) is None for row in forces for axis in ("x","y","z"))):
        raise UnsupportedNativeXML("actual force State omits requested complete Forces/Energies")
    values = np.asarray([[float(row.get(axis)) for axis in ("x","y","z")] for row in forces],dtype=np.float64)
    potential,kinetic = float(energies.get("PotentialEnergy")),float(energies.get("KineticEnergy"))
    if values.shape != positions.shape or not np.isfinite(values).all() or not all(math.isfinite(row) for row in (potential,kinetic)):
        raise ValueError("actual force State contains incomplete/nonfinite force/energy receivers")
    return positions,box,values,potential


def reduce_same_geometry_force_control(data, atom_count, *, system_xml, relaxed_state_xml, cpu_state_xml):
    """Same original full System, same independently selected relaxed point/box."""
    import numpy as np
    system_sha256, relaxed_state_sha256 = sha256(system_xml).hexdigest(),sha256(relaxed_state_xml).hexdigest()
    actual_positions, actual_box = state_geometry_from_xml(relaxed_state_xml)
    actual_count,_ = constraints_from_system_xml(system_xml)
    if actual_count != atom_count or actual_positions.shape != (atom_count,3):
        raise ValueError("force control substitutes full native System/relaxed atom census")
    for name in ("cuda", "cpu"):
        if (str(np.asarray(data[name+"_system_xml_sha256"]).item()) != system_sha256
                or int(np.asarray(data[name+"_integration_force_groups"]).item()) & 0xffffffff != 0xffffffff
                or str(np.asarray(data["common_relaxed_state_sha256"]).item()) != relaxed_state_sha256):
            raise ValueError("force control changes the actual common System/force groups/relaxed source")
    left, right = (_finite_binary64(data[name+"_box_vectors_nm"]) for name in ("cpu","cuda"))
    if (left.shape != (3,3) or not _same_binary64_bits(left,right)
            or not _same_binary64_bits(left,actual_box)):
        raise ValueError("force engines evaluate different/nonfinite full periodic boxes")
    if any(not _same_binary64_bits(data[name+"_positions_nm"],actual_positions) for name in ("cpu","cuda")):
        raise ValueError("force engines substitute the authentic returned relaxed State")
    for name,raw in (("cuda",relaxed_state_xml),("cpu",cpu_state_xml)):
        positions,box,forces,potential = state_force_energy_from_xml(raw)
        if (positions.shape != (atom_count,3) or not _same_binary64_bits(positions,actual_positions)
                or not _same_binary64_bits(box,actual_box)
                or not _same_binary64_bits(forces,data[name+"_force_kj_mol_nm"])
                or not _same_binary64_bits(potential,data[name+"_potential_kj_mol"])):
            raise ValueError("force/energy arrays differ from the actual full native State receivers")
    return science.reduce_force_control(data,atom_count)


def integrator_controls_from_xml(raw):
    root = ET.fromstring(raw)
    if (root.tag != "Integrator" or root.get("type") != "VerletIntegrator" or root.get("version") != "1"
            or root.get("constraintTolerance") is None or root.get("integrationForceGroups") is None):
        raise UnsupportedNativeXML("unsupported actual chemical-control Integrator XML")
    tolerance = Decimal(root.get("constraintTolerance"))
    if not tolerance.is_finite() or tolerance <= 0:
        raise ValueError("actual chemical-control Integrator omits constraint tolerance")
    groups = int(root.get("integrationForceGroups"))
    if groups & 0xffffffff != 0xffffffff:
        raise ValueError("chemical-control Integrator omits actual force groups")
    return tolerance,groups


def _reported_binary64(value):
    if (type(value) is not dict or set(value) != {"binary64_hex","ieee754_binary64_be"}
            or struct.pack(">d",float.fromhex(value["binary64_hex"])).hex() != value["ieee754_binary64_be"]):
        raise ValueError("minimizer progress substitutes its original binary64 value")
    return float.fromhex(value["binary64_hex"])


def reduce_terminal_minimizer(terminal, termination, progress_rows, *, system_xml, integrator_xml,
                              relaxed_state_xml):
    """Independent final callback, full System constraints and actual final State.

    A known native return with no final callback is an operator completion, not
    proof that the final objective met its stopping standard.
    """
    atom_count,constraints = constraints_from_system_xml(system_xml)
    final,_ = state_geometry_from_xml(relaxed_state_xml)
    tolerance,_ = integrator_controls_from_xml(integrator_xml)
    if (termination["reporter_ever_requests_early_stop"] is not False
            or termination["tolerance_kj_mol_nm"] != "10"
            or type(termination["max_iterations"]) is not int or termination["max_iterations"] != 0
            or termination["progress_view"] != "ALL_CALLBACK_SCALAR_ROWS_AND_FINAL_FULL_OBJECTIVE_ARRAYS"
            or termination["objective_rms_normalization"] != "SQRT_SUM_ALL_3N_OBJECTIVE_COMPONENTS_SQUARED_OVER_N_PARTICLES"):
        raise ValueError("minimizer changed its prospective native stopping/observation contract")
    count,last = 0,None
    for row in progress_rows:
        count += 1
        if (row["callback_ordinal"] != count or row["reporter_requests_early_stop"] is not False
                or row["x_count"] != 3*atom_count or row["gradient_count"] != 3*atom_count
                or row["particle_count"] != atom_count
                or row["objective_rms_normalization"] != termination["objective_rms_normalization"]
                or type(row["optimizer_iteration_index"]) is not int):
            raise ValueError("minimizer progress omits its complete declared callback census")
        last = row
    if (type(termination["callback_count"]) is not int or termination["callback_count"] != count
            or (last is not None and (last["optimizer_iteration_index"] != termination["last_optimizer_iteration_index"]
                or last["full_native_args"] != termination["full_last_native_args"]))):
        raise ValueError("minimizer terminal observation changes the last authentic callback")
    if termination["native_returned"] is not True or termination["error_text"] is not None:
        return None,None,A.UNEVALUABLE,("CHEMICAL_MINIMIZER_KNOWN_ADVERSE_RETURN",)
    if count == 0 or terminal is None:
        return None,None,A.UNEVALUABLE,("FINAL_OBJECTIVE_CALLBACK_MISSING",)
    rms,residual,verdict,reasons = terminal_objective_reduction(terminal["x_nm"],
        terminal["objective_gradient_kj_mol_nm"],final,constraints,atom_count=atom_count,
        constraint_tolerance=tolerance)
    reported = _reported_binary64(last["objective_gradient_rms_kj_mol_nm"])
    norm = 0.0
    for value in terminal["objective_gradient_kj_mol_nm"]:
        norm = math.hypot(norm,float(value))
    expected_reported = norm/math.sqrt(atom_count)
    if not math.isfinite(reported) or reported != expected_reported:
        raise ValueError("terminal full gradient differs from original last callback RMS")
    return rms,residual,verdict,reasons


def assess_control(plan, returned, *, current_raw_root):
    """PURE authentic raw reduction at a caller-selected portable custody root.

    The caller authenticates the original unit definition, completion, receipt,
    typed census and raw archive before selecting this root. This function never
    invokes the producer, consults its absolute workdir or supplies qualification.
    """
    plan.__post_init__()
    returned.__post_init__()
    if returned.plan != plan.identity or returned.assets not in tuple(row[1] for row in plan.selected_assets):
        raise ValueError("chemical/force assessment substitutes its actual selected plan/assets")
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_preparation import directory_census
    root = Path(current_raw_root)
    parents = {Path(row.relative_path).parent for row in returned.files}
    if len(parents) != 1:
        raise ValueError("chemical/force assessment changes its complete flat unit scope")
    relative_directory = next(iter(parents))
    if relative_directory.is_absolute() or ".." in relative_directory.parts:
        raise ValueError("chemical/force portable raw scope escapes selected custody")
    directory = root/relative_directory
    if directory_census(directory,root).files != returned.files:
        raise ValueError("chemical/force raw files differ from its whole authenticated unit census")
    by_path = {row.relative_path:row for row in returned.files}
    def raw(path):
        relative = Path(path)
        if relative.is_absolute() or ".." in relative.parts or relative.as_posix() not in by_path:
            raise ValueError("chemical/force raw operand is absent from original complete file census")
        return (root/relative).read_bytes()
    def document(name):
        return json.loads(raw((relative_directory/name).as_posix()))
    def apparatus_member(row):
        payload = raw(row["relative_path"])
        if (len(payload),sha256(payload).hexdigest()) != (row["byte_count"],row["sha256"]):
            raise ValueError("chemical/force apparatus substitutes authenticated full XML bytes")
        return payload
    objective,agreement = A.UNEVALUABLE,A.UNEVALUABLE
    rms,residual,force,energy = None,None,None,None
    reasons = []
    if not returned.operators_completed:
        reasons.append("CHEMICAL_FORCE_OPERATORS_KNOWN_ADVERSE_RETURN")
    else:
        import numpy as np
        minimizer = document("minimizer-apparatus.json")
        cuda,cpu = document("apparatus-cuda.json"),document("apparatus-cpu.json")
        system = apparatus_member(minimizer["system"])
        integrator = apparatus_member(minimizer["integrator"])
        if any(apparatus_member(row["system"]) != system for row in (cuda,cpu)):
            raise ValueError("minimizer and force branches change the actual full System")
        relaxed = raw((relative_directory/"minimized.xml").as_posix())
        cpu_state = raw((relative_directory/"cpu-force-reference.xml").as_posix())
        try:
            constraints_from_system_xml(system)
            integrator_controls_from_xml(integrator)
            for row in (cuda,cpu):
                integrator_controls_from_xml(apparatus_member(row["integrator"]))
            state_force_energy_from_xml(relaxed)
            state_force_energy_from_xml(cpu_state)
        except UnsupportedNativeXML:
            return c.ChemicalForceAssessment("assessment."+returned.unit_id,plan.identity,returned.identity,
                A.UNEVALUABLE,A.UNEVALUABLE,None,None,None,None,("ACTUAL_OPENMM_XML_SHAPE_UNSUPPORTED",))
        terminal_path = (relative_directory/"minimizer-terminal.npz").as_posix()
        terminal = None
        if terminal_path in by_path:
            with np.load(root/terminal_path,allow_pickle=False) as selected:
                terminal = {name:selected[name] for name in selected.files}
        # The compact progress stream retains every callback; no thinning.
        with (directory/"minimizer-progress.jsonl").open() as progress:
            rms,residual,objective,why = reduce_terminal_minimizer(terminal,
                document("minimizer-termination.json"),(json.loads(line) for line in progress),
                system_xml=system,integrator_xml=integrator,relaxed_state_xml=relaxed)
        reasons.extend(why)
        force_path = returned.force_receiver_path
        if force_path not in by_path:
            raise ValueError("force receiver is absent from the authenticated whole unit census")
        with np.load(root/force_path,allow_pickle=False) as data:
            force,energy = reduce_same_geometry_force_control(data,returned.atom_count,
                system_xml=system,relaxed_state_xml=relaxed,
                cpu_state_xml=cpu_state)
        agreement = A.SATISFIED if force <= science.FORCE_TARGET and energy <= science.ENERGY_TARGET_PER_ATOM else A.REFUSED
        if agreement is A.REFUSED:
            reasons.append("FROZEN_FORCE_OR_ENERGY_PRECISION_TARGET_FAILED")
    return c.ChemicalForceAssessment("assessment."+returned.unit_id,plan.identity,returned.identity,
        objective,agreement,rms,residual,force,energy,tuple(sorted(set(reasons))))
