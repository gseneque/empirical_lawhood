# SPDX-License-Identifier: MPL-2.0
"""Explicit local GPU observation at resource admission, never discovery."""

import csv
from dataclasses import dataclass
from io import StringIO
import os
import re
import shutil

from empirical_lawhood.execution.local.bounded_process import run_bounded_command


@dataclass(frozen=True, slots=True)
class CudaDeviceObservation:
    physical_index: int
    uuid: str
    total_memory_bytes: int
    free_memory_bytes: int
    compute_capability: str
    name: str
    driver_version: str


def parse_cuda_devices(raw: bytes, *, visible_devices: str | None):
    """Resolve CUDA's ordered explicit device selection against an actual census."""
    rows = []
    for values in csv.reader(StringIO(raw.decode("utf-8"))):
        if not values:
            continue
        if len(values) != 7:
            raise ValueError("GPU device observation has an incomplete field census")
        index, uuid, total, free, capability, name, driver = (v.strip() for v in values)
        if (not index.isdecimal() or not uuid.startswith("GPU-")
                or not total.isdecimal() or not free.isdecimal()
                or not 0 <= int(free) <= int(total) or int(total) == 0
                or re.fullmatch(r"[1-9][0-9]*\.[0-9]+", capability) is None
                or not name or not driver):
            raise ValueError("GPU device observation contains unsupported or invalid device fields")
        rows.append(CudaDeviceObservation(int(index), uuid, int(total)*2**20,
            int(free)*2**20, capability, name, driver))
    if len({r.uuid for r in rows}) != len(rows) or len({r.physical_index for r in rows}) != len(rows):
        raise ValueError("GPU device observation repeats a device")
    if visible_devices is None:
        return tuple(rows)
    if visible_devices in ("", "-1"):
        return ()
    selected = []
    for value in visible_devices.split(","):
        matches = [r for r in rows if (str(r.physical_index) == value
                   or value.startswith("GPU-") and r.uuid.startswith(value))]
        if len(matches) != 1 or matches[0] in selected:
            raise ValueError("CUDA_VISIBLE_DEVICES does not select unique observed whole GPUs")
        selected.append(matches[0])
    return tuple(selected)


def observe_cuda_devices():
    """Read available GPU capacity only when an actual GPU task requests it."""
    executable = shutil.which("nvidia-smi")
    if executable is None:
        raise RuntimeError("GPU device observation requires nvidia-smi on the selected host")
    result = run_bounded_command((executable,
        "--query-gpu=index,uuid,memory.total,memory.free,compute_cap,name,driver_version",
        "--format=csv,noheader,nounits"), timeout_seconds=15,
        maximum_stdout_bytes=64*1024, maximum_stderr_bytes=4096)
    if result.returncode:
        raise RuntimeError("GPU device observation failed on the selected host")
    return parse_cuda_devices(result.stdout, visible_devices=os.environ.get("CUDA_VISIBLE_DEVICES"))
