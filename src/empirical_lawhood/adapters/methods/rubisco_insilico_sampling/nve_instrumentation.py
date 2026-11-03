# SPDX-License-Identifier: MPL-2.0
"""All eleven actual full States/checkpoints before further integration."""
from contextlib import contextmanager
import json
import os

from . import storage
from .control_instrumentation import selected_control_instrumentation


class NVEProgress:
    def __init__(self,directory,root,unit):
        self.directory,self.root,self.unit=directory,root,unit
        self.ordinal=0
        self.stream=(directory/'nve-progress.jsonl').open('x')

    def record(self,*,name,state,steps,checkpoint):
        from .control_science import state_force_energy_from_xml
        raw=(self.directory/(name+'.xml')).read_bytes()
        state_force_energy_from_xml(raw)
        def member(path):
            size,digest=storage.file_hash(path)
            return dict(relative_path=path.relative_to(self.root).as_posix(),byte_count=size,sha256=digest)
        self.ordinal+=1
        row=dict(receiver_ordinal=self.ordinal,name=name,steps=int(steps),time_picosecond=str(storage._clock(state)),
            potential_kj_mol=float(state.getPotentialEnergy().value_in_unit(self.unit.kilojoule_per_mole)),
            kinetic_kj_mol=float(state.getKineticEnergy().value_in_unit(self.unit.kilojoule_per_mole)),
            total_energy_kj_mol=float((state.getPotentialEnergy()+state.getKineticEnergy()).value_in_unit(self.unit.kilojoule_per_mole)),
            full_state=member(self.directory/(name+'.xml')),checkpoint=member(checkpoint))
        self.stream.write(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n')
        self.stream.flush()
        os.fsync(self.stream.fileno())

    def close(self):
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.stream.close()


@contextmanager
def selected_nve_instrumentation(native,mm,unit,ledger,directory,np):
    # Reuse the settled domain apparatus/complete setter snapshots. No chemical
    # minimizer or materializer is called by the existing _nve_case operator.
    with selected_control_instrumentation(native,mm,unit,ledger,directory,np):
        receiver=native._receiver
        progress=NVEProgress(directory,ledger.root,unit)
        try:
            def full_receiver(selected_mm,selected_ledger,context,selected_directory,name,**keywords):
                if (selected_ledger is not ledger or selected_directory!=directory
                        or name not in ('initial-full-state',*('nve-state-'+str(i).zfill(2) for i in range(1,11)))):
                    raise ValueError('NVE receiver changes declared complete eleven-state window')
                # Full scientific arrays are retained, including requested
                # velocities/forces and the selected Context global clock.
                result=receiver(selected_mm,selected_ledger,context,selected_directory,name,
                    positions=True,velocities=True,forces=True)
                path=directory/('nve-checkpoint-'+str(progress.ordinal).zfill(2)+'.bin')
                ledger.call('sampling.nve-full-checkpoint',dict(receiver=name,steps=int(context.getStepCount()),
                    time_picosecond=str(storage._clock(result))),context.createCheckpoint,
                    realization=lambda payload:retain_checkpoint(path,payload))
                progress.record(name=name,state=result,steps=context.getStepCount(),checkpoint=path)
                return result
            native._receiver=full_receiver
            yield
        finally:
            native._receiver=receiver
            progress.close()


def retain_checkpoint(path,payload):
    if type(payload) is not bytes or not payload:raise ValueError('NVE checkpoint omits actual opaque state')
    storage.immutable_bytes(path,payload)
    size,digest=storage.file_hash(path)
    return dict(byte_count=size,sha256=digest)


