# SPDX-License-Identifier: MPL-2.0
"""Complete exposed programme report for portable projection checks.

This loader reads repository fixtures only. Historical receipts identify the
exposed products; they grant no execution, resume or scientific authority.
"""

import gzip
from hashlib import sha256
import json
from pathlib import Path


_REPORT_BYTES = 15_545_913
_REPORT_SHA256 = "8185d5711018e7752481a5c08a657a46b71bab8392ec45cb2623c3b7abd4dfbd"
_CENSUS_SHA256 = "9a8976f80569c91c064c3acba739450b8b088837c72fc97c2b35b18bf2d4d2dd"


def programme_report():
    """Authenticate exact report bytes, the complete census and receipt joins."""
    root = Path(__file__).parent / "fixtures/rubisco/candidate-programme"
    census_raw = (root / "report-census.json").read_bytes()
    if sha256(census_raw).hexdigest() != _CENSUS_SHA256:
        raise ValueError("exposed programme fixture changes its provenance census")
    census = json.loads(census_raw)
    compressed = (root / "programme-report.json.gz").read_bytes()
    if (
        len(compressed) != census["archive_bytes"]
        or sha256(compressed).hexdigest() != census["archive_sha256"]
        or census["evidence_role"] != "EXPOSED_SOFTWARE_CONFORMANCE_ONLY"
        or census["scientific_qualification"] != "NOT_PERFORMED"
        or census["fresh_independent_units"] != 0
        or census["native_operations_performed_for_fixture"] != 0
        or census["report_thinned"]
    ):
        raise ValueError("exposed programme fixture changes bytes or evidence role")
    raw = gzip.decompress(compressed)
    if (
        len(raw) != _REPORT_BYTES
        or len(raw) != census["report_bytes"]
        or sha256(raw).hexdigest() != _REPORT_SHA256
        or sha256(raw).hexdigest() != census["report_sha256"]
    ):
        raise ValueError("exposed programme fixture substitutes or thins the report")
    report = json.loads(raw)
    custody = census["retained_custody_census"]
    members = custody["members"]
    if (
        len(members) != custody["member_count"]
        or sum(row["bytes"] for row in members.values()) != custody["member_bytes"]
        or members != report["tmpfs_census"]["members"]
        or members != report["durable_complete_census"]["members"]
        or set(census["retained_receipt_joins"]) != set(report["waves"])
    ):
        raise ValueError("exposed programme fixture loses its complete custody census")
    for name, join in census["retained_receipt_joins"].items():
        wave = report["waves"][name]
        receipt_raw = join["receipt_canonical_utf8"].encode()
        manifest_raw = join["receipt_manifest_canonical_utf8"].encode()
        for path, payload in (
            (join["receipt_path"], receipt_raw),
            (join["receipt_manifest_path"], manifest_raw),
        ):
            if members[path] != {
                "bytes": len(payload), "sha256": sha256(payload).hexdigest()
            }:
                raise ValueError("exposed programme fixture changes a retained receipt")
        receipt = json.loads(receipt_raw)
        manifest = json.loads(manifest_raw)
        attempt = join["attempt_id"]
        identity = wave["receipt_identities"][attempt]
        if (
            sha256(receipt_raw).hexdigest() != identity["value"]["object_fingerprint"]
            or receipt["value"]["receipt_id"] != identity["value"]["object_id"]
            or receipt["value"]["attempt_id"] != attempt
            or wave["measured_event"]["value"]["receipt"] != identity
            or manifest["value"]["logical"]["value"]["content_sha256"]
            != identity["value"]["object_fingerprint"]
            or join["product_index"] != wave["report"]["retained_product_index"]
        ):
            raise ValueError("exposed programme fixture changes a receipt/product join")
        for product in join["product_index"]:
            document = wave["report"]["terminal_products"][product["task_id"]][
                product["output_id"]
            ]
            payload = (
                json.dumps(
                    document, sort_keys=True, separators=(",", ":"),
                    ensure_ascii=True, allow_nan=False,
                ) + "\n"
            ).encode()
            if (
                len(payload) != product["size_bytes"]
                or sha256(payload).hexdigest() != product["sha256"]
                or product["producing_receipt"] != identity
                or members[product["relative_path"]]
                != {"bytes": len(payload), "sha256": sha256(payload).hexdigest()}
            ):
                raise ValueError("exposed programme fixture substitutes a complete product")
    return report
