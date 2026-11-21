# SPDX-License-Identifier: MPL-2.0
"""Unrestrained complete-reference relaxation inside the shared native boundary."""

from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.active_model_assessment import assess_catalytic_seed
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_selection import ActiveRelaxationSettings
from empirical_lawhood.domains.rubisco.rubisco_response.active_state_geometry import expand_state_coordinates
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_native import GRADIENT_UNIT
from empirical_lawhood.adapters.rubisco.rubisco_response.fixed_coordinate_mm import COULOMB_KJ_NM_PER_MOL_E2


class InvalidRelaxationGeometry(ValueError):
    """A nonfinite trial cannot enter an electronic calculation."""


def checked_reference_evaluation(*, operator, coordinates, shape, observe, label, phase, conversion=None):
    """Retain the original complete reference return and its physical unit check."""
    import numpy as np
    coordinates = np.asarray(coordinates, dtype='<f8').reshape(shape)
    if not np.isfinite(coordinates).all():
        raise InvalidRelaxationGeometry('nonfinite-reference-relaxation-trial')
    coordinate_sha = sha256(coordinates.tobytes()).hexdigest()
    observe(dict(event='relaxation-entry', evaluation=label, phase=phase,
        coordinate_sha256=coordinate_sha, physical_atoms=len(coordinates)))
    try:
        result = operator.evaluate(coordinates)
        energy = float(result['energy_hartree'])
        gradient = np.asarray(result['gradient_hartree_per_bohr'], dtype='<f8')
        values = (float(result['bohr_angstrom']), float(result['hartree_kj_mol']))
        if (result['gradient_unit'] != GRADIENT_UNIT or values[0] != .52917721092
                or values[1] != COULOMB_KJ_NM_PER_MOL_E2 / (values[0] / 10)
                or not np.isfinite(values).all() or values[1] <= 0
                or gradient.shape != shape or not np.isfinite(gradient).all() or not np.isfinite(energy)
                or conversion is not None and conversion != values):
            raise ValueError('reference relaxation received incomplete arrays or a changed physical unit')
        observe(dict(event='relaxation-return', evaluation=label, phase=phase,
            coordinate_sha256=coordinate_sha, gradient_sha256=sha256(gradient.tobytes()).hexdigest(),
            energy_hartree=energy, gradient_unit=GRADIENT_UNIT,
            maximum_gradient_hartree_per_bohr=float(np.max(np.abs(gradient)))))
        return result, values
    except BaseException as error:
        observe(dict(event='relaxation-error', evaluation=label, phase=phase,
            coordinate_sha256=coordinate_sha, error_type=type(error).__name__, error=str(error)))
        raise


def minimize_reference_geometry(*, operator, initial_angstrom, settings, observe, geometry_guard=None):
    """Use complete reference gradients in the existing limited-memory minimizer.

    There is no iteration, evaluation or wall-time ceiling. The minimizer has
    its existing numerical line-search/resolution stops. It adds no restraints,
    artificial masses, thermostat, clock rescaling or inferred state weights.
    """
    import numpy as np
    from empirical_lawhood.domains.rubisco.rubisco_response.geometry_domain_minimizer import minimize_geometry
    exact(settings, ActiveRelaxationSettings)
    xyz = np.asarray(initial_angstrom, dtype='<f8')
    if xyz.ndim != 2 or xyz.shape[1] != 3 or not len(xyz) or not np.isfinite(xyz).all() or not callable(observe):
        raise ValueError('reference relaxation requires complete finite coordinates and an actual observer')
    calls = 0
    conversion = None

    def evaluate(coordinates, phase):
        nonlocal calls, conversion
        coordinates = np.asarray(coordinates, dtype='<f8').reshape(xyz.shape)
        if not np.isfinite(coordinates).all():
            raise InvalidRelaxationGeometry('nonfinite-reference-relaxation-trial')
        if geometry_guard is not None:
            geometry_guard(coordinates)
        calls += 1
        result, conversion = checked_reference_evaluation(operator=operator, coordinates=coordinates,
            shape=xyz.shape, observe=observe, label=calls, phase=phase, conversion=conversion)
        return result

    def objective(flat_nm):
        trial = np.asarray(flat_nm).reshape(xyz.shape)*10
        if calls == 0 and np.array_equal(np.asarray(flat_nm).reshape(xyz.shape), xyz/10):
            trial = xyz
        result = evaluate(trial, 'minimizer')
        bohr, hartree = conversion
        # dE/dx_nm = dE/dx_Bohr * (10 / Bohr_A) * Hartree_kJ/mol.
        return (float(result['energy_hartree'])*hartree,
            (np.asarray(result['gradient_hartree_per_bohr'])*hartree*10/bohr).reshape(-1))

    result = minimize_geometry(objective, (xyz/10).reshape(-1), violation_type=InvalidRelaxationGeometry,
        maximum_gradient=float(settings.maximum_gradient_kj_mol_nm), maximum_iterations=None,
        maximum_evaluations=None, callback=lambda row: observe(dict(event='accepted-minimizer-step', **row)))
    final_xyz = np.asarray(result.x, dtype='<f8').reshape(xyz.shape)*10
    final = evaluate(final_xyz, 'final-endpoint-force')
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality import gradient_statistics
    summary = dict(optimizer_reported_success=bool(result.success), optimizer_reason=str(result.message),
        iterations=int(result.nit), optimizer_evaluations=int(result.nfev), complete_reference_evaluations=calls,
        final_evaluation=calls, gradient_unit=GRADIENT_UNIT, bohr_angstrom=conversion[0], hartree_kj_mol=conversion[1],
        maximum_final_gradient_kj_mol_nm=float(np.max(np.abs(final['gradient_hartree_per_bohr'])))*conversion[1]*10/conversion[0],
        maximum_gradient_selection_kj_mol_nm=str(settings.maximum_gradient_kj_mol_nm),
        initial_energy_kj_mol=float(result.initial_energy_kj_mol), final_energy_hartree=float(final['energy_hartree']),
        physical_atom_count=len(xyz), optimizer_settings=result.settings, added_restraints=False,
        molecular_time_seconds=None, equilibrium_population='UNEVALUABLE', rate_admission='UNEVALUABLE',
        final_gradient_statistics=gradient_statistics(final['gradient_hartree_per_bohr'], unit=GRADIENT_UNIT,
            bohr_angstrom=conversion[0], hartree_kj_mol=conversion[1]))
    return final_xyz, final, summary


def execute_active_relaxation(*, representation, site, protocol, seed, prototype,
                              settings, coordinate_bytes, topology_path, directory,
                              prefix_selection=None, model_name=None, configuration=None, continuation=None):
    """Build the selected operator and retain original endpoint arrays before assessment."""
    import numpy as np
    if prefix_selection is not None:
        from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_selection import ActivePreparationPrefixSelection
        from empirical_lawhood.science.identity.provenance import ObjectIdentity
        exact(prefix_selection, ActivePreparationPrefixSelection)
        exact(configuration, ObjectIdentity)
        if prefix_selection.conditional.state_census != ((site.path.reactive_site_id, seed.state_label, seed.water_occupancy),):
            raise ValueError('preparation prefix changes its single prospective chemical case')
        allowance = prefix_selection.allowance_for(model_name)
    elif model_name is not None or configuration is not None or continuation is not None:
        raise ValueError('full relaxation cannot carry undeclared preparation-prefix selections')
    root = Path(directory)
    topology = Path(topology_path)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir() or any(root.iterdir()):
        raise ValueError('active relaxation requires its fresh absolute native work directory')
    if (not topology.is_absolute() or topology.is_symlink()
            or sha256(topology.read_bytes()).hexdigest() != representation.raw_topology.object_fingerprint):
        raise ValueError('active relaxation substitutes its complete original topology')
    assessment = assess_catalytic_seed(representation=representation, site=site, protocol=protocol,
        seed=seed, coordinate_bytes=coordinate_bytes, cell=prototype.cell)
    if assessment.disposition != 'SATISFIED':
        raise ValueError('active relaxation seed has independent construction findings: '+repr(assessment.findings))
    xyz = expand_state_coordinates(seed, coordinate_bytes)
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality import bound_geometry_terms, assess_molecular_geometry
    raw_topology = topology.read_bytes()
    geometry_terms = bound_geometry_terms(representation, raw_topology)
    with (root/'original.prmtop').open('xb') as stream:
        stream.write(raw_topology)
    def geometry_report(coordinates):
        return assess_molecular_geometry(coordinates, geometry_terms,
            policy=prototype.molecular.geometry_quality, cell_angstrom=tuple(map(float, prototype.cell.lengths_angstrom)),
            exempt_bonded_atoms=site.path.qm_atom_indices)
    initial_quality = geometry_report(xyz)
    (root/'initial-whole-molecule-quality.json').write_text(json.dumps(initial_quality, sort_keys=True, indent=2)+'\n')
    if initial_quality['findings']:
        raise InvalidRelaxationGeometry('initial whole-molecule quality refused: '+repr(initial_quality['findings']))
    for name, record in (('seed.json', seed), ('site.json', site), ('protocol.json', protocol), ('settings.json', settings)):
        with (root/name).open('xb') as stream:
            for chunk in record.canonical_chunks():
                stream.write(chunk)
    if prefix_selection is not None:
        with (root / 'prefix-selection.json').open('xb') as stream:
            for chunk in prefix_selection.canonical_chunks():
                stream.write(chunk)
    with (root/'initial-coordinates-angstrom.npy').open('xb') as stream:
        np.save(stream, xyz, allow_pickle=False)
    bindings = dict(representation=representation.identity.to_document(), prototype=prototype.identity.to_document(),
        topology_sha256=representation.raw_topology.object_fingerprint,
        original_coordinate_sha256=seed.original_coordinate_sha256,
        initial_coordinate_sha256=seed.expanded_coordinate_sha256, physical_atoms=len(xyz),
        cell=prototype.cell.to_document(), state_graph=seed.graph.to_document(),
        other_sites='Original active keto topology and occupancy; focal states are nested views',
        cross_vdw='Original source atom parameters retained; chemical applicability remains unassessed')
    (root/'source-bindings.json').write_text(json.dumps(bindings, sort_keys=True, indent=2)+'\n')
    previous_count = 0
    if continuation is not None:
        from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_continuation import ActivePreparationContinuation, original_configuration
        selected = continuation['continuation']
        exact(selected, ActivePreparationContinuation)
        previous = selected.previous
        if (previous.prefix != prefix_selection or previous.original.model_name != model_name
                or previous.original.prototype != prototype or previous.original.plan.settings != settings
                or original_configuration(previous) != configuration):
            raise ValueError('native preparation continuation changes original state, source or numerical selection')
        previous_count = len(continuation['evaluations'])
        allowance = selected.remaining_allowance
        for name, body in continuation['files'].items():
            if Path(name).parts != (name,):
                raise ValueError('preparation continuation escapes its original native file census')
            with (root / name).open('xb') as stream:
                stream.write(body)
        (root / 'continuation-selection.json').write_bytes(selected.canonical_bytes())
    from empirical_lawhood.domains.rubisco.rubisco_response import periodic_mm_remainder as coupling, periodic_images as images
    from empirical_lawhood.adapters.rubisco.rubisco_response import pyscf_periodic_electronic as electronic
    from empirical_lawhood.adapters.rubisco.rubisco_response.periodic_qmmm import PeriodicCoupledOperator, build_periodic_amber_system
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_operator_options
    log_mode = 'x' if continuation is None else 'a'
    with (root/'native-observations.jsonl').open(log_mode, buffering=1) as native_log, (root/'relaxation-evaluations.jsonl').open(log_mode, buffering=1) as relaxation_log:
        def native_observe(row):
            if previous_count and 'evaluation' in row:
                row = dict(row, evaluation=row['evaluation'] + previous_count)
            native_log.write(json.dumps(row, sort_keys=True, allow_nan=True)+'\n')
        def observe(row):
            relaxation_log.write(json.dumps(row, sort_keys=True, allow_nan=True)+'\n')
            from empirical_lawhood.adapters.rubisco.progress import observe_native_progress
            observe_native_progress(row)
        def geometry_guard(coordinates):
            quality = geometry_report(coordinates)
            if quality['findings']:
                observe(dict(event='geometry-trial-refused',
                    coordinate_sha256=sha256(np.asarray(coordinates, dtype='<f8').tobytes()).hexdigest(),
                    findings=quality['findings'], metrics=quality['metrics'], native_contact=False))
                raise InvalidRelaxationGeometry('whole-molecule quality refused before reference evaluation')
        original, scales, assignment = build_periodic_amber_system(representation=representation,
            cell=prototype.cell, settings=prototype.molecular, topology_path=topology, output_directory=root)
        operator = PeriodicCoupledOperator(representation=representation, selection=site.path,
            settings=prototype.electronic, cell=prototype.cell, original_system=original,
            source_scee=scales, coupling=coupling, images=images, electronic=electronic, observe=native_observe,
            reuse_converged_density=prototype.electronic.ks_flavour == 'RKS',
            **periodic_operator_options(prototype.engine))
        try:
            (root/'coupling-audit.json').write_text(json.dumps(dict(original_assignment=assignment,
                remainder=operator.remainder_audit, embedding=operator.embedding_audit), sort_keys=True, indent=2, allow_nan=False)+'\n')
            if prefix_selection is not None:
                from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_checkpoint import prepare_checkpoint, publish_checkpoint_files
                from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_evaluation import publish_evaluation_files
                from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_native import minimize_reference_prefix
                pins = dict(configuration=configuration, seed=seed.identity, prototype=prototype.identity)
                def retain_evaluation(number, coordinates, returned):
                    return publish_evaluation_files(root, number=number, coordinates=coordinates,
                        result=returned, **pins)
                def retain_checkpoint(state, number, coordinates, returned):
                    record, arrays = prepare_checkpoint(state=state, native_coordinates=coordinates,
                        native_result=returned, native_evaluation=number, **pins)
                    seal = root / f'accepted-{state.iterations:08d}.json'
                    if seal.exists():
                        if seal.read_bytes() != record.canonical_bytes():
                            raise ValueError('preparation continuation changes a sealed original optimizer state')
                    else:
                        publish_checkpoint_files(root, record, arrays)
                returned = minimize_reference_prefix(operator=operator, initial_angstrom=xyz,
                    settings=settings, complete_return_allowance=allowance, observe=observe,
                    retain_evaluation=retain_evaluation, retain_checkpoint=retain_checkpoint,
                    geometry_guard=geometry_guard,
                    resume_state=None if continuation is None else continuation['state'],
                    original_evaluations=() if continuation is None else continuation['evaluations'])
                summary = returned['summary']
                if summary['complete_reference_evaluations'] != operator.evaluations + previous_count:
                    raise ValueError('preparation prefix loses actual complete native evaluations')
                (root / 'preparation-prefix-summary.json').write_text(
                    json.dumps(summary, sort_keys=True, indent=2, allow_nan=False) + '\n')
                return summary
            final_xyz, final, summary = minimize_reference_geometry(operator=operator, initial_angstrom=xyz,
                settings=settings, observe=observe, geometry_guard=geometry_guard)
            for name, value in (('final-coordinates-angstrom.npy', final_xyz),
                    ('final-gradient-hartree-per-bohr.npy', final['gradient_hartree_per_bohr']),
                    ('final-energy-hartree.npy', np.asarray(final['energy_hartree']))):
                with (root/name).open('xb') as stream:
                    np.save(stream, value, allow_pickle=False)
            if summary['complete_reference_evaluations'] != operator.evaluations:
                raise ValueError('relaxation loses actual nested reference evaluations')
            (root/'relaxation-summary.json').write_text(json.dumps(summary, sort_keys=True, indent=2, allow_nan=False)+'\n')
            return summary
        finally:
            del operator
