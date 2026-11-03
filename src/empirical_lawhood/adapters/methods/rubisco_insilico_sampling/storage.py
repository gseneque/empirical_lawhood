# SPDX-License-Identifier: MPL-2.0
"""Complete ordered file custody and native RNG checkpoints, without ceilings.

Adapted from the source-bound M1v6 checkpoint/cursor design. Native state,
software, hardware, source, model and actual clocks remain joined. The former
archive/resource/atom limits and monolithic base64 capsules are not adopted.
"""

import ctypes
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
import math
import os
import gzip
import resource
import time
import traceback
from pathlib import Path
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord

from . import contracts as c
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p


def file_hash(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("native member is not a regular selected file")
    before = path.stat()
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            digest.update(chunk)
    after = path.stat()
    if (before.st_size,before.st_ino,before.st_mtime_ns) != (after.st_size,after.st_ino,after.st_mtime_ns):
        raise ValueError("native member changed during complete authentication")
    return after.st_size,digest.hexdigest()


def member(path, root, role):
    size,digest = file_hash(path)
    relative = path.relative_to(root).as_posix()
    return c.NativeMember("member."+sha256(relative.encode()).hexdigest(),relative,size,digest,role)


def complete_census(root):
    rows = []
    for path in sorted(Path(root).rglob("*")):
        if path.is_symlink():
            raise ValueError("selected native output contains a symlink")
        if path.is_file():
            rows.append(member(path,Path(root),"COMPLETE_NATIVE_ATTEMPT_MEMBER"))
        elif not path.is_dir():
            raise ValueError("native output contains an unretained special file")
    return tuple(rows)


def verify_view(rows, root, *, prefix=""):
    """Verify exact raw members at a current, explicitly selected portable view.

    Absolute producing-workdir strings are never consulted. A caller supplies
    the imported current custody root/prefix after authenticating its parent.
    """
    root = Path(root)
    for row in rows:
        row.__post_init__()
        relative = Path(prefix)/row.relative_path
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("portable native view escapes authenticated parent")
        path = root/relative
        if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink():
            raise ValueError("portable native member escapes current parent")
        if file_hash(path) != (row.size_bytes,row.sha256):
            raise ValueError("portable native member size/SHA substitution")
    return True


def immutable_file(path, writer):
    """Exclusive final names retain failed partial bytes rather than replacing.

    All callers use fresh monotonically numbered members in selected custody.
    A process crash leaves its named partial file for the complete census.
    """
    path = Path(path)
    if any(p.is_symlink() for p in (path.parent, *path.parent.parents)):
        raise ValueError("immutable native output traverses a link")
    partial = path.with_name(path.name+".partial")
    with partial.open("xb") as stream:
        writer(stream)
        stream.flush()
        os.fsync(stream.fileno())
    _publish_partial(path,partial)


def _publish_partial(path,partial):
    library = ctypes.CDLL(None, use_errno=True)
    rename = library.renameat2
    rename.argtypes = (ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint)
    rename.restype = ctypes.c_int
    if rename(-100,os.fsencode(partial),-100,os.fsencode(path),1):
        error=ctypes.get_errno()
        raise OSError(error,os.strerror(error),str(path))
    descriptor=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def immutable_bytes(path, payload):
    immutable_file(path, lambda stream: stream.write(payload))


def verify_portable_view(view, product):
    view.__post_init__()
    if view.owning_product != c.identity(product) or view.members != product.complete_members:
        raise ValueError("portable native view changes its receipted product/member identity")
    return verify_view(view.members, view.custody_root, prefix=view.native_relative_prefix)


def view_member_path(view, relative_path):
    matches = [r for r in view.members if r.relative_path == relative_path]
    if len(matches) != 1:
        raise ValueError("native receiver is absent from complete parent byte census")
    verify_view(tuple(matches), view.custody_root, prefix=view.native_relative_prefix)
    return Path(view.custody_root)/view.native_relative_prefix/relative_path


@dataclass(frozen=True, slots=True)
class CheckpointCursor(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/checkpoint-cursor"
    product_id: str
    source: ObjectIdentity
    model_assets: ObjectIdentity
    trajectory_id: str
    hardware_sha256: str
    system_sha256: str
    integrator_sha256: str
    global_steps: int
    global_time_picosecond: Decimal
    production_steps: int
    coordinate_frames: int
    observable_frames: int
    checkpoint: c.NativeMember
    prior_checkpoint: ObjectIdentity | None


def _clock(state):
    quantity=state.getTime()
    if str(quantity.unit)!="picosecond":
        raise ValueError("native checkpoint changes pinned global time unit")
    return Decimal(str(quantity.value_in_unit(quantity.unit)))


def save_checkpoint(context, directory, source, assets, trajectory_id, hardware,
                    system_sha256, integrator_sha256, production_steps,
                    coordinate_frames, observable_frames, sequence, prior=None,
                    *,census_root=None,native_call=None):
    """Retain actual opaque RNG state and a separate observed cursor."""
    path = Path(directory)/("checkpoint-"+str(sequence).zfill(8)+".bin")
    call=native_call or (lambda role,request,function:function())
    immutable_bytes(path,call("sampling.create-checkpoint",{},context.createCheckpoint))
    state = call("sampling.checkpoint-clock-receiver",{},context.getState)
    # Context time is returned in the pinned native picosecond unit.
    clock = _clock(state)
    record = CheckpointCursor("checkpoint."+trajectory_id+"."+str(sequence),
                              c.identity(source),assets,trajectory_id,hardware,
                              system_sha256,integrator_sha256,int(context.getStepCount()),
                              clock,production_steps,coordinate_frames,observable_frames,
                              member(path,Path(directory) if census_root is None else Path(census_root),"OPAQUE_NATIVE_RNG_AND_FULL_STATE"),
                              c.identity(prior) if prior is not None else None)
    immutable_bytes(Path(directory)/("checkpoint-"+str(sequence).zfill(8)+".json"),record.canonical_bytes())
    return record


class StreamCallLedger:
    """Full native call rows on disk, with only segment summaries in products.

    All nested rows remain retained. Expense sums include top-level rows once;
    the enclosing registered attempt still owns actual total service expense.
    """
    def __init__(self,root,model_id,*,counter=0):
        self.root=Path(root)
        self.model_id=model_id
        self.counter=counter
        self.current_parent=None
        self.segments=[]
        self._raw=self._stream=None

    def open_segment(self,path):
        if self._stream is not None:
            raise ValueError("native ledger segment is already open")
        self.path=Path(path)
        self.partial=self.path.with_name(self.path.name+".partial")
        self._raw=self.partial.open("xb")
        self._stream=gzip.GzipFile(fileobj=self._raw,mode="wb",mtime=0)
        self._counts=[0,0,0]
        self._first=self._last=None
        self._wall=self._cpu=Decimal(0)

    def call(self,role,request,function,*,realization=None,files=()):
        if self._stream is None:
            raise ValueError("native call has no selected retained ledger segment")
        self.counter+=1
        call_id="native-call."+str(self.counter).zfill(10)
        parent=self.current_parent
        self.current_parent=call_id
        wall,cpu=time.perf_counter(),time.process_time()
        before=resource.getrusage(resource.RUSAGE_CHILDREN)
        termination,error,realized="COMPLETED",None,{}
        try:
            value=function()
            if realization is not None:
                realized=realization(value)
            return value
        except BaseException:
            termination,error="TECHNICAL_FAILURE",traceback.format_exc()
            raise
        finally:
            after=resource.getrusage(resource.RUSAGE_CHILDREN)
            elapsed=Decimal(str(time.perf_counter()-wall))
            expense=Decimal(str(time.process_time()-cpu+after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime))
            row=p.NativeCall(call_id,parent,self.model_id,role,json.dumps(request,sort_keys=True,separators=(",",":"),default=str),json.dumps(realized,sort_keys=True,separators=(",",":"),default=str),elapsed,expense,termination,error,tuple(files))
            self.current_parent=parent
            self._stream.write(row.canonical_bytes()+b"\n")
            self._stream.flush()
            self._raw.flush()
            self._counts[0]+=1
            self._counts[1 if termination=="COMPLETED" else 2]+=1
            self._first=self._first or call_id
            self._last=call_id
            if parent is None:
                self._wall+=elapsed;self._cpu+=expense

    def close_segment(self):
        self._stream.close()
        self._raw.flush();os.fsync(self._raw.fileno());self._raw.close()
        self._stream=self._raw=None
        _publish_partial(self.path,self.partial)
        row=c.NativeLedgerSegment(member(self.path,self.root,"COMPLETE_ORDERED_NATIVE_CALL_LEDGER"),*self._counts,self._first,self._last,self._wall,self._cpu)
        self.segments.append(row)
        return row


def ledger_rows(path):
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    with gzip.open(path,"rb") as stream:
        for row in stream:
            yield decode_canonical_bytes(row.rstrip(b"\n"),p.NativeCall,maximum_bytes=None)


def restore_checkpoint(context, cursor, source, assets, hardware, system_sha256,
                       integrator_sha256, current_view):
    """Actual continuation requires identical declared model/software/hardware.

    Native checkpoint restoration is not a fresh ensemble or a task receipt.
    The enclosing registered operation still needs an actual authorized parent.
    """
    if (cursor.source != c.identity(source) or cursor.model_assets != assets or
        cursor.hardware_sha256 != hardware or cursor.system_sha256 != system_sha256 or
        cursor.integrator_sha256 != integrator_sha256):
        raise ValueError("native continuation substitutes source/model/hardware")
    verify_view((cursor.checkpoint,),current_view)
    payload=(Path(current_view)/cursor.checkpoint.relative_path).read_bytes()
    context.loadCheckpoint(payload)
    actual = _clock(context.getState())
    if context.getStepCount()!=cursor.global_steps or not math.isclose(float(actual),float(cursor.global_time_picosecond),rel_tol=1e-9,abs_tol=1e-7):
        raise ValueError("native continuation changes actual step/global clock")
    # The exact restored RNG capsule is retained and independently compared.
    if context.createCheckpoint()!=payload:
        raise ValueError("native checkpoint does not restore exact opaque RNG/state")
    return dict(actual_steps=context.getStepCount(),actual_time_picosecond=str(actual),
                checkpoint_sha256=sha256(payload).hexdigest())


def json_lines(path):
    """Consume all ordered rows; an invalid partial final row stays a failure."""
    with Path(path).open("r",encoding="utf8") as stream:
        for number,line in enumerate(stream,1):
            try:
                yield json.loads(line)
            except ValueError as error:
                raise ValueError(f"native observation row {number} is incomplete") from error
