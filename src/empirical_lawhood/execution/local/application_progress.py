# SPDX-License-Identifier: MPL-2.0
"""A bounded identity companion for the shared operational-progress.v2 file."""

from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.storage.application_invocations import record_bytes, utc_now
from empirical_lawhood.storage.progress import OperationalProgressReporter, read_progress


class ApplicationProgressReporter(OperationalProgressReporter):
    def __init__(self, path, operation, *, store, handle):
        self.store, self.handle, self.sequence = store, handle, 0
        self.binding_sha256 = store.intent(handle)["binding_sha256"]
        super().__init__(path, operation, expected_parent_device=store.identity[0])

    def _install(self, raw):
        self.store.require_current()
        super()._install(raw)
        self.sequence += 1
        value = json.loads(raw)
        self.store.publish(self.handle, "progress", {
            "schema": "empirical-lawhood/application/progress-binding", "version": "1.0.0",
            "handle": self.handle, "binding_sha256": self.binding_sha256,
            "sequence": self.sequence, "observed_utc": value["updated_at_utc"],
            "snapshot_sha256": sha256(record_bytes(value)).hexdigest(),
            "run_id": None, "task_id": value["task_id"], "attempt_id": None,
            "identity_scope": "INVOCATION_AND_REPORTED_TASK;_OTHER_IDENTITIES_UNKNOWN",
            "scientific_authority": "NONE"})


def invocation_progress(store, handle, *, progress_root):
    """Never reconstruct a result or infer completion from an advisory phase."""
    if progress_root is None:
        return {"availability": "NOT_SELECTED", "scientific_authority": "NONE"}
    binding = store._read(store.path(handle) / "progress.json")
    if binding is None:
        return {"availability": "NOT_OBSERVED", "scientific_authority": "NONE"}
    try:
        intent = store.intent(handle)
        if (binding["schema"] != "empirical-lawhood/application/progress-binding" or binding["version"] != "1.0.0"
                or binding["handle"] != handle or binding["binding_sha256"] != intent["binding_sha256"]
                or type(binding["sequence"]) is not int or binding["sequence"] < 1):
            raise ValueError("progress binding changed")
        original = read_progress(Path(progress_root) / (handle + ".json"))
        if (sha256(record_bytes(original)).hexdigest() != binding["snapshot_sha256"]
                or original["operation"] != intent["binding"]["request"]["operation"]):
            return {"availability": "UPDATING_OR_UNBOUND", "scientific_authority": "NONE"}
        age = max(0, (datetime.now(timezone.utc)-datetime.fromisoformat(original["updated_at_utc"])).total_seconds())
        # Decimal wrappers preserve advisory numbers in the application transport;
        # the original strict progress reader and its field set stay unchanged.
        def transport(value):
            if type(value) is float:
                return Decimal(str(value))
            if type(value) is dict:
                return {key: transport(item) for key, item in value.items()}
            if type(value) is list:
                return [transport(item) for item in value]
            return value
        snapshot = transport(original)
        return {"availability": "OBSERVED", "binding": binding, "snapshot": snapshot,
            "read_utc": utc_now(), "age_seconds": Decimal(str(age)), "stale": age > 10,
            "completion_source": "ORIGINAL_RECEIPTS_ONLY", "scientific_authority": "NONE"}
    except (OSError, ValueError, KeyError, TypeError):
        return {"availability": "UNAVAILABLE", "scientific_authority": "NONE"}
