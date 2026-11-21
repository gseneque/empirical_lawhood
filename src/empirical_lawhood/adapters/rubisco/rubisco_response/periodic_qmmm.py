# SPDX-License-Identifier: MPL-2.0
"""Candidate full periodic electrostatic QM/MM operator.

The registered caller owns actual source, model, resource and native admission.
These numerical objects are not receipts or scientific qualification. Imports
of electronic and molecular engines occur only at explicit construction.
"""

from decimal import Decimal
import gc
from hashlib import sha256
import math
import time

from empirical_lawhood.adapters.rubisco.rubisco_response.fixed_coordinate_mm import COULOMB_KJ_NM_PER_MOL_E2
from empirical_lawhood.science.records.serialization import release_canonical_encodings
from empirical_lawhood.domains.rubisco.rubisco_response.electronic_states import validate_electronic_state
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_force_contracts as contracts


def build_periodic_amber_system(*, representation, cell, settings, topology_path, output_directory):
    """Construct and retain the complete original MM assignment before masking.

    The registered caller owns native entry and the fresh output directory.
    Original parameters are retained before the independent correspondence
    check; a failure keeps those files. No energy kernel or SCF is called.
    """
    import json
    from pathlib import Path
    import openmm as mm
    from openmm import app, unit
    from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.amber_parameters import assigned_census_supported_inactive14, read_prmtop
    from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.physical_preparation_geometry import interaction_partition
    from empirical_lawhood.adapters.rubisco.rubisco_insilico_free_energy.native_coupling import inspect_force_snapshot
    from empirical_lawhood.domains.rubisco.rubisco_response.amber_mm_assignment import assess_amber_force_assignment
    from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation

    exact(representation, MolecularRepresentation)
    exact(cell, contracts.AmberPeriodicCell)
    exact(settings, contracts.PeriodicMMSettings)
    if (cell.raw_topology != representation.raw_topology or cell.raw_coordinates != representation.raw_coordinates
            or cell.physical_atom_count != len(representation.atoms)):
        raise ValueError("periodic MM builder changes its complete original representation/cell selection")
    if settings.cutoff_angstrom >= min(cell.lengths_angstrom)/2:
        raise ValueError("periodic MM cutoff must be below half the shortest original cell edge")
    source, directory = Path(topology_path), Path(output_directory)
    if not source.is_absolute() or not directory.is_absolute() or not directory.is_dir():
        raise ValueError("periodic MM builder requires selected absolute source and existing fresh output paths")
    raw = source.read_bytes()
    if sha256(raw).hexdigest() != representation.raw_topology.object_fingerprint:
        raise ValueError("periodic MM builder substitutes its original topology bytes")
    with (directory/"mm-settings.json").open("xb") as stream:
        stream.write(settings.canonical_bytes())
    topology = app.AmberPrmtopFile(str(source))
    system = topology.createSystem(nonbondedMethod=getattr(app, settings.nonbonded_method),
        nonbondedCutoff=float(settings.cutoff_angstrom)/10*unit.nanometer,
        constraints=None, rigidWater=False, removeCMMotion=False, hydrogenMass=None,
        ewaldErrorTolerance=float(settings.ewald_relative_tolerance))
    del topology
    if (system.getNumParticles() != cell.physical_atom_count or system.getNumConstraints()
            or any(system.isVirtualSite(i) for i in range(system.getNumParticles()))):
        raise ValueError("periodic MM builder changes the unconstrained complete physical atom denominator")
    forces = [f for f in system.getForces() if type(f).__name__ == "NonbondedForce"]
    if len(forces) != 1:
        raise ValueError("periodic MM builder lacks one complete native nonbonded population")
    force = forces[0]
    force.setUseDispersionCorrection(False)
    force.setUseSwitchingFunction(False)
    if (force.getNonbondedMethod() != getattr(mm.NonbondedForce, settings.nonbonded_method)
            or abs(force.getCutoffDistance().value_in_unit(unit.nanometer)*10-float(settings.cutoff_angstrom)) > 1e-12
            or force.getEwaldErrorTolerance() != float(settings.ewald_relative_tolerance)):
        raise ValueError("periodic MM builder changes the selected native numerical convention")
    vectors = tuple(tuple(float(v) for v in row.value_in_unit(unit.nanometer))
        for row in system.getDefaultPeriodicBoxVectors())
    expected = tuple(tuple(float(cell.lengths_angstrom[i])/10 if i == j else 0.0 for j in range(3)) for i in range(3))
    if any(abs(a-b) > 1e-6 for row, target in zip(vectors, expected, strict=True) for a, b in zip(row, target, strict=True)):
        raise ValueError("periodic MM native cell differs from its original assessed Amber box")
    snapshot = inspect_force_snapshot(system, unit=unit)
    masses = tuple(float(system.getParticleMass(i).value_in_unit(unit.dalton)) for i in range(system.getNumParticles()))
    with (directory/"original-mm-parameters.json").open("x") as stream:
        json.dump(dict(snapshot=snapshot, masses=masses, cell_vectors_nm=vectors,
            settings=settings.identity.to_document(), raw_topology_sha256=sha256(raw).hexdigest()),
            stream, allow_nan=False, separators=(",", ":"))
        stream.write("\n")
    assignment = assess_amber_force_assignment(raw, snapshot, masses)
    del snapshot, masses
    sections = read_prmtop(raw.decode("ascii"))
    census = assigned_census_supported_inactive14(sections)
    _, active, _, _ = interaction_partition(sections, census)
    original_box = sections.get("BOX_DIMENSIONS", ())
    if (len(original_box) != 4 or any(abs(a-b) > Decimal("0.00001")
            for a, b in zip(original_box, (Decimal(90), *cell.lengths_angstrom), strict=True))):
        raise ValueError("periodic MM construction substitutes original raw box dimensions")
    source_scee = {pair: values[0] for pair, values in active.items()}
    del sections, census, active
    if source.read_bytes() != raw:
        raise ValueError("periodic MM topology changed during native construction")
    with (directory/"mm-assignment.json").open("x") as stream:
        json.dump(assignment, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    return system, source_scee, assignment


def solve_selected_scf(mf, maximum_cycles, *, observe, evaluation, initial_density=None):
    """Continue the same SCF density until convergence when no ceiling is set.

    PySCF's public kernel takes an integer iteration count. Successive chunks
    retain its returned density and grow without a total iteration ceiling.
    Every original chunk return and every iteration remains observable. A
    chunk return never substitutes for the selected convergence criteria.
    Historical finite selections keep their original single-kernel behavior.
    """
    if maximum_cycles is not None:
        mf.max_cycle = maximum_cycles
        return float(mf.kernel() if initial_density is None else mf.kernel(dm0=initial_density))
    original_callback = mf.callback
    completed_cycles, chunk_cycles, chunk = 0, 50, 0

    def callback(state):
        original_callback({**state, 'cycle': completed_cycles + state['cycle']})

    mf.callback = callback
    try:
        while True:
            chunk += 1
            mf.max_cycle = chunk_cycles
            # The public kernel uses the previous returned orbitals when they
            # exist. Make that continuation explicit at every subsequent chunk.
            guess = initial_density if chunk == 1 else mf.make_rdm1()
            energy = float(mf.kernel() if guess is None else mf.kernel(dm0=guess))
            cycles = mf.cycles
            observe(dict(event='scf-chunk-return', evaluation=evaluation, chunk=chunk,
                cycles=cycles, cumulative_cycles=completed_cycles + cycles,
                converged=bool(mf.converged), energy_hartree=energy, count_ceiling=None))
            if (not math.isfinite(energy) or type(cycles) is not int
                    or not 0 < cycles <= chunk_cycles):
                raise ValueError('SCF continuation returned nonfinite energy or no valid iteration progress')
            if mf.converged:
                return energy
            completed_cycles += cycles
            chunk_cycles *= 2
    finally:
        mf.callback = original_callback


class _PeriodicNumerics:
    """Common Ewald, link, MM-remainder and electronic energy/gradient implementation."""

    def __init__(self, *, settings, original_system, source_scee, charges, qm, mm_indices, links,
                     bonds, numbers, qm_charge, multiplicity, lengths, coupling, images, electronic,
                     observe, reuse_converged_density, accelerated_compute, device_memory_bytes,
                     molecular_platform, host_memory_bytes, capture_electronic_state):
        """Bind the numerical kernel after its caller has checked the source and atom partition."""
        import numpy as np
        import openmm as mm
        from openmm import unit
        from pyscf import dft, gto
        from pyscf.lib import param
        from empirical_lawhood.adapters.rubisco.progress import progress_observer
        if type(reuse_converged_density) is not bool:
            raise ValueError('density reuse requires an explicit Boolean selection')
        if type(accelerated_compute) is not bool:
            raise TypeError('accelerated_compute requires a boolean')
        if not accelerated_compute and device_memory_bytes is not None:
            raise ValueError('device memory cannot be selected for the non-accelerated operator')
        if host_memory_bytes is not None and (not accelerated_compute or type(host_memory_bytes) is not int
                or host_memory_bytes <= 0):
            raise ValueError('an explicit host-memory allocation requires a supported accelerated selection')
        if molecular_platform is not None and (not accelerated_compute or molecular_platform not in ('CUDA', 'Reference')):
            raise ValueError('an explicit molecular platform requires a supported accelerated selection')
        if not callable(observe):
            raise ValueError("an actual attempt observer is required before native construction")
        if settings.ks_flavour == "RKS" and multiplicity != 1:
            raise ValueError("restricted closed-shell KS cannot represent the selected nonzero spin")
        self.np, self.mm, self.unit, self.gto, self.dft = np, mm, unit, gto, dft
        self.coupling, self.images, self.electronic = coupling, images, electronic
        self.settings, self.observe = settings, progress_observer(observe)
        self.physical_count = original_system.getNumParticles()
        self.qm_charge, self.multiplicity = qm_charge, multiplicity
        self.numbers = list(numbers) + [1]*len(links)
        self.qm, self.mm_indices, self.links = qm, mm_indices, links
        self.gpu_backend = None
        if accelerated_compute:
            from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_backend import GpuPeriodicBackend
            self.gpu_backend = GpuPeriodicBackend(device_memory_bytes=device_memory_bytes, observe=observe,
                molecular_platform=molecular_platform or 'CUDA',
                **({'host_memory_bytes':host_memory_bytes} if host_memory_bytes is not None else {}))
            self.dft = self.gpu_backend.dft
        cuts = tuple(sorted((q, m) for q, m, _ in self.links))
        shifted, self.embedding_audit = coupling.shifted_embedding_charges(charges, self.qm, bonds, cuts)
        self.embedding = np.asarray(shifted)[list(self.mm_indices)]
        from empirical_lawhood.adapters.rubisco.rubisco_response.periodic_mm_remainder import periodic_mm_remainder
        self.remainder, self.remainder_audit = periodic_mm_remainder(
            original_system, self.qm, source_scee, mm=mm, unit=unit)
        self.lattice = np.asarray([vector.value_in_unit(unit.nanometer)
                                   for vector in original_system.getDefaultPeriodicBoxVectors()])*10
        if (self.lattice.shape != (3, 3) or not np.array_equal(self.lattice, np.diag(np.diag(self.lattice)))
                or np.any(np.diag(self.lattice) <= 0)
                or float(settings.real_cutoff_angstrom) >= min(np.diag(self.lattice))):
            raise ValueError("the selected kernel requires an orthorhombic cell and real cutoff below its shortest edge")
        if np.max(np.abs(np.diag(self.lattice)-np.asarray(tuple(float(v) for v in lengths)))) > 1e-5:
            raise ValueError("native MM cell differs from its independently read original source cell")
        self.bohr_angstrom = float(param.BOHR)
        self.gradient_unit = "Eh/PySCF-Bohr-0.52917721092-A"
        if self.bohr_angstrom != float(Decimal("0.52917721092")):
            raise ValueError("periodic supplier changes its explicitly selected native Bohr convention")
        self.bohr_nm = self.bohr_angstrom/10
        # Match the installed electronic coordinate unit and the actual MM
        # Coulomb coefficient. This makes the point-charge coupling consistent.
        self.hartree_kj_mol = COULOMB_KJ_NM_PER_MOL_E2/self.bohr_nm
        self.integrator = mm.VerletIntegrator(0.0005)
        self.context = (mm.Context(self.remainder, self.integrator, mm.Platform.getPlatformByName('Reference'))
            if self.gpu_backend is None else self.gpu_backend.openmm_context(self.remainder, self.integrator, mm))
        if self.gpu_backend is None:
            self.observe(dict(event='compute-backend', accelerated_compute=False,
                backend='pyscf.periodic-direct.openmm-reference', gpu_devices=0))
        self.evaluations = 0
        self.reuse_converged_density = reuse_converged_density
        self._converged_density_guess = None
        self.capture_electronic_state = capture_electronic_state

    def close(self):
        """Release this operation's native context, integrator and retained density."""
        self.context = None
        self.integrator = None
        self._converged_density_guess = None

    def evaluate(self, coordinates_angstrom, *, density_seed=None, density_bytes=None,
                 spin_trial_density=None, capture_numerical_state=None):
        """Electronic solution and complete unrestrained E/G at one geometry.

        SCF convergence, basis/field accuracy and physical model validation are
        separate. Every attempt is observed, including a failure before return.
        Optional density reuse is confined to this fixed operator and a previous
        complete successful evaluation. Each geometry builds fresh potentials.
        """
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_memory import memory_observation
        from empirical_lawhood.adapters.rubisco.rubisco_response.pyscf_periodic_dft import MemoryBoundedNumInt, bind_bounded_gradient
        from empirical_lawhood.adapters.rubisco.rubisco_response.pyscf_periodic_jk import bind_bounded_jk, bind_bounded_jk_gradient
        from empirical_lawhood.adapters.rubisco.rubisco_response.pyscf_periodic_diis import bind_checked_diis
        if self.context is None:
            raise ValueError("periodic evaluation requires an active native context")
        np, unit = self.np, self.unit
        gpu = getattr(self, 'gpu_backend', None)
        norm = np.linalg.norm if gpu is None else gpu.norm
        host = np.asarray if gpu is None else gpu.to_host
        settings, selection = self.settings, self.selection
        reuse = getattr(self, 'reuse_converged_density', False)
        previous = getattr(self, '_converged_density_guess', None) if reuse else None
        self._converged_density_guess = None
        seeded = density_seed is not None or density_bytes is not None
        if seeded and self.selection is None:
            raise ValueError("electronic checkpoint reuse requires its complete original path and cell")
        if capture_numerical_state is not None and not callable(capture_numerical_state):
            raise TypeError("a numerical-state consumer must be callable")
        if spin_trial_density is not None and (settings.ks_flavour != 'UKS' or seeded or reuse
                or type(settings) is contracts.ConstrainedPeriodicForceSettings):
            raise ValueError("a competing spin density requires an independent cold UKS surface")
        if seeded and (self.evaluations != 0 or reuse):
            raise ValueError('checkpoint density requires one new evaluation without previous-density reuse')
        xyz = np.asarray(coordinates_angstrom, dtype=float)
        if xyz.shape != (self.physical_count, 3) or not np.isfinite(xyz).all():
            raise ValueError("coupled evaluation requires all finite physical coordinates in native order")
        qxyz, jacobians = self.coupling.linked_qm_coordinates(xyz, self.qm, self.links)
        field, image_shifts = self.images.localize_periodic_field(qxyz, xyz[list(self.mm_indices)], self.lattice)
        center = qxyz.mean(axis=0)
        radius = float(np.max(np.linalg.norm(qxyz-center, axis=1)))
        translations = np.asarray([(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1)
                                   for c in (-1, 0, 1) if (a, b, c) != (0, 0, 0)]) @ self.lattice
        image_distance = float(np.min(np.linalg.norm(qxyz[:, None, :]+translations[None, :, :]-center, axis=2)))
        if not radius < float(settings.direct_field_cutoff_angstrom) < image_distance:
            raise ValueError("direct field must include every complete QM atom and exclude all QM images")
        numbers = self.numbers
        self.evaluations += 1
        label = self.evaluations
        started, cpu = time.monotonic(), time.process_time()
        self.observe(dict(event='entry', evaluation=label, physical_atoms=len(xyz), qm_atoms=len(qxyz),
                          memory=memory_observation(settings.memory_megabytes),
                          qm_radius_angstrom=radius, direct_field_cutoff_angstrom=float(settings.direct_field_cutoff_angstrom)))
        try:
            if gpu is not None:
                gpu.begin()
            if label == 1:
                from empirical_lawhood.execution.resources.process_memory import release_unused_process_memory
                released = release_canonical_encodings(self.representation)
                release_unused_process_memory()
                self.observe(dict(event='record-encoding-release', evaluation=label,
                    released_record_encodings=released,
                    memory=memory_observation(settings.memory_megabytes)))
            else:
                gc.collect()
            mol = self.gto.M(atom=list(zip(numbers, qxyz, strict=True)), unit='Angstrom',
                basis=settings.basis, charge=self.qm_charge,
                spin=self.multiplicity-1, verbose=0)
            density_context = (settings, self.qm_charge, self.multiplicity,
                tuple(numbers), tuple(self.qm), tuple(self.mm_indices), tuple(self.links),
                tuple(int(v) for v in mol.ao_loc_nr()), sha256(self.lattice.tobytes()).hexdigest(),
                sha256(self.embedding.tobytes()).hexdigest())
            initial_density = None
            if previous is not None:
                if previous[2] != density_context:
                    raise ValueError('previous density belongs to a changed fixed operator context')
                initial_density = previous[3]
            if seeded:
                from empirical_lawhood.adapters.rubisco.rubisco_response.periodic_density_seed import density_for_operator
                initial_density, populations = density_for_operator(density_seed, density_bytes, mol=mol,
                    representation=self.representation, path=selection, settings=settings,
                    cell=self.cell, coordinates=xyz)
                self.observe(dict(event='checkpoint-density-validation', evaluation=label,
                    seed=density_seed.identity.to_document(), source_definition=density_seed.source_definition.identity.to_document(),
                    checkpoint_sha256=density_seed.checkpoint.sha256, electron_populations=populations,
                    exact_process_continuation=False, original_completion_claimed=False))
            self.observe(dict(event='scf-initial-density', evaluation=label,
                policy='AUTHENTICATED_CHECKPOINT_DENSITY' if seeded else 'PREVIOUS_SUCCESSFUL_EVALUATION' if reuse else 'COLD_START',
                source_evaluation=previous[0] if previous is not None else None,
                source_coordinate_sha256=previous[1] if previous is not None else None,
                density_sha256=sha256(initial_density.tobytes()).hexdigest() if initial_density is not None else None,
                density_shape=list(initial_density.shape) if initial_density is not None else None))
            constrained = type(settings) is contracts.ConstrainedPeriodicForceSettings
            if constrained:
                from empirical_lawhood.adapters.rubisco.rubisco_response.constrained_electronic_native import build_constrained_mean_field, constraint_residuals, constrained_diagnostics
                base = build_constrained_mean_field(mol, settings.state, gpu=gpu)
                self.observe(dict(event='constrained-state-entry', evaluation=label,
                    state=settings.state.identity.to_document(),
                    upstream='GPU4PYSCF_1.8.1_CDFT_UKS_MINAO_LAGRANGE'))
            else:
                base = getattr(self.dft, settings.ks_flavour)(mol)
            base.xc, base.grids.level = settings.functional, settings.grid_level
            if gpu is None:
                base._numint = MemoryBoundedNumInt(base._numint,
                    memory_megabytes=settings.memory_megabytes,
                    observe=lambda row: self.observe(dict(evaluation=label, **row)))
            else:
                from pyscf.dft.rks import KohnShamDFT
                base.small_rho_cutoff = KohnShamDFT.small_rho_cutoff
                initial_density = gpu.density_to_device(initial_density)
            couple = self.electronic.add_mm_charges if gpu is None else gpu.couple
            mf = couple(base, field, self.lattice, self.embedding,
                rcut_ewald=float(settings.real_cutoff_angstrom),
                rcut_hcore=float(settings.direct_field_cutoff_angstrom), unit='Angstrom')
            mf.mm_mol.mesh = np.asarray(settings.reciprocal_mesh)
            eta, cutoff = float(settings.ewald_eta_inverse_bohr), float(settings.real_cutoff_angstrom)/self.bohr_angstrom
            mf.mm_mol.get_ewald_params = lambda precision=None, rcut=None: (eta, cutoff)
            mf.mm_mol.precision = float(settings.ewald_precision)
            mf.max_memory = mf.mm_mol.max_memory = settings.memory_megabytes
            if gpu is None:
                bind_bounded_jk(mf, memory_megabytes=settings.memory_megabytes,
                    observe=lambda row: self.observe(dict(evaluation=label, **row)))
                bind_checked_diis(mf, observe=lambda row: self.observe(dict(evaluation=label, **row)))
            mf.conv_tol = float(settings.energy_tolerance_hartree)
            mf.conv_tol_grad = float(settings.orbital_gradient_tolerance)
            def convergence(state):
                gradient = mf.get_grad(state['mo_coeff'], state['mo_occ'], state['fock'])
                return (abs(state['e_tot']-state['last_hf_e']) < mf.conv_tol
                        and float(norm(gradient)) < mf.conv_tol_grad
                        and (not constrained or max(abs(v) for v in constraint_residuals(mf,
                            mf.make_rdm1(state['mo_coeff'], state['mo_occ'])))
                            <= float(settings.state.population_tolerance_electrons)))
            def iteration(state):
                self.observe(dict(event='scf-iteration', evaluation=label,
                    memory=memory_observation(settings.memory_megabytes),
                    **{name: float(state[name]) for name in ('cycle', 'e_tot', 'norm_gorb', 'norm_ddm') if name in state}))
            mf.check_convergence, mf.callback = convergence, iteration
            self.observe(dict(event='scf-entry', evaluation=label,
                memory=memory_observation(settings.memory_megabytes), basis_functions=int(mol.nao)))
            if spin_trial_density is not None:
                trial = np.asarray(spin_trial_density, dtype=float)
                if (trial.shape != (2, mol.nao, mol.nao) or not np.isfinite(trial).all()
                        or not np.allclose(trial, trial.transpose(0, 2, 1), atol=1e-10, rtol=0)):
                    raise ValueError("spin trial must contain two finite symmetric original-basis density matrices")
                overlap = mol.intor_symmetric('int1e_ovlp')
                if not np.allclose(np.einsum('aij,ji->a', trial, overlap), mol.nelec, rtol=0, atol=1e-6):
                    raise ValueError("spin trial changes the selected electron populations")
                initial_density = gpu.density_to_device(trial) if gpu is not None else trial
            eqm = solve_selected_scf(mf, settings.maximum_scf_cycles, observe=self.observe,
                evaluation=label, initial_density=initial_density)
            # GPU get_grad requires its explicit Fock operand. For CDFT this
            # also retains the selected Lagrangian's population potential.
            explicit_fock = gpu is not None or constrained
            final_fock = mf.get_fock(dm=mf.make_rdm1(), cycle=-1) if explicit_fock else None
            residual = float(norm(mf.get_grad(mf.mo_coeff, mf.mo_occ, final_fock))) if explicit_fock else float(
                norm(mf.get_grad(mf.mo_coeff, mf.mo_occ)))
            self.observe(dict(event='electronic-return', evaluation=label, converged=bool(mf.converged),
                              memory=memory_observation(settings.memory_megabytes),
                              energy_hartree=eqm, orbital_gradient_norm=residual, basis_functions=int(mol.nao)))
            if not mf.converged or not math.isfinite(eqm) or not math.isfinite(residual) or residual >= mf.conv_tol_grad:
                raise ValueError("electronic solution did not satisfy the selected energy and orbital criteria")
            if constrained:
                diagnostics = constrained_diagnostics(mf, state=settings.state)
                self.observe(dict(event='constrained-state-return', evaluation=label, **diagnostics))
                if self.capture_electronic_state is not None:
                    self.capture_electronic_state(mf, gpu, label, diagnostics)
                if max(abs(v) for v in diagnostics['residual_electrons']) > float(settings.state.population_tolerance_electrons):
                    raise ValueError('electronic return violates the selected charge/spin population constraints')
            derivative = mf.nuc_grad_method() if gpu is None else gpu.gradient(mf)
            derivative.grid_response = True
            if gpu is None:
                bind_bounded_gradient(derivative, unrestricted=settings.ks_flavour == 'UKS')
                bind_bounded_jk_gradient(derivative, memory_megabytes=settings.memory_megabytes,
                    observe=lambda row: self.observe(dict(evaluation=label, **row)))
            self.observe(dict(event='qm-gradient-entry', evaluation=label,
                memory=memory_observation(settings.memory_megabytes)))
            gq = host(derivative.kernel())
            self.observe(dict(event='qm-gradient-return', evaluation=label,
                memory=memory_observation(settings.memory_megabytes)))
            ge = host(derivative.grad_hcore_mm(mf.make_rdm1()) + derivative.grad_nuc_mm() + derivative.de_ewald_mm)
            self.observe(dict(event='embedding-gradient-return', evaluation=label,
                memory=memory_observation(settings.memory_megabytes)))
            self.context.setPositions(xyz/10*unit.nanometer)
            state = self.context.getState(getEnergy=True, getForces=True)
            emm = state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)/self.hartree_kj_mol
            gmm = -state.getForces(asNumpy=True).value_in_unit(unit.kilojoule_per_mole/unit.nanometer)*self.bohr_nm/self.hartree_kj_mol
            if np.shape(ge) != (len(self.mm_indices), 3) or not np.isfinite(ge).all() or not np.isfinite(gmm).all():
                raise ValueError("native electronic or MM return omits a finite complete gradient")
            projected = self.coupling.pullback_qm_gradient(len(xyz), self.qm, gq, jacobians)
            total = gmm + projected
            total[list(self.mm_indices)] += ge
            energy = float(eqm+emm)
            if not math.isfinite(energy) or not np.isfinite(total).all():
                raise ValueError("coupled native return contains nonfinite energy or gradients")
            result = dict(energy_hartree=energy, gradient_hartree_per_bohr=total,
                qm_energy_hartree=eqm, mm_remainder_energy_hartree=float(emm),
                qm_link_gradient_hartree_per_bohr=gq, embedding_mm_gradient_hartree_per_bohr=ge,
                remainder_gradient_hartree_per_bohr=gmm, image_shifts=image_shifts,
                scf_converged=True, orbital_gradient_norm=residual, basis_functions=int(mol.nao),
                net_gradient_norm=float(np.linalg.norm(total.sum(axis=0))),
                bohr_angstrom=self.bohr_angstrom, hartree_kj_mol=self.hartree_kj_mol, gradient_unit=self.gradient_unit)
            successor = None
            if reuse:
                density = np.array(host(mf.make_rdm1()), dtype=float, order='C', copy=True)
                expected_shape = (mol.nao, mol.nao) if settings.ks_flavour == 'RKS' else (2, mol.nao, mol.nao)
                if density.shape != expected_shape or not np.isfinite(density).all():
                    raise ValueError('converged density guess is incomplete or nonfinite')
                density.setflags(write=False)
                successor = (label, sha256(xyz.tobytes()).hexdigest(), density_context, density)
            if capture_numerical_state is not None:
                capture_numerical_state(mf)
            if gpu is not None:
                gpu.finish(evaluation=label, failed=False)
            self.observe(dict(event='return', evaluation=label, energy_hartree=energy,
                memory=memory_observation(settings.memory_megabytes),
                wall_seconds=time.monotonic()-started, process_cpu_seconds=time.process_time()-cpu))
            self._converged_density_guess = successor
            return result
        except BaseException as error:
            self._converged_density_guess = None
            if gpu is not None:
                try:
                    gpu.finish(evaluation=label, failed=True)
                except Exception as observation_error:
                    self.observe(dict(event='gpu-cost-unavailable', evaluation=label,
                        error_type=type(observation_error).__name__, error=str(observation_error)))
            self.observe(dict(event='error', evaluation=label, error_type=type(error).__name__, error=str(error),
                wall_seconds=time.monotonic()-started, process_cpu_seconds=time.process_time()-cpu))
            raise


class PeriodicCoupledOperator(_PeriodicNumerics):
    """One fixed atom partition and cell; every call returns a complete gradient."""

    def __init__(self, *, representation, selection, settings, cell, original_system, source_scee,
                 coupling, images, electronic, observe, reuse_converged_density=False,
                 accelerated_compute=False, device_memory_bytes=None, capture_electronic_state=None,
                 molecular_platform=None, host_memory_bytes=None):
        from empirical_lawhood.domains.rubisco.rubisco_response.catalytic_path_selection import validate_catalytic_path_selection
        from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
        from openmm import unit

        contracts.validate_periodic_force_settings(settings)
        exact(cell, contracts.AmberPeriodicCell)
        validate_catalytic_path_selection(selection, representation)
        if type(settings) is contracts.ConstrainedPeriodicForceSettings:
            validate_electronic_state(settings.state, path=selection, representation=representation)
            if not accelerated_compute or reuse_converged_density:
                raise ValueError('constrained surfaces require the explicit GPU backend and cold UKS selection')
        if capture_electronic_state is not None and not callable(capture_electronic_state):
            raise TypeError('electronic-state capture requires an actual native record sink')
        if (cell.raw_topology != representation.raw_topology or cell.raw_coordinates != representation.raw_coordinates
                or cell.physical_atom_count != len(representation.atoms)):
            raise ValueError("periodic cell substitutes the selected complete molecular representation")
        if original_system.getNumParticles() != len(representation.atoms):
            raise ValueError("original MM system changes the complete physical atom denominator")
        nonbonded = [f for f in original_system.getForces() if type(f).__name__ == 'NonbondedForce']
        if len(nonbonded) != 1:
            raise ValueError("one complete original MM nonbonded population is required")
        charges = tuple(nonbonded[0].getParticleParameters(i)[0].value_in_unit(unit.elementary_charge)
                        for i in range(len(representation.atoms)))
        for i, atom in enumerate(representation.atoms):
            mass = original_system.getParticleMass(i).value_in_unit(unit.dalton)
            if (abs(mass-float(atom.mass_dalton)) > 1e-8
                    or abs(charges[i]-float(atom.charge_electron)) > 1e-10):
                raise ValueError("native MM parameters change a complete physical mass or source charge")
        self.representation, self.selection, self.cell = representation, selection, cell
        super().__init__(settings=settings, original_system=original_system, source_scee=source_scee,
            charges=charges, qm=selection.qm_atom_indices, mm_indices=selection.mm_atom_indices,
            links=tuple((b.qm_atom_index, b.mm_atom_index, float(b.link_distance_angstrom)) for b in selection.boundaries),
            bonds=tuple((b.first, b.second) for b in representation.bonds),
            numbers=tuple(representation.atoms[i].atomic_number for i in selection.qm_atom_indices),
            qm_charge=selection.qm_formal_charge, multiplicity=selection.spin_multiplicity,
            lengths=cell.lengths_angstrom, coupling=coupling, images=images, electronic=electronic, observe=observe,
            reuse_converged_density=reuse_converged_density, accelerated_compute=accelerated_compute,
            device_memory_bytes=device_memory_bytes, molecular_platform=molecular_platform,
            host_memory_bytes=host_memory_bytes, capture_electronic_state=capture_electronic_state)


class ObservedCorePeriodicOperator(_PeriodicNumerics):
    """Periodic force for the selected native observed-core partition and Amber system."""

    def __init__(self, *, partition, settings, original_system, source_scee, observe,
                 accelerated_compute=False, device_memory_bytes=None, molecular_platform=None, host_memory_bytes=None):
        from openmm import unit
        from empirical_lawhood.adapters.rubisco.rubisco_response import pyscf_periodic_electronic
        from empirical_lawhood.domains.rubisco.rubisco_response import periodic_images, periodic_mm_remainder
        from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
        from empirical_lawhood.domains.rubisco.rubisco_response.observed_core_partition import ObservedCorePartition

        exact(partition, ObservedCorePartition)
        exact(settings, contracts.PeriodicForceSettings)
        if not callable(observe):
            raise ValueError("observed core requires its selected native operation observer")
        count = len(partition.atomic_numbers)
        if (original_system.getNumParticles() != count or original_system.getNumConstraints()
                or any(original_system.isVirtualSite(i) for i in range(count))):
            raise ValueError("observed periodic system changes the complete unconstrained atom population")
        forces = [f for f in original_system.getForces() if type(f).__name__ == "NonbondedForce"]
        if len(forces) != 1 or forces[0].getNumParticles() != count:
            raise ValueError("observed core requires one original nonbonded parameter population")
        nb = forces[0]
        if (nb.getNonbondedMethod() != nb.PME or nb.getUseDispersionCorrection() or nb.getUseSwitchingFunction()
                or abs(nb.getCutoffDistance().value_in_unit(unit.nanometer)-1.0) > 1e-12
                or abs(nb.getEwaldErrorTolerance()-1e-4) > 1e-12):
            raise ValueError("observed core changes the declared native periodic convention")
        charges = tuple(nb.getParticleParameters(i)[0].value_in_unit(unit.elementary_charge) for i in range(count))
        for i, (mass, charge) in enumerate(zip(partition.masses_dalton, partition.charges_electron, strict=True)):
            if (abs(original_system.getParticleMass(i).value_in_unit(unit.dalton) - mass) > 1e-8
                    or abs(charges[i] - charge) > 1e-10):
                raise ValueError("observed core changes original source masses or charges")
        qm = partition.qm_atom_indices
        selected = set(qm)
        self.representation = partition
        self.selection = self.cell = None
        super().__init__(settings=settings, original_system=original_system, source_scee=source_scee,
            charges=charges, qm=qm, mm_indices=tuple(i for i in range(count) if i not in selected),
            links=partition.links, bonds=partition.bonds, numbers=tuple(partition.atomic_numbers[i] for i in qm),
            qm_charge=partition.qm_formal_charge, multiplicity=partition.spin_multiplicity,
            lengths=partition.lengths_angstrom, coupling=periodic_mm_remainder, images=periodic_images,
            electronic=pyscf_periodic_electronic, observe=observe, reuse_converged_density=False,
            accelerated_compute=accelerated_compute, device_memory_bytes=device_memory_bytes,
            molecular_platform=molecular_platform, host_memory_bytes=host_memory_bytes, capture_electronic_state=None)
