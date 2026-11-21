# SPDX-License-Identifier: MPL-2.0
"""Independently join every electronic pair to its original sampled frame."""

from fractions import Fraction
from hashlib import sha256
import math
import re

from empirical_lawhood.adapters.rubisco.rubisco_response.constrained_electronic_native import STATE_ARRAYS
from empirical_lawhood.domains.rubisco.rubisco_response.constrained_electronic_read import _array as electronic_array, assess_electronic_arrays
from empirical_lawhood.domains.rubisco.rubisco_response.electronic_coupling_science import pair_coupling, singlet_triplet_spin_orbit
from empirical_lawhood.domains.rubisco.rubisco_response.electronic_ensemble_records import ElectronicEnsembleRule
from empirical_lawhood.domains.rubisco.rubisco_response.electronic_ensemble_science import reduce_electronic_pair, joint_electronic_analysis
from empirical_lawhood.domains.rubisco.rubisco_response.electronic_observation_native import state_prefix
from empirical_lawhood.domains.rubisco.rubisco_response.equilibrium_reweighting_read import validate_reweighting_inputs, read_equilibrium_reweighting, recheck_reweighting_originals
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_backend_evidence import GpuTraceAssessment
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_operation import ObservedElectronicEquilibriumConfig
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_assessment import _array, _json
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_read import authenticate_trajectory_files
from empirical_lawhood.domains.rubisco.electronic.spin_orbit import SOC_ARRAYS


_SAMPLE = re.compile(r'sample\.([0-9]{16})\.state\.(.+)\Z')
PAIR_COLUMNS = ('donor_energy_hartree', 'acceptor_energy_hartree', 'diabatic_gap_hartree',
    'orthogonal_gap_hartree', 'coupling_real_hartree', 'coupling_imaginary_hartree',
    'coupling_squared_hartree2', 'gap_speed_hartree_per_second', 'absolute_determinant_overlap',
    'directional_defect_hartree', 'donor_spin_square_excess', 'acceptor_spin_square_excess')


def validate_electronic_ensemble_inputs(selection, sources):
    exact(selection, ElectronicEnsembleRule)
    capacity = validate_reweighting_inputs(selection.equilibrium, sources)
    phase_bytes, rows = 0, 0
    for trace, source in zip(selection.equilibrium.traces,sources,strict=True):
        exact(source.config, ObservedElectronicEquilibriumConfig)
        prototypes = {p.electronic.state.state_id:p for p in source.config.selection.observations.prototypes}
        primary = source.config.original.selection.electronic.state.state_id
        selected = tuple(p for p in selection.pairs if p.ensemble_id == trace.ensemble_id)
        if any(p.donor_state_id != primary or p.acceptor_state_id not in prototypes for p in selected):
            raise ValueError('electronic pair substitutes its actual donor ensemble or observed acceptor state')
        for pair in selected:
            if pair.coupling != 'SPIN_FREE' and (
                    prototypes[pair.donor_state_id].electronic.state.spin_orbit is None):
                raise ValueError('spin transfer has no selected original spin-orbit operator')
            if pair.coupling == 'SPIN_ORBIT_SINGLET_TRIPLET_MULTIPLET' and {
                    prototypes[state_id].electronic.state.spin_multiplicity
                    for state_id in (pair.donor_state_id,pair.acceptor_state_id)} != {1,3}:
                raise ValueError('complete oxygen spin transfer requires the original singlet and triplet states')
        n = source.config.selection.settings.expected_samples
        phase_bytes += n*(source.config.selection.physical_atom_count*3*8+256*len(prototypes)+4096)
        rows += n*len(selected)*len(PAIR_COLUMNS)*8
    columns = len(selection.pairs)+len(selection.equilibrium.contrasts)
    joint_bytes = selection.equilibrium.criteria.bootstrap_replicates*columns*1024
    needed = capacity['estimated_workspace_bytes']+phase_bytes+rows*3+joint_bytes+3*selection.electronic_criteria.maximum_workspace_bytes
    if needed > selection.maximum_workspace_bytes:
        raise ValueError('complete electronic ensemble exceeds its selected phase, matrix and analysis workspace')
    if 3*len(selection.pairs)+6*len(sources)+5*len(selection.equilibrium.ensembles)+2 > 250:
        raise ValueError('electronic ensemble exceeds the complete bounded named-array transport')
    return dict(original_equilibrium=capacity, estimated_workspace_bytes=needed,
        selected_workspace_bytes=selection.maximum_workspace_bytes)


def _qm_geometry(prototype, coordinates):
    """Independent original-coordinate/link construction; no electronic call."""
    import numpy as np
    rows = [coordinates[i] for i in prototype.path.qm_atom_indices]
    for boundary in prototype.path.boundaries:
        q, m = coordinates[boundary.qm_atom_index], coordinates[boundary.mm_atom_index]
        displacement = m-q
        norm = float(np.linalg.norm(displacement))
        if norm <= 0:
            raise ValueError('electronic frame has a coincident QM/MM link boundary')
        rows.append(q+float(boundary.link_distance_angstrom)*displacement/norm)
    return np.asarray(rows)/.52917721092


def assess_original_electronic_point(*, prototype, primary_prototype, frame, raw, criteria, primary_native):
    """Reduce one already authenticated frame/state, preserving its failures."""
    import numpy as np
    state = prototype.electronic.state
    point = _json(raw['json']) if 'json' in raw else None
    base = dict(state=state.identity.to_document(), point=point, complete=False,
        electronic_assessment=None, gpu_assessment=None, findings=(), missing=())
    if point is None:
        base['missing'] = ('ORIGINAL_ELECTRONIC_POINT_NOT_RETURNED',)
        return base, None
    primary = prototype == primary_prototype
    evaluation = frame['evaluation'] if primary else 1
    if (point.get('sample_ordinal') != frame['ordinal'] or point.get('sample_step') != frame['step']
            or point.get('sampled_prototype') != primary_prototype.identity.to_document()
            or point.get('observed_prototype') != prototype.identity.to_document()
            or point.get('state') != state.identity.to_document() or point.get('primary') is not primary
            or point.get('coordinate_sha256') != frame['coordinate_sha256']
            or point.get('evaluation') != evaluation):
        raise ValueError('electronic point substitutes its original molecular frame, state or force evaluation')
    if not primary:
        elapsed = point.get('auxiliary_elapsed_seconds')
        if type(elapsed) not in (int,float) or not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError('electronic point omits its original complete auxiliary elapsed cost')
        gpu = GpuTraceAssessment(prototype.engine,state=state)
        for name,value in sorted(raw.items()):
            if name.startswith('gpu.'):
                gpu.consume(name,value)
        try:
            base['gpu_assessment'] = gpu.finish(successful=point['error'] is None,expected_evaluations=1)
        except ValueError:
            if point['error'] is None:
                raise
            base['missing'] = ('FAILED_POINT_GPU_COST_CENSUS_UNAVAILABLE',)
    if point['error'] is not None:
        base['missing'] += ('ORIGINAL_ELECTRONIC_POINT_FAILED',)
        return base, None
    prefix = f'electronic.{evaluation:016d}.'
    metadata = _json(raw[prefix+'state.json'])
    if (metadata['state'] != state.to_document() or metadata['evaluation'] != evaluation
            or metadata['atom_charges'] != frame['qm_atomic_numbers']
            or not np.allclose(np.asarray(metadata['atom_coordinates_bohr']), frame['qm_coordinates_bohr'],
                rtol=0,atol=float(criteria.matrix_tolerance))):
        raise ValueError('electronic matrices change their original state, nuclei or link geometry')
    expected = set(STATE_ARRAYS) | (set(SOC_ARRAYS) if state.spin_orbit is not None else set())
    if set(metadata['arrays']) != expected:
        raise ValueError('electronic point changes its complete selected matrix population')
    arrays = {name:electronic_array(raw[prefix+name+'.npy'],description=spec,
        maximum_bytes=criteria.maximum_workspace_bytes//8) for name,spec in metadata['arrays'].items()}
    assessment = assess_electronic_arrays(state=state,metadata=metadata,arrays=arrays,criteria=criteria)
    if primary:
        native, derivative = primary_native, frame['primary_velocity_gradient']
    else:
        prefix = f'evaluation.{evaluation:016d}.'
        native = _json(raw[prefix+'native-return.json'])
        gradient = _array(raw[prefix+'gradient_hartree_per_bohr.npy'],frame['velocity'].shape)
        energy = float(_array(raw[prefix+'energy_hartree.npy'],()))
        if energy != native['energy_hartree']:
            raise ValueError('vertical electronic return substitutes its original energy array')
        derivative = math.fsum((gradient*frame['velocity']).ravel())*1e13/.52917721092
    if (native is None or native['energy_hartree'] != point['energy_hartree']
            or native['bohr_angstrom'] != .52917721092
            or native['hartree_kj_mol'] != frame['hartree_kj_mol']
            or native['gradient_unit'] != frame['gradient_unit']):
        raise ValueError('vertical electronic point changes its complete original energy or physical units')
    findings = []
    if (native.get('scf_converged') is not True
            or type(native.get('orbital_gradient_norm')) not in (int,float)
            or not math.isfinite(native['orbital_gradient_norm'])
            or native['orbital_gradient_norm'] >= float(prototype.electronic.orbital_gradient_tolerance)):
        findings.append('SELECTED_CONSTRAINED_STATIONARITY_NOT_SATISFIED')
    for key in ('selected_matrix_criteria','selected_spin_square_criteria'):
        if assessment[key] != 'SATISFIED':
            findings.append(key.upper()+'_NOT_SATISFIED')
    base.update(electronic_assessment=assessment,findings=tuple(findings),complete=not findings)
    return base, dict(arrays=arrays,metadata=metadata,energy=point['energy_hartree'],velocity_gradient=derivative)


def read_electronic_ensembles(*, selection, sources, assessor_source):
    import numpy as np
    capacity = validate_electronic_ensemble_inputs(selection,sources)
    frames = {}
    def collect(trace,source,frame,q):
        prototype = source.config.original.selection
        velocity = frame['velocities_nm_per_ps'].copy()
        frames[(trace.trace_id,frame['sample_ordinal'])] = dict(ordinal=frame['sample_ordinal'],
            step=frame['step'],evaluation=frame['evaluation'],velocity=velocity,
            coordinate_sha256=sha256(frame['coordinates_angstrom'].tobytes()).hexdigest(),
            qm_coordinates_bohr=_qm_geometry(prototype,frame['coordinates_angstrom']),
            qm_atomic_numbers=[source.representation.atoms[i].atomic_number for i in prototype.path.qm_atom_indices]
                +[1]*len(prototype.path.boundaries),
            primary_velocity_gradient=math.fsum((frame['reference_gradient_hartree_per_bohr']*velocity).ravel())*1e13/.52917721092,
            hartree_kj_mol=frame['hartree_kj_mol'],gradient_unit=frame['gradient_unit'])
    equilibrium, projected = read_equilibrium_reweighting(selection=selection.equilibrium,sources=sources,
        assessor_source=assessor_source,sample_consumer=collect)
    values, support, census = {}, {}, {}
    for trace,source in zip(selection.equilibrium.traces,sources,strict=True):
        pairs = tuple(p for p in selection.pairs if p.ensemble_id == trace.ensemble_id)
        n = source.config.selection.settings.expected_samples
        for pair in pairs:
            values[(pair.pair_id,trace.trace_id)] = np.full((n,len(PAIR_COLUMNS)),np.nan,dtype='<f8')
            support[(pair.pair_id,trace.trace_id)] = np.zeros(n,dtype='|b1')
        census[trace.trace_id] = dict(expected_samples=n,observed_frames={},unfinished_frame_groups=[])
        if source.original_result is None:
            continue
        prototypes = source.config.selection.observations.prototypes
        primary = source.config.original.selection
        native_names = {f'evaluation.{f["evaluation"]:016d}.native-return.json':ordinal
            for (name,ordinal),f in frames.items() if name == trace.trace_id}
        original_native = {}
        original = source.original_result
        files = authenticate_trajectory_files(source.native_subwork,original.definition,original.returned,
            source.config.selection,primary,
            select_member=lambda name:name in native_names or _SAMPLE.fullmatch(name) is not None,
            maximum_array_bytes=selection.electronic_criteria.maximum_workspace_bytes//8)
        current, group, retained = None, {}, 0

        def reduce_frame(ordinal,raw):
            if not 1 <= ordinal <= n:
                raise ValueError('electronic archive adds an unassigned sample ordinal')
            frame = frames.get((trace.trace_id,ordinal))
            if frame is None:
                if original.returned.error is None:
                    raise ValueError('successful electronic archive lacks its original equilibrium frame')
                census[trace.trace_id]['unfinished_frame_groups'].append(ordinal)
                return
            reports, operands = {}, {}
            for prototype in prototypes:
                prefix = state_prefix(prototype,ordinal)
                subset = {name[len(prefix):]:value for name,value in raw.items() if name.startswith(prefix)}
                point_name = prefix[:-1]+'.json'
                if point_name in raw:
                    subset['json'] = raw[point_name]
                state_id = prototype.electronic.state.state_id
                reports[state_id],operands[state_id] = assess_original_electronic_point(prototype=prototype,
                    primary_prototype=primary,frame=frame,raw=subset,criteria=selection.electronic_criteria,
                    primary_native=original_native.get(ordinal))
            pair_reports = {}
            for pair in pairs:
                a,b = operands[pair.donor_state_id],operands[pair.acceptor_state_id]
                row = dict(complete=False,findings=(),missing=())
                pair_reports[pair.pair_id] = row
                if a is None or b is None:
                    row['missing'] = ('ORIGINAL_PAIR_OPERANDS_UNAVAILABLE',)
                    continue
                aa,bb = a['arrays'],b['arrays']
                if (a['metadata']['ao_labels'] != b['metadata']['ao_labels']
                        or not np.allclose(aa['ao-overlap'],bb['ao-overlap'],rtol=0,
                            atol=float(selection.electronic_criteria.matrix_tolerance))):
                    raise ValueError('electronic pair changes its complete original AO basis and metric')
                soc = None if pair.coupling == 'SPIN_FREE' else .5*sum(aa[k]+bb[k] for k in SOC_ARRAYS)
                try:
                    computed = pair_coupling(overlap=aa['ao-overlap'],coefficients_a=aa['mo-coefficients'],
                        occupations_a=aa['mo-occupations'],energy_a=a['energy'],potential_a=aa['constraint-potential'],
                        coefficients_b=bb['mo-coefficients'],occupations_b=bb['mo-occupations'],energy_b=b['energy'],
                        potential_b=bb['constraint-potential'],maximum_overlap=float(selection.electronic_criteria.maximum_determinant_overlap),
                        soc_imaginary=soc)
                except ValueError as error:
                    row['findings'] = (str(error),)
                    continue
                coupling = computed['orthogonal_spin_free_coupling_hartree' if pair.coupling == 'SPIN_FREE'
                    else 'orthogonal_spin_orbit_coupling_hartree']
                h2 = abs(coupling)**2
                defect = computed['directional_hamiltonian_defect_hartree']
                if Fraction(defect) > Fraction(selection.electronic_criteria.maximum_directional_defect_hartree):
                    row['findings'] = ('DIRECTIONAL_CDFT_HAMILTONIANS_DISAGREE',)
                if pair.coupling == 'SPIN_ORBIT_SINGLET_TRIPLET_MULTIPLET':
                    donor_triplet = next(p for p in prototypes if p.electronic.state.state_id == pair.donor_state_id
                        ).electronic.state.spin_multiplicity == 3
                    singlet,triplet = (bb,aa) if donor_triplet else (aa,bb)
                    singlet_id,triplet_id = ((pair.acceptor_state_id,pair.donor_state_id) if donor_triplet
                        else (pair.donor_state_id,pair.acceptor_state_id))
                    try:
                        multiplet = singlet_triplet_spin_orbit(overlap=aa['ao-overlap'],
                            singlet_coefficients=singlet['mo-coefficients'],singlet_occupations=singlet['mo-occupations'],
                            triplet_coefficients=triplet['mo-coefficients'],triplet_occupations=triplet['mo-occupations'],
                            soc_imaginary=soc,donor_is_triplet=donor_triplet,
                            singlet_spin_square_excess=reports[singlet_id]['electronic_assessment']['spin_square_excess'],
                            triplet_spin_square_excess=reports[triplet_id]['electronic_assessment']['spin_square_excess'])
                    except ValueError as error:
                        # Authenticated but unsupported determinants are a
                        # scientific adverse row, not permission to discard
                        # a configuration or repeat its native acquisition.
                        row['findings'] += ('SPIN_MULTIPLET_COMPLETION_UNSUPPORTED: '+str(error),)
                        continue
                    amplitudes = multiplet.pop('singlet_bra_amplitudes_hartree')
                    row['spin_multiplet'] = dict(multiplet,
                        singlet_bra_amplitudes_real_imag_hartree=tuple((v.real,v.imag) for v in amplitudes))
                    h2 = multiplet['coupling_squared_hartree2']
                    error = multiplet['relative_coupling_squared_error_bound']
                    if error is None or Fraction(error) > Fraction(pair.maximum_relative_spin_completion_error):
                        row['findings'] += ('SPIN_MULTIPLET_COMPLETION_ERROR_EXCEEDS_SELECTION',)
                row['complete'] = not row['findings'] and all(reports[s]['complete'] for s in (pair.donor_state_id,pair.acceptor_state_id))
                values[(pair.pair_id,trace.trace_id)][ordinal-1] = (a['energy'],b['energy'],b['energy']-a['energy'],
                    computed['orthogonal_energy_gap_hartree'],coupling.real,coupling.imag,h2,
                    b['velocity_gradient']-a['velocity_gradient'],abs(computed['determinant_overlap']),defect,
                    reports[pair.donor_state_id]['electronic_assessment']['spin_square_excess'],
                    reports[pair.acceptor_state_id]['electronic_assessment']['spin_square_excess'])
                support[(pair.pair_id,trace.trace_id)][ordinal-1] = row['complete']
            census[trace.trace_id]['observed_frames'][str(ordinal)] = dict(states=reports,pairs=pair_reports)

        try:
            for name,raw in files:
                if name in native_names:
                    original_native[native_names[name]] = _json(raw)
                match = _SAMPLE.fullmatch(name)
                if match is None:
                    continue
                ordinal = int(match[1])
                if ordinal != current:
                    if current is not None:
                        reduce_frame(current,group)
                    current,group,retained = ordinal,{},0
                retained += len(raw)
                if retained > selection.electronic_criteria.maximum_workspace_bytes:
                    raise ValueError('original frame matrices exceed the complete selected read workspace')
                group[name] = raw
            if current is not None:
                reduce_frame(current,group)
        finally:
            for _ in files:
                pass
            files.close()
    estimates, arrays, points, energy_conversions = {}, dict(projected), {}, {}
    for pair in selection.pairs:
        traces = tuple(t for t in selection.equilibrium.traces if t.ensemble_id == pair.ensemble_id)
        data = np.concatenate([values[(pair.pair_id,t.trace_id)] for t in traces])
        supported = np.concatenate([support[(pair.pair_id,t.trace_id)] for t in traces])
        points[pair.pair_id] = (data,supported)
        arrays[pair.pair_id+'.original_points'] = np.where(np.isfinite(data),data,0.)
        arrays[pair.pair_id+'.original_point_available'] = np.isfinite(data)
        arrays[pair.pair_id+'.supported'] = supported
        w = projected.get(pair.ensemble_id+'.target_weights')
        if w is None or len(w) != len(data):
            estimates[pair.pair_id] = dict(primary_rate_per_second=None,selected_golden_rule_criteria='UNEVALUABLE',
                missing=('COMPLETE_ORIGINAL_EQUILIBRIUM_POPULATION_UNAVAILABLE',))
            continue
        conversions = {f['hartree_kj_mol'] for (trace_id,_),f in frames.items() if trace_id in {t.trace_id for t in traces}}
        if len(conversions) != 1:
            raise ValueError('electronic ensemble changes its original common energy unit')
        energy_conversions[pair.ensemble_id] = next(iter(conversions))
        by_trace = {s.trace_id:s for s in sources}
        intervals = tuple(float(Fraction(by_trace[t.trace_id].config.selection.settings.dynamics.step_seconds)
            *by_trace[t.trace_id].config.selection.settings.sample_interval_steps) for t in traces)
        estimates[pair.pair_id] = reduce_electronic_pair(pair=pair,weights=w,gaps=data[:,2],
            coupling_squared=data[:,6],gap_speeds=data[:,7],point_supported=supported,
            trace_counts=tuple(len(values[(pair.pair_id,t.trace_id)]) for t in traces),
            sample_intervals_seconds=intervals,hartree_kj_mol=next(iter(conversions)),
            unbiased_gap_dynamics=all(by_trace[t.trace_id].config.selection.window is None for t in traces))
    joint,joint_arrays = joint_electronic_analysis(rule=selection,equilibrium=equilibrium,
        projected=projected,points=points,point_estimates=estimates,energy_conversions=energy_conversions)
    arrays.update(joint_arrays)
    for array in arrays.values():
        array.setflags(write=False)
    report = dict(selection=selection.identity.to_document(),assessor_source=assessor_source.to_document(),
        capacity=capacity,equilibrium=equilibrium,original_trace_census=census,pair_columns=PAIR_COLUMNS,pairs=estimates,joint=joint,
        assigned_points=sum(s.config.selection.settings.expected_samples*len(s.config.selection.observations.prototypes) for s in sources),
        complete_pair_configurations=sum(int(a.sum()) for a in support.values()),
        original_cost_scope='PRIMARY_TRACE_AND_EACH_COLD_VERTICAL_POINT_WITH_COMPLETE_PARENT_ELAPSED_COST',
        physical_spin_admission='UNEVALUABLE',physical_rate_admission='UNEVALUABLE',new_native_calls=0,
        evidence_scope=selection.scope)
    recheck_reweighting_originals(sources)
    return report,arrays
