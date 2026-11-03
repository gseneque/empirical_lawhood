# SPDX-License-Identifier: MPL-2.0
"""Measured complete typed transport, independent of any scientific warrant."""

import json
import subprocess
import sys


def test_complete_representative_typed_custody_and_relocated_replay(tmp_path):
    result = subprocess.run((sys.executable, "-m", "tests.recursive_typed_custody_probe",
        str(tmp_path / "selected")), capture_output=True, text=True, check=True)
    report = json.loads(result.stdout)
    assert report["evidence_role"] == "EXPOSED_TYPED_CUSTODY_CONFORMANCE_ONLY"
    assert report["native_contact_count"] == report["fresh_independent_units"] == 0
    assert report["scientific_qualification"] == "NOT_PERFORMED"
    assert report["complete_typed_product_count"] == report["recovered_typed_product_count"] == 17
    assert report["repeated_recovered_typed_product_count"] == 17
    assert report["total_complete_typed_reads"] == 51
    assert set(report["populations"]) == {"battery", "rubisco", "material", "matrix", "sparse-biological"}
    assert report["populations"]["battery"]["complete_receiver_rows"] == 50001
    assert report["populations"]["sparse-biological"]["complete_nonzero_count"] == 2000000
    assert report["complete_serialized_bytes"] > 32 * 1024**2
    assert report["sparse_source_bytes"] > 16 * 1024**2
    # Replaying each complete cohort must reuse the largest operand working
    # set. The measured constructor high-water remains explicit in the report.
    # This adds no operational RAM limit and removes no scientific rows.
    assert report["replay_incremental_peak_rss_bytes"] < 2 * report["maximum_serialized_member_bytes"]
    assert report["scientific_joint_assessment_memory"] == "NOT_ESTABLISHED"
