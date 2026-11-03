# SPDX-License-Identifier: MPL-2.0
"""Complete native operands and selected terminal minimizer evidence.

The progress view is prospective: every callback's ordinal/index/full scalar
args/norm/count, and the last callback's full x/gradient on known return/error.
Intermediate full x/gradient arrays are not selected scientific observations.
No callback requests early stopping. A lost native call remains UNKNOWN.
"""

from contextlib import contextmanager
import json
import math
import os
from pathlib import Path

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as preparation_contracts
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_instrumentation import selected_value, write_full_positions

from . import storage


class TerminalReporterCapture:
    """Bounded current native arrays, full compact progress and immutable terminal."""

    def __init__(self, directory, np):
        self.directory, self.np = Path(directory), np
        self.ordinal = 0
        self.last_x = self.last_gradient = self.last_args = self.last_iteration = None
        self.progress = (self.directory / "minimizer-progress.jsonl").open("x")

    def record(self, iteration, x, gradient, args):
        self.ordinal += 1
        point = self.np.array(x, dtype=self.np.float64, copy=True)
        grad = self.np.array(gradient, dtype=self.np.float64, copy=True)
        # Preserve actual values before an independent finiteness/shape decision.
        norm = 0.0
        for value in grad.flat:
            norm = math.hypot(norm, float(value))
        particles = point.size//3 if point.size and point.size%3 == 0 else 0
        rms = norm/math.sqrt(particles) if particles else float("nan")
        self.last_x, self.last_gradient = point, grad
        self.last_args, self.last_iteration = selected_value(dict(args)), int(iteration)
        row = dict(callback_ordinal=self.ordinal, optimizer_iteration_index=int(iteration),
            full_native_args=self.last_args, x_count=int(point.size), gradient_count=int(grad.size),
            particle_count=int(particles),
            objective_rms_normalization="SQRT_SUM_ALL_3N_OBJECTIVE_COMPONENTS_SQUARED_OVER_N_PARTICLES",
            objective_gradient_rms_kj_mol_nm=selected_value(rms), reporter_requests_early_stop=False)
        self.progress.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n")
        self.progress.flush()
        os.fsync(self.progress.fileno())
        return False

    def finish(self, *, native_returned, error_text):
        self.progress.flush()
        self.progress.close()
        if self.ordinal:
            storage.immutable_file(self.directory / "minimizer-terminal.npz", lambda stream:
                self.np.savez_compressed(stream, x_nm=self.last_x,
                    objective_gradient_kj_mol_nm=self.last_gradient))
        document = dict(native_returned=bool(native_returned), error_text=error_text,
            callback_count=self.ordinal, last_optimizer_iteration_index=self.last_iteration,
            full_last_native_args=self.last_args, reporter_ever_requests_early_stop=False,
            progress_view="ALL_CALLBACK_SCALAR_ROWS_AND_FINAL_FULL_OBJECTIVE_ARRAYS",
            tolerance_kj_mol_nm="10", max_iterations=0,
            objective_rms_normalization="SQRT_SUM_ALL_3N_OBJECTIVE_COMPONENTS_SQUARED_OVER_N_PARTICLES",
            max_iterations_meaning="NATIVE_CONVERGENCE_NO_ITERATION_CEILING")
        storage.immutable_bytes(self.directory / "minimizer-termination.json",
            json.dumps(document,sort_keys=True,separators=(",",":" )).encode()+b"\n")


def materialize_flat_assets(assets, directory):
    """Preserve original identities/paths in a map; copy exact authentic bytes."""
    assets.__post_init__()
    result, mapping = {}, []
    for row in assets.files:
        name = Path(row.evidence.relative_path).name
        if name in result:
            raise ValueError("flat selected model assets duplicate a native filename")
        target = directory / name
        storage.immutable_bytes(target, row.raw_utf8.encode())
        if storage.file_hash(target) != (row.evidence.byte_count,row.evidence.sha256):
            raise ValueError("flat model copy changes original actual bytes")
        result[name] = target
        mapping.append(dict(original_relative_path=row.evidence.relative_path,
            current_filename=name, byte_count=row.evidence.byte_count, sha256=row.evidence.sha256))
    storage.immutable_bytes(directory / "original-asset-materialization-map.json",
        json.dumps(dict(original_assets=preparation_contracts.identity(assets).to_document(), members=mapping),
            sort_keys=True,separators=(",",":" )).encode()+b"\n")
    return result


@contextmanager
def selected_control_instrumentation(native, mm, unit, ledger, directory, np, *, before_materialization=None):
    """Bind domain snapshots around the unchanged selected model operators."""
    originals = (native._materialize, native._context, native._set_configuration,
        mm.LocalEnergyMinimizer.minimize, native._receiver, native._arrays)
    contexts, receiver_states = {}, {}
    sequence = 0

    def raw_json(name, value):
        storage.immutable_bytes(directory / name, json.dumps(value,sort_keys=True,
            separators=(",",":" )).encode()+b"\n")

    def materialize(assets, selected_directory):
        if selected_directory != directory:
            raise ValueError("controlled materialization changes its actual selected raw unit scope")
        if before_materialization is not None:
            before_materialization()
        return materialize_flat_assets(assets,directory)

    def xml(value, kind):
        nonlocal sequence
        sequence += 1
        path = directory / ("controlled-"+kind+"-"+str(sequence).zfill(6)+".xml")
        storage.immutable_bytes(path, mm.XmlSerializer.serialize(value).encode())
        size, digest = storage.file_hash(path)
        return dict(relative_path=path.relative_to(ledger.root).as_posix(),byte_count=size,sha256=digest)

    def state(context, name):
        def realize(value):
            return dict(full_state=xml(value,name))
        return ledger.call("sampling.controlled-full-state",dict(name=name),
            lambda:context.getState(getPositions=True,getVelocities=True,getForces=True,
                getEnergy=True,getParameters=True,enforcePeriodicBox=False),realization=realize)

    def context(mm, selected_ledger, selected_directory, system, integrator, platform_name, properties):
        if selected_ledger is not ledger or selected_directory != directory:
            raise ValueError("controlled context changes actual selected unit/custody")
        system_file, integrator_file = xml(system,"system"), xml(integrator,"integrator")
        request = dict(system=system_file,integrator=integrator_file,platform=platform_name,
            properties=properties,force_groups=integrator.getIntegrationForceGroups(),
            constraint_tolerance=selected_value(integrator.getConstraintTolerance()))
        raw_json("apparatus-"+platform_name.lower()+".json",request)
        def realized(value):
            observed = native._platform_properties(value.getPlatform(),value)
            result = dict(platform=value.getPlatform().getName(),actual_properties=observed)
            raw_json("context-realization-"+str(ledger.counter).zfill(6)+".json",result)
            return result
        result = ledger.call("sampling.context",request,
            lambda:mm.Context(system,integrator,mm.Platform.getPlatformByName(platform_name),properties),
            realization=realized)
        contexts[id(result)] = system, integrator, platform_name, system_file["sha256"]
        actual = json.loads(ledger.calls[-1].realized_json)
        if actual["platform"] != platform_name or any(actual["actual_properties"].get(key) != value for key,value in properties.items()):
            raise ValueError("actual native context differs from selected platform; raw return retained")
        return result

    def set_configuration(selected_ledger, current, box, positions, source_member):
        if selected_ledger is not ledger or id(current) not in contexts:
            raise ValueError("controlled configuration has no actual selected context")
        suffix = str(ledger.counter+1).zfill(6)
        write_full_positions(directory / ("requested-box-"+suffix+".json"),box)
        write_full_positions(directory / ("requested-positions-"+suffix+".json"),positions)
        original = originals[2]
        return original(ledger,current,box,positions,source_member)

    def minimize(current, tolerance, maximum_iterations):
        if id(current) not in contexts or maximum_iterations != 0:
            raise ValueError("controlled minimizer changes actual context/native stopping contract")
        selected_tolerance = float(tolerance.value_in_unit(unit.kilojoule_per_mole/unit.nanometer))
        if selected_tolerance != 10:
            raise ValueError("controlled minimizer changes declared objective tolerance")
        system, integrator, _, _ = contexts[id(current)]
        before = state(current,"pre-minimizer-full-state")
        xml(before,"selected-pre-minimizer-state")
        raw_json("declared-system-constraints.json",dict(constraints=tuple(
            dict(left=int(system.getConstraintParameters(index)[0]),
                right=int(system.getConstraintParameters(index)[1]),
                distance_nm=str(system.getConstraintParameters(index)[2].value_in_unit(unit.nanometer)))
            for index in range(system.getNumConstraints())),
            integration_force_groups=integrator.getIntegrationForceGroups(),
            constraint_tolerance=str(integrator.getConstraintTolerance())))
        capture = TerminalReporterCapture(directory,np)
        class Reporter(mm.MinimizationReporter):
            def report(self, iteration, x, gradient, args):
                return capture.record(iteration,x,gradient,args)
        import traceback
        try:
            reporter = ledger.call("sampling.minimizer-reporter",dict(early_stop=False),lambda:Reporter())
        except Exception:
            capture.finish(native_returned=False,error_text=traceback.format_exc())
            raise
        requested = dict(tolerance_kj_mol_nm="10",max_iterations=0,reporter_early_stop=False,
            system=xml(system,"minimizer-system"),integrator=xml(integrator,"minimizer-integrator"))
        raw_json("minimizer-apparatus.json",requested)
        def actual_minimize():
            returned, error = False, None
            try:
                result = originals[3](current,tolerance,maximum_iterations,reporter)
                returned = True
                return result
            except BaseException:
                error = traceback.format_exc()
                raise
            finally:
                capture.finish(native_returned=returned,error_text=error)
        result = ledger.call("sampling.effective-chemical-minimization",requested,actual_minimize)
        state(current,"post-minimizer-full-state")
        return result

    def receiver(mm, selected_ledger, current, selected_directory, name, **keywords):
        result = originals[4](mm,selected_ledger,current,selected_directory,name,**keywords)
        if id(current) not in contexts or selected_ledger is not ledger:
            raise ValueError("force receiver has no actual selected context")
        if name in ("minimized", "cpu-force-reference"):
            _, integrator, platform, system_sha = contexts[id(current)]
            receiver_states[platform] = result, system_sha, integrator.getIntegrationForceGroups()
        return result

    def arrays(path, **values):
        if Path(path).name == "independent-force-receivers.npz":
            cuda, cpu = receiver_states["CUDA"], receiver_states["CPU"]
            values = dict(values, cuda_box_vectors_nm=np.asarray(cuda[0].getPeriodicBoxVectors(
                asNumpy=True).value_in_unit(unit.nanometer),dtype=np.float64),
                cpu_box_vectors_nm=np.asarray(cpu[0].getPeriodicBoxVectors(
                    asNumpy=True).value_in_unit(unit.nanometer),dtype=np.float64),
                cuda_system_xml_sha256=np.array(cuda[1]),cpu_system_xml_sha256=np.array(cpu[1]),
                cuda_integration_force_groups=np.array(cuda[2]),cpu_integration_force_groups=np.array(cpu[2]),
                common_relaxed_state_sha256=np.array(storage.file_hash(directory/"minimized.xml")[1]))
        return originals[5](path,**values)

    native._materialize, native._context, native._set_configuration = materialize, context, set_configuration
    mm.LocalEnergyMinimizer.minimize = minimize
    native._receiver, native._arrays = receiver, arrays
    try:
        yield
    finally:
        (native._materialize, native._context, native._set_configuration,
            mm.LocalEnergyMinimizer.minimize, native._receiver, native._arrays) = originals
