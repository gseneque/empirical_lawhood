# SPDX-License-Identifier: MPL-2.0
"""Portable exposed source operands; no receipts or biological qualification.

The archived scripts are source evidence and are never executed by this loader.
Conditional products are reconstructed by their scientific owners in the test.
"""

from hashlib import sha256
import io
import json
from pathlib import Path
import tarfile

from empirical_lawhood.adapters.methods.rubisco_cycle_constraints import (
    assessment as cycle_assessment,
    contracts,
    recursive_translation as cycle_drafts,
)
from empirical_lawhood.adapters.methods.rubisco_nomination_preparation import (
    contracts as nomination,
    science as nomination_science,
)
from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry import science
from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry.source_manifest import (
    INITIAL_CANDIDATE_IDS,
    SOURCE_MANIFEST,
)
from empirical_lawhood.kernel.decoding import (
    decode_canonical_bytes,
    decode_canonical_record,
)


def source_operands():
    """Authenticate the complete local source census without extracting paths."""
    root = Path(__file__).parent / "fixtures/rubisco/nomination"
    census = json.loads((root / "source-census.json").read_bytes())
    raw = (root / "source-operands.tar.gz").read_bytes()
    if (
        len(raw) != census["archive_bytes"]
        or sha256(raw).hexdigest() != census["archive_sha256"]
        or census["evidence_role"] != "EXPOSED_SOFTWARE_CONFORMANCE_ONLY"
        or census["scientific_qualification"] != "NOT_PERFORMED"
        or census["fresh_independent_units"] != 0
        or census["contains_execution_receipts"]
    ):
        raise ValueError("exposed nomination fixture changes source or evidence role")
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        members = archive.getmembers()
        if (
            len(members) != len(census["members"])
            or {row.name for row in members} != set(census["members"])
            or any(not row.isfile() for row in members)
        ):
            raise ValueError("exposed nomination fixture changes its complete census")
        values = {}
        for member in members:
            selected = census["members"][member.name]
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("exposed nomination fixture omits a regular member")
            payload = stream.read()
            if (
                len(payload) != selected["size_bytes"]
                or sha256(payload).hexdigest() != selected["sha256"]
            ):
                raise ValueError("exposed nomination fixture substitutes source bytes")
            values[member.name] = payload
    return values


def sources():
    """Rebuild exact exposed mechanism and macro records from source operands."""
    operands = source_operands()
    mechanism = contracts.source_audit_from_bytes({
        name: operands["mechanism/" + name]
        for name, _, _ in contracts.SOURCE_MEMBERS
    })
    macro = science.source_audit_from_bytes(
        {
            source_id: operands["macro/" + source_id + "--" + filename]
            for source_id, filename, _, _ in SOURCE_MANIFEST
        },
        candidate_ids=INITIAL_CANDIDATE_IDS,
    )
    return mechanism, macro


def proposal():
    """Keep the complete unentered construct and paired-assay proposal."""
    preparation = decode_canonical_bytes(
        source_operands()["nomination-input.json"],
        nomination.NominationPreparationSource,
        maximum_bytes=None,
    )
    return preparation.source_members, preparation.assay


def nominee():
    """Rederive the exact exposed analytical dossier; no assay or receipt exists.

    Structural input pins this dossier's original fingerprint. Keeping its
    original input and conditional query makes that identity portable without
    weakening the source contract or declaring new qualification.
    """
    mechanism, macro = sources()
    model = cycle_assessment.supply(mechanism)
    query = cycle_drafts.instance_from_source(
        macro,
        instance_id="instance.rubisco-cycle.first-use",
        candidate_ids=("gp.wt", "wilson2017-row17"),
    )
    outcome = cycle_assessment.assess_use(model, macro, query)
    preparation = decode_canonical_bytes(
        source_operands()["nomination-input.json"],
        nomination.NominationPreparationSource,
        maximum_bytes=None,
    )
    return macro, nomination_science.prepare(preparation, macro, outcome)


def mechanistic_source(macro, dossier):
    from empirical_lawhood.adapters.methods.rubisco_insilico_mechanism import (
        science as mechanism,
    )

    operands = source_operands()
    return mechanism.source_from_bytes(
        {name: operands["mechanistic/" + name] for name, *_ in mechanism.SOURCE_MANIFEST},
        macro=macro,
        nomination=dossier,
    )


def structural_source():
    from empirical_lawhood.adapters.methods.rubisco_insilico_structure import (
        contracts as structural,
    )

    operands = source_operands()
    document = json.loads(operands["structural-selection.json"])
    for member in document["value"]["source_members"]:
        member["value"]["raw_utf8"] = operands[member.pop("operand")].decode()
    return decode_canonical_record(document, structural.StructuralSource)
