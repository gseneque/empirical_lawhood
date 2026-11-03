# SPDX-License-Identifier: MPL-2.0
"""PURE authentic NVE admission and complete actual clock/energy reduction."""
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.status import OperationalStatus
from . import contracts,nve_contracts as c,science
from .control_science import (UnsupportedNativeXML,_reported_binary64,_same_binary64_bits,
    constraints_from_system_xml,integrator_controls_from_xml,state_force_energy_from_xml)


def validate_operands(plan,source,supplies,custody):
    """Caller first authenticates actual independent original manifests/receipts.

    custody rows are model, original definition, completion identity/completion,
    original chemical return, and the independent canonical numerical assessment.
    No native contact or approval is created by this PURE join.
    """
    plan.__post_init__()
    from .serialized_nve_custody import validate_direct_custody
    validate_direct_custody(plan,custody)
    source.__post_init__()
    if p.identity(source)!=plan.chemical_controls.source or source.engine_inventory_sha256!=plan.chemical_controls.engine_inventory_sha256:
        raise ValueError('NVE control substitutes original admitted engine/scientific source')
    if (tuple(row.model_id for row in supplies)!=tuple(row[0] for row in plan.admitted_parents)
            or tuple(row[0] for row in custody)!=tuple(row.model_id for row in supplies)):
        raise ValueError('NVE control changes genuine admitted selected parent denominator')
    selected=dict(plan.chemical_controls.selected_assets)
    for supply,row,parent in zip(supplies,custody,plan.admitted_parents,strict=True):
        supply.__post_init__()
        name,definition,completion_id,completion,returned,assessment=row
        for original in (definition,completion,returned,assessment):original.__post_init__()
        if (parent!=(name,supply.identity,definition.identity,completion_id,returned.identity,ObjectIdentity.from_record(assessment.product_id,assessment))
                or ObjectIdentity.from_record(completion_id.object_id,completion)!=completion_id
                or definition.operation_id!='rubisco.chemical-force.unit'
                or definition.subwork_id!='control.chemical-force.'+name
                or definition.configuration!=plan.chemical_controls.identity
                or completion.definition!=definition.identity or completion.operational_status is not OperationalStatus.SUCCEEDED
                or completion.omitted_output_ids or completion.unknown_streams
                or completion.output_ids!=tuple(sorted(output.output_id for output in definition.outputs))
                or not returned.operators_completed or returned.error_text is not None
                or returned.unit_id!=definition.subwork_id or returned.plan!=plan.chemical_controls.identity
                or supply.chemical_return!=returned.identity or supply.chemical_assessment!=ObjectIdentity.from_record(assessment.product_id,assessment)
                or assessment.plan!=plan.chemical_controls.identity or assessment.returned!=returned.identity
                or assessment.objective_precision_disposition is not A.SATISFIED or assessment.force_agreement_disposition is not A.SATISFIED
                or p.identity(supply.model_assets)!=selected[name] or returned.assets!=selected[name]
                or supply.model_assets.source!=plan.chemical_controls.source
                or any(member.evidence not in returned.files for member in (supply.system,supply.relaxed_state))):
            raise ValueError('NVE needs genuine complete chemical custody and independent objective/force admission')
        count,_=constraints_from_system_xml(supply.system.raw_utf8.encode())
        positions,_,_,_=state_force_energy_from_xml(supply.relaxed_state.raw_utf8.encode())
        if count!=returned.atom_count or positions.shape!=(count,3):
            raise ValueError('NVE relaxed source substitutes original full atom/System census')
    return plan


def requested_binary64_positions(raw):
    """Read the unchanged complete native setter observation, without coercion."""
    import numpy as np
    value=json.loads(raw)
    def decode(row):
        if type(row) is dict and set(row)=={'unit','value'}:
            if row['unit']!='nanometer':raise ValueError('NVE setter changes explicit nanometer unit')
            return decode(row['value'])
        if type(row) is dict and 'full_native_bytes_hex' in row:
            dtype=np.dtype(row['dtype'])
            if dtype.kind!='f' or dtype.itemsize!=8 or row['byte_order']!='C':
                raise ValueError('NVE setter changes actual binary64 array representation')
            values=np.frombuffer(bytes.fromhex(row['full_native_bytes_hex']),dtype=dtype)
            return values.reshape(tuple(row['shape']))
        if type(row) is list:return [decode(value) for value in row]
        return _reported_binary64(row)
    result=np.asarray(decode(value))
    if result.dtype.kind!='f' or result.dtype.itemsize!=8 or not np.isfinite(result).all():
        raise ValueError('NVE setter omits full finite actual native positions/box')
    return result


def constraints_met(positions,constraints,tolerance):
    """Exact squared binary64 distances against declared complete precision."""
    seen=set()
    for left,right,distance in constraints:
        if (left==right or not 0<=left<len(positions) or not 0<=right<len(positions)
                or tuple(sorted((left,right))) in seen or not distance.is_finite() or distance<=0):
            raise ValueError('NVE actual System constraint census substitutes particles/distances')
        seen.add(tuple(sorted((left,right))))
        d,tol=Fraction(distance),Fraction(tolerance)
        square=sum(((Fraction.from_float(float(positions[left,axis]))-Fraction.from_float(float(positions[right,axis])))**2
            for axis in range(3)),Fraction(0))
        if not (d*(1-tol))**2<=square<=(d*(1+tol))**2:return False
    return True


def join_full_hamiltonian(actual,admitted,resolution):
    """Retain every System member; only the frozen refined PME precision differs.

    The source builds the primary System with the same unchanged Amber operator
    as the admitted force control. Refined rebuilding may change the one actual
    NonbondedForce serializer attribute ``ewaldTolerance`` and no other byte or
    XML member. Counts alone cannot establish the Hamiltonian.
    """
    parser=lambda:ET.XMLParser(target=ET.TreeBuilder(insert_comments=True,insert_pis=True))
    current=ET.fromstring(actual,parser=parser())
    original=ET.fromstring(admitted,parser=parser())
    for system in (current,original):
        if (system.tag!='System' or system.get('type')!='System' or system.get('version')!='1'
                or system.find('PeriodicBoxVectors') is None or system.find('Forces') is None):
            raise UnsupportedNativeXML('NVE Hamiltonian omits complete supported System shape')
    original_forces=original.findall('./Forces/Force[@type="NonbondedForce"]')
    current_forces=current.findall('./Forces/Force[@type="NonbondedForce"]')
    if len(original_forces)!=1 or len(current_forces)!=1:
        raise UnsupportedNativeXML('NVE Hamiltonian lacks its single actual Amber NonbondedForce')
    primary=next(row[2] for row in contracts.INTEGRATION if row[0]=='primary')
    selected=next(row[2] for row in contracts.INTEGRATION if row[0]==resolution)
    for force,tolerance in ((original_forces[0],primary),(current_forces[0],selected)):
        value=force.get('ewaldTolerance')
        if value is None:raise UnsupportedNativeXML('NVE actual NonbondedForce omits ewaldTolerance')
        if not Decimal(value).is_finite() or Decimal(value)!=tolerance:
            raise ValueError('NVE Hamiltonian substitutes frozen actual Ewald precision')
    if resolution=='primary':
        if actual!=admitted:raise ValueError('NVE primary Hamiltonian differs from whole admitted System')
    else:
        current_forces[0].set('ewaldTolerance',original_forces[0].get('ewaldTolerance'))
        if ET.tostring(current)!=ET.tostring(original):
            raise ValueError('NVE refined Hamiltonian changes more than frozen Ewald precision')


def join_context(plan,apparatus,native_calls,directory,system,integrator):
    """Assess original requested and realized apparatus, without filling defaults."""
    controls=plan.chemical_controls
    properties=dict(Precision=controls.platform_precision,DeviceIndex=controls.device_index,
        DeterministicForces=controls.deterministic_forces,UseCpuPme=controls.use_cpu_pme)
    tolerance,groups=integrator_controls_from_xml(integrator)
    expected=dict(system=apparatus['system'],integrator=apparatus['integrator'],platform='CUDA',
        properties=properties,force_groups=groups,constraint_tolerance=apparatus['constraint_tolerance'])
    rows=tuple(row for row in native_calls if row.role=='sampling.context')
    observations=tuple(directory.glob('context-realization-*.json'))
    if len(rows)!=1 or len(observations)!=1:
        raise ValueError('NVE assessment omits single original actual Context observation')
    requested=json.loads(rows[0].requested_json)
    realized=json.loads(rows[0].realized_json)
    if (apparatus!=expected or requested!=expected
            or not _same_binary64_bits(_reported_binary64(apparatus['constraint_tolerance']),float(tolerance))
            or apparatus['system']['sha256']!=sha256(system).hexdigest()
            or apparatus['integrator']['sha256']!=sha256(integrator).hexdigest()
            or realized!=json.loads(observations[0].read_bytes())
            or realized.get('platform')!='CUDA' or type(realized.get('actual_properties')) is not dict
            or any(realized['actual_properties'].get(key)!=value for key,value in properties.items())):
        raise ValueError('NVE original Context substitutes selected actual System/Integrator/platform/properties')


def exact_reported_component_excursion(components,atom_count):
    """Supplement the unchanged total metric; no true backend error bound.

    These are the already-reported finite binary64 component values. Their exact
    rational sums retain small changes that their rounded native total may hide.
    """
    import math
    if type(atom_count) is not int or atom_count<=0 or len(components)!=11:
        raise ValueError('NVE component diagnostic changes complete eleven-state atom census')
    values=[]
    for potential,kinetic in components:
        if any(type(value) is not float or not math.isfinite(value) for value in (potential,kinetic)):
            raise ValueError('NVE component diagnostic substitutes finite reported binary64 values')
        values.append(Fraction.from_float(potential)+Fraction.from_float(kinetic))
    return max(abs(value-values[0]) for value in values)/atom_count


def validate_native_inputs(plan,returned,calls,roster):
    """Original caller-authenticated call returns bind seed and initial controls."""
    if tuple(row.call_id for row in calls)!=tuple(row.object_id for row in returned.native_calls):
        raise ValueError('NVE independent assessment omits complete original native call returns')
    for row in calls:
        row.__post_init__()
        if row.model_id!=returned.unit_id or row.termination!='COMPLETED' or row.error_text is not None:
            raise ValueError('positive NVE operators have adverse/substituted actual native calls')
    def request(role):
        rows=tuple(row for row in calls if row.role==role)
        if len(rows)!=1:raise ValueError('NVE native input has missing/duplicate actual '+role)
        return json.loads(rows[0].requested_json)
    def decimal(value):
        if type(value) is not dict or set(value)!={'decimal'}:raise ValueError('NVE native Decimal input lost exact spelling')
        return Decimal(value['decimal'])
    _,seed,_=next(row for row in contracts.ENSEMBLES if row[0]==roster[-2])
    velocity=request('sampling.initialize-thermal-velocities')
    dt,tolerance=next(row[1:] for row in contracts.INTEGRATION if row[0]==roster[-1])
    if (velocity['velocity_seed']!=seed or type(velocity['velocity_seed']) is not int
            or decimal(velocity['temperature_kelvin'])!=plan.temperature_kelvin
            or decimal(request('sampling.verlet-integrator')['step_size_picosecond'])!=dt
            or decimal(request('sampling.apply-constraint-tolerance')['tolerance'])!=tolerance
            or decimal(request('sampling.apply-position-constraints')['tolerance'])!=tolerance
            or decimal(request('sampling.apply-velocity-constraints')['tolerance'])!=tolerance):
        raise ValueError('NVE actual initialization substitutes fixed seed/timestep/temperature/constraints')
    intervals=tuple(json.loads(row.requested_json) for row in calls if row.role=='sampling.nve-integration')
    if len(intervals)!=10 or any(row['steps']!=int(Decimal(10)/dt) or decimal(row['step_size_picosecond'])!=dt
            or row['physical_time_picosecond']!=10 for row in intervals):
        raise ValueError('NVE actual integration omits the full ten selected10ps increments')


def reduce_return(plan,returned,supply,*,current_raw_root,native_calls):
    """Every original full receiver, checkpoint, clock and apparatus is read.

    Native checkpoints are authenticated opaque evidence, not automatically
    replayed or a claim that a restored Context was independently demonstrated.
    """
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_preparation import directory_census
    import numpy as np
    returned.__post_init__()
    supply.__post_init__()
    if returned.plan!=plan.identity or returned.relaxed_supply!=supply.identity:
        raise ValueError('NVE assessment substitutes actual selected return/supply')
    if not returned.operators_completed:return A.UNEVALUABLE,None,('NVE_OPERATORS_KNOWN_ADVERSE_RETURN',),None
    directories={Path(row.relative_path).parent for row in returned.files}
    if len(directories)!=1:raise ValueError('NVE assessment changes complete flat unit raw scope')
    relative=next(iter(directories))
    root=Path(current_raw_root)
    directory=root/relative
    if relative.is_absolute() or '..' in relative.parts or directory_census(directory,root).files!=returned.files:
        raise ValueError('NVE assessment changes original full raw custody')
    by_path={row.relative_path:row for row in returned.files}
    def raw_member(row):
        path=row['relative_path']
        expected=by_path.get(path)
        if expected is None or (expected.byte_count,expected.sha256)!=(row['byte_count'],row['sha256']):
            raise ValueError('NVE receiver/checkpoint/apparatus is absent from exact whole raw census')
        raw=(root/path).read_bytes()
        if (len(raw),sha256(raw).hexdigest())!=(expected.byte_count,expected.sha256):raise ValueError('NVE raw bytes changed')
        return raw
    roster=next(row for row in contracts.trajectory_roster() if c.unit_id(row)==returned.unit_id)
    validate_native_inputs(plan,returned,native_calls,roster)
    dt,tolerance=next(row[1:] for row in contracts.INTEGRATION if row[0]==roster[-1])
    apparatus=json.loads((directory/'apparatus-cuda.json').read_bytes())
    system=raw_member(apparatus['system'])
    integrator=raw_member(apparatus['integrator'])
    try:
        join_full_hamiltonian(system,supply.system.raw_utf8.encode(),roster[-1])
        join_context(plan,apparatus,native_calls,directory,system,integrator)
        atom_count,constraints=constraints_from_system_xml(system)
        observed_tolerance,_=integrator_controls_from_xml(integrator)
        actual_integrator=ET.fromstring(integrator)
        if actual_integrator.get('stepSize') is None:raise UnsupportedNativeXML('actual NVE Integrator has no stepSize')
        if Decimal(actual_integrator.get('stepSize'))!=dt or observed_tolerance!=tolerance:
            raise ValueError('NVE actual Integrator substitutes selected step/constraint precision')
        actual_positions,actual_box,_,_=state_force_energy_from_xml(supply.relaxed_state.raw_utf8.encode())
        position_paths=tuple(directory.glob('requested-positions-*.json'))
        box_paths=tuple(directory.glob('requested-box-*.json'))
        if (len(position_paths)!=1 or len(box_paths)!=1 or not _same_binary64_bits(requested_binary64_positions(position_paths[0].read_bytes()),actual_positions)
                or not _same_binary64_bits(requested_binary64_positions(box_paths[0].read_bytes()),actual_box)):
            raise ValueError('NVE actual setter changes independently admitted relaxed point/box')
        rows=[]
        components=[]
        constraints_satisfied=True
        with (directory/'nve-progress.jsonl').open() as progress:
            for ordinal,line in enumerate(progress):
                row=json.loads(line)
                if ordinal>10 or row['receiver_ordinal']!=ordinal+1:
                    raise ValueError('NVE progress duplicates/thins full eleven actual receivers')
                name='initial-full-state' if ordinal==0 else 'nve-state-'+str(ordinal).zfill(2)
                if row['name']!=name or Path(row['full_state']['relative_path']).name!=name+'.xml':
                    raise ValueError('NVE progress substitutes ordered actual State receivers')
                raw=raw_member(row['full_state'])
                positions,box,_,potential=state_force_energy_from_xml(raw)
                state=ET.fromstring(raw)
                velocities=state.find('Velocities')
                energies=state.find('Energies')
                if (state.get('time') is None or state.get('stepCount') is None or velocities is None
                        or any(v.tag!='Velocity' or any(v.get(axis) is None for axis in ('x','y','z')) for v in velocities)):
                    raise UnsupportedNativeXML('actual NVE State omits full clock/step/velocity fields')
                values=np.asarray([[float(v.get(axis)) for axis in ('x','y','z')] for v in velocities],dtype=np.float64)
                if positions.shape!=(atom_count,3) or values.shape!=positions.shape or not np.isfinite(values).all() or not _same_binary64_bits(box,actual_box):
                    raise ValueError('NVE State substitutes complete atom/velocity/periodic-box census')
                kinetic=float(energies.get('KineticEnergy'))
                time,steps=Decimal(state.get('time')),int(state.get('stepCount'))
                if (steps!=row['steps'] or time!=Decimal(row['time_picosecond'])
                        or not _same_binary64_bits(potential,row['potential_kj_mol'])
                        or not _same_binary64_bits(kinetic,row['kinetic_kj_mol'])
                        or not _same_binary64_bits(potential+kinetic,row['total_energy_kj_mol'])):
                    raise ValueError('NVE producer progress differs from original full native State')
                checkpoint=raw_member(row['checkpoint'])
                if not checkpoint or Path(row['checkpoint']['relative_path']).name!='nve-checkpoint-'+str(ordinal).zfill(2)+'.bin':
                    raise ValueError('NVE progress omits original ordered actual checkpoint')
                constraints_satisfied=constraints_satisfied and constraints_met(positions,constraints,tolerance)
                rows.append(dict(total_energy_kj_mol=potential+kinetic,time_picosecond=str(time),steps=steps))
                components.append((potential,kinetic))
        numerical=json.loads((directory/'numerical-control.json').read_bytes())
        expected=dict(atom_count=atom_count,step_size_picosecond=str(dt),receivers=rows,
            integration_wall_seconds=numerical['integration_wall_seconds'])
        if numerical!=expected or returned.atom_count!=atom_count:
            raise ValueError('NVE reported numerical control differs from complete independent raw States')
        excursion,_,_=science.reduce_nve_control(expected,atom_count,dt)
        component_excursion=exact_reported_component_excursion(components,atom_count)
    except UnsupportedNativeXML:
        return A.UNEVALUABLE,None,('ACTUAL_NVE_XML_SHAPE_UNSUPPORTED',),None
    reasons=[]
    if excursion>science.NVE_TARGET_PER_ATOM or not constraints_satisfied:
        reasons.append('FROZEN_NVE_ENERGY_OR_CONSTRAINT_PRECISION_FAILED')
    if component_excursion>Fraction(science.NVE_TARGET_PER_ATOM):
        reasons.append('EXACT_REPORTED_COMPONENT_SUM_PRECISION_FAILED')
    return (A.REFUSED if reasons else A.SATISFIED),excursion,tuple(sorted(reasons)),component_excursion


def assess_nve(plan,returns,supplies,*,current_raw_root,native_calls=()):
    """Full96 outcomes and48 refinement pairs; unentered work is UNEVALUABLE."""
    plan.__post_init__()
    by_return={row.unit_id:row for row in returns}
    if len(by_return)!=len(returns) or set(by_return)-{c.unit_id(row) for row in plan.selected_cases}:
        raise ValueError('NVE assessment fabricates/repeats an unselected native result')
    by_supply={row.identity:row for row in supplies}
    by_calls=dict(native_calls)
    if len(by_calls)!=len(native_calls) or set(by_calls)!=set(by_return):
        raise ValueError('NVE assessment changes actual native-call custody denominator')
    cases=[]
    component_excursions=[]
    for name in c.unit_ids():
        if name not in by_return:
            cases.append((name,A.UNEVALUABLE,None,('NVE_NOT_ATTEMPTED',)))
            component_excursions.append((name,None,None))
        else:
            returned=by_return[name]
            verdict,excursion,reasons,component_excursion=reduce_return(plan,returned,by_supply[returned.relaxed_supply],
                current_raw_root=current_raw_root,native_calls=by_calls[name])
            cases.append((name,verdict,excursion,reasons))
            component_excursions.append((name,None,None) if component_excursion is None else
                (name,component_excursion.numerator,component_excursion.denominator))
    by_case={row[0]:row for row in cases}
    by_component={name:None if numerator is None else Fraction(numerator,denominator)
        for name,numerator,denominator in component_excursions}
    refinements=[]
    for key in contracts.trajectory_roster():
        if key[-1]!='primary':continue
        left,right=by_case[c.unit_id(key)],by_case[c.unit_id((*key[:-1],'refined'))]
        verdict=A.UNEVALUABLE
        if all(row[1] is A.SATISFIED for row in (left,right)):
            verdict=A.SATISFIED if (right[2]<=left[2]+science.REFINEMENT_ROUNDOFF_FLOOR_PER_ATOM
                and by_component[right[0]]<=by_component[left[0]]+Fraction(science.REFINEMENT_ROUNDOFF_FLOOR_PER_ATOM)) else A.REFUSED
        elif any(row[1] is A.REFUSED for row in (left,right)):verdict=A.REFUSED
        refinements.append((c.unit_id(key).rsplit('.',1)[0],verdict,left[2],right[2]))
    outcomes=tuple(row[1] for row in (*cases,*refinements))
    verdict=A.UNEVALUABLE if A.UNEVALUABLE in outcomes else A.REFUSED if A.REFUSED in outcomes else A.SATISFIED
    return c.NVEControlAssessment('assessment.'+plan.plan_id,plan.identity,tuple(row.identity for row in sorted(returns,key=lambda row:row.unit_id)),
        tuple(cases),tuple(refinements),verdict,tuple(component_excursions))
