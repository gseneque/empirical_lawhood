# SPDX-License-Identifier: MPL-2.0
"""A subprocess measures complete streamed custody, not scientific success."""

import json
import subprocess
import sys


def test_complete_large_opaque_custody_has_bounded_working_memory(tmp_path):
    result = subprocess.run((sys.executable, "-m", "tests.recursive_custody_memory_probe",
                             str(tmp_path / "selected")), capture_output=True, text=True, check=True)
    report = json.loads(result.stdout)
    assert report["evidence_role"] == "EXPOSED_CUSTODY_ONLY_NO_TYPED_SCIENCE"
    assert report["complete_member_count"] == 4
    assert report["complete_payload_bytes"] > 128 * 1024**2
    assert report["retained_decoded_scientific_records"] == 0
    assert report["complete_streamed_copy_count"] == report["complete_member_count"]
    assert len(report["member_census"]) == report["complete_member_count"]
    assert report["additional_peak_rss_bytes"] < 64 * 1024**2
