# SPDX-License-Identifier: MPL-2.0
"""Authenticated local operands for exposed PURE inquiry conformance.

Historical locator strings identify filenames; they are never opened. The
complete nomination archive supplies the original macro and mechanism bytes.
"""

from hashlib import sha256
import json
from pathlib import Path

from tests.rubisco_nomination_fixture import source_operands

from empirical_lawhood.adapters.methods.rubisco_cycle_constraints import contracts
from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry.challenge import (
    YAMORI_BYTES,
    YAMORI_SHA256,
)
from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry.source_manifest import (
    SOURCE_MANIFEST,
)

FIXTURES = Path(__file__).parent / "fixtures"
CANDIDATE_MANIFEST_SHA256 = "17dcdd2ed789cca72be619b2e12bd4f16728a351ad547b4f6c3d43c175c9e62d"
YAMORI_CENSUS_SHA256 = "520dbe65ff6664828448ac02a052c9507fc027968e7593aaf4dc9f7501460088"


def candidate_source_operands():
    """Preserve all 22 original caller IDs using exact archive member identities."""
    raw = (FIXTURES / "rubisco_candidate_source_paths.json").read_bytes()
    if sha256(raw).hexdigest() != CANDIDATE_MANIFEST_SHA256:
        raise ValueError("candidate fixture changes its historical caller manifest")
    manifest = json.loads(raw)
    archived = source_operands()
    selected = {}
    for row in manifest["sources"]:
        filename = Path(row["path"]).name
        members = [
            name for name, payload in archived.items()
            if name.startswith("macro/")
            and name.split("--", 1)[-1] == filename
            and len(payload) == row["bytes"]
            and sha256(payload).hexdigest() == row["sha256"]
        ]
        if len(members) != 1 or row["source_id"] in selected:
            raise ValueError("candidate fixture changes its exact source census")
        selected[row["source_id"]] = archived[members[0]]
    if len(selected) != 22:
        raise ValueError("candidate fixture omits its complete source denominator")
    return selected


def portfolio_source_operands(archived=None):
    """Keep the original typed macro source IDs without historical path lookup."""
    archived = source_operands() if archived is None else archived
    return {
        source_id: archived["macro/" + source_id + "--" + filename]
        for source_id, filename, _, _ in SOURCE_MANIFEST
    }


def successor_source_operands():
    """Return the exact Wilson article and GenBank parent for caller-owned IDs."""
    archived = source_operands()
    return (
        archived["macro/source.007--wilson2017-jbc.html"],
        archived["macro/source.008--te-MG000148.gb"],
    )


def finalist_source_operands():
    """Reuse macro/mechanism stock and the complete pinned Yamori primary XML."""
    archived = source_operands()
    root = FIXTURES / "rubisco/finalist"
    raw_census = (root / "source-census.json").read_bytes()
    if sha256(raw_census).hexdigest() != YAMORI_CENSUS_SHA256:
        raise ValueError("finalist fixture changes its source census")
    census = json.loads(raw_census)
    member = census["member"]
    if (
        census["evidence_role"] != "EXPOSED_SOFTWARE_CONFORMANCE_ONLY"
        or census["scientific_qualification"] != "NOT_PERFORMED"
        or census["fresh_independent_units"] != 0
        or census["contains_execution_receipts"]
        or member != {
            "path": "yamori2026-primary.xml",
            "size_bytes": YAMORI_BYTES,
            "sha256": YAMORI_SHA256,
        }
    ):
        raise ValueError("finalist fixture changes its source or evidence role")
    yamori = (root / member["path"]).read_bytes()
    if len(yamori) != YAMORI_BYTES or sha256(yamori).hexdigest() != YAMORI_SHA256:
        raise ValueError("finalist fixture substitutes Yamori source bytes")
    mechanism = {
        name: archived["mechanism/" + name]
        for name, _, _ in contracts.SOURCE_MEMBERS
    }
    return portfolio_source_operands(archived), mechanism, yamori
