# SPDX-License-Identifier: MPL-2.0
"""Pure source/model admissions; preparation never qualifies dynamics or biology."""

import json

from empirical_lawhood.adapters.methods.rubisco_insilico_structure import contracts as s
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A

from . import contracts as c
from .preparation import controlled_constructs, validate_controlled_constructs

PUBLISHED_MANIFEST_SHA256 = (
    "b3871840a00e58cb3cf9156e81eefe29eb5676f7b1b5c5fdc15563ca8bd46400"
)
STOCK_FILES = (
    (
        "source.1bwv-ph8-pdb",
        "data/systems_for_MD/extant/1bwv/1bwv.ph8.pdb",
        "published",
    ),
    (
        "source.3zxw-ph8-pdb",
        "data/systems_for_MD/extant/3zxw/3zxw.ph8.pdb",
        "published",
    ),
    ("source.cabp-frcmod", "data/systems_for_MD/parameters/cabp.frcmod", "published"),
    ("source.cabp-prepi", "data/systems_for_MD/parameters/cabp.prepi", "published"),
    ("source.engine-inventory", None, "engine-manifest"),
    (
        "source.ff14sb-frcmod",
        "ambertools24-tleap/dat/leap/parm/frcmod.ff14SB",
        "engine",
    ),
    ("source.gaff2-dat", "ambertools24-tleap/dat/leap/parm/gaff2.dat", "engine"),
    ("source.kcx-frcmod", "data/systems_for_MD/parameters/kcx.frcmod", "published"),
    ("source.kcx-prepin", "data/systems_for_MD/parameters/kcx.prepin", "published"),
    ("source.leaprc-gaff2", "ambertools24-tleap/dat/leap/cmd/leaprc.gaff2", "engine"),
    (
        "source.leaprc-protein-ff14sb",
        "ambertools24-tleap/dat/leap/cmd/leaprc.protein.ff14SB",
        "engine",
    ),
    (
        "source.leaprc-water-tip3p",
        "ambertools24-tleap/dat/leap/cmd/leaprc.water.tip3p",
        "engine",
    ),
    ("source.original-1bwv-cif", "1bwv.cif", "original"),
    ("source.original-3zxw-cif", "3zxw.cif", "original"),
    ("source.parm10-dat", "ambertools24-tleap/dat/leap/parm/parm10.dat", "engine"),
    ("source.published-manifest", None, "published-manifest"),
)


def validate_stock(source_members):
    """Join original text to exact archived official/native stock manifests."""
    members = {row.member_id: row for row in source_members}
    if tuple(members) != tuple(row[0] for row in STOCK_FILES):
        raise ValueError("preparation omits/reorders exact source stock")
    for row in source_members:
        row.__post_init__()
    if members["source.engine-inventory"].sha256 != c.ENGINE_INVENTORY_SHA256:
        raise ValueError("preparation substitutes exact installed engine")
    if members["source.published-manifest"].sha256 != PUBLISHED_MANIFEST_SHA256:
        raise ValueError("preparation substitutes original published stock manifest")
    engine = json.loads(members["source.engine-inventory"].raw_utf8)
    published = json.loads(members["source.published-manifest"].raw_utf8)
    if (
        engine["scientific_native_contacts"] != 0
        or published["git_tree"] != "e6c621656ca1a8eb7e09381d6405da5d412274a1"
    ):
        raise ValueError("tool/source preparation receipt changes original meaning")
    expected = {
        "original": dict(s.ORIGINALS),
        "engine": {
            row["path"]: row["sha256"]
            for row in engine["entries"]
            if row["kind"] == "file"
        },
        "published": {row["path"]: row["sha256"] for row in published["members"]},
    }
    for member_id, path, origin in STOCK_FILES:
        if path is not None and members[member_id].sha256 != expected[origin][path]:
            raise ValueError("molecular parameter stock substitutes an original source")
    return {key: row.raw_utf8 for key, row in members.items()}


def _original_sequences(inventory):
    sequences = {}
    for pdb, lsu_length, ssu_length in (("1BWV", 493, 138), ("3ZXW", 475, 118)):
        for name, length in (("lsu", lsu_length), ("ssu", ssu_length)):
            chains = [
                row
                for row in inventory.chains
                if row.pdb_id == pdb and len(row.full_sequence) == length
            ]
            if len(chains) != 8 or len({row.full_sequence for row in chains}) != 1:
                raise ValueError(
                    "preparation changes authentic full eight-chain source roster"
                )
            for row in chains:
                row.__post_init__()
            sequences[pdb.lower() + "." + name] = chains[0].full_sequence
    views = dict(inventory.proposed_sequences)
    originals = dict(
        gp_lsu=sequences["1bwv.lsu"],
        gp_ssu_m1=views["gp.ssu.wt.m1.fasta"],
        gp_ssu_v1=views["gp.ssu.wt.v1.fasta"],
        te_lsu=sequences["3zxw.lsu"],
        te_ssu=sequences["3zxw.ssu"],
    )
    # The declared M/V processing views must preserve the authentic remainder.
    if originals["gp_ssu_m1"][1:] != sequences["1bwv.ssu"][1:]:
        raise ValueError("Gp processing view changes authentic structural sequence")
    return originals


def source_from_inventory(
    inventory, coordinates, nomination, source_members, *, native_workdir
):
    """Build after actual authentic source/nomination results, never a mock receipt."""
    inventory.__post_init__()
    coordinates.__post_init__()
    nomination.__post_init__()
    validate_stock(tuple(source_members))
    if coordinates.inventory != s.identity(
        inventory
    ) or inventory.nomination != c.identity(nomination):
        raise ValueError("coordinate/source inventory changes actual nominal lineage")
    return c.PreparationSelection(
        "input." + c.NAMESPACE + ".preparation",
        s.identity(inventory),
        s.identity(coordinates),
        c.identity(nomination),
        native_workdir,
        c.ENGINE_INVENTORY_SHA256,
        controlled_constructs(**_original_sequences(inventory)),
        tuple(source_members),
    )


def validate_inputs(source, nomination, inventory, coordinates):
    source.__post_init__()
    if (
        c.identity(nomination) != source.nomination
        or s.identity(inventory) != source.structural_inventory
        or s.identity(coordinates) != source.structural_coordinates
        or coordinates.inventory != source.structural_inventory
        or inventory.nomination != source.nomination
    ):
        raise ValueError(
            "preparation substitutes actual source/coordinate/nomination history"
        )
    validate_stock(source.source_members)
    validate_controlled_constructs(source.constructs, _original_sequences(inventory))
    return source


def validate_source(source, nomination, inventory, coordinates):
    return validate_inputs(source, nomination, inventory, coordinates)


def assess_preparation_integrity(source, nomination, inventory, coordinates, preparation, assets):
    """Additive independent raw assignment census; native coverage stays unknown."""
    from types import SimpleNamespace

    from empirical_lawhood.adapters.methods.rubisco_insilico_structure.independent_assessment import (
        original_assembly,
        validate_coordinate_export,
    )

    from .preparation_integrity import SOURCE_CONVERSIONS, assess, source_disulfide_partners

    validate_inputs(source, nomination, inventory, coordinates)
    preparation.__post_init__()
    if (preparation.source != c.identity(source)
            or preparation.structural_inventory != source.structural_inventory
            or preparation.structural_coordinates != source.structural_coordinates
            or preparation.nomination != source.nomination):
        raise ValueError("preparation outcome changes its actual immutable source lineage")
    atoms, chains, disulfides = (), (), {}
    if any(model.disposition is A.SATISFIED for model in preparation.models):
        members = {row.member_id:row.raw_utf8 for row in source.source_members}
        engine = {row["path"]:row["sha256"] for row in json.loads(members["source.engine-inventory"])["entries"] if row["kind"] == "file"}
        if any(engine.get(".venv/lib/python3.11/site-packages/"+path) != digest for path,digest in SOURCE_CONVERSIONS):
            raise ValueError("independent Amber conversions substitute pinned installed source")
        pieces = [original_assembly(pdb,members["source.original-"+pdb.lower()+"-cif"])
            for pdb in ("1BWV","3ZXW")]
        atoms, chains, operators = (tuple(row for piece in pieces for row in piece[index]) for index in (0,1,2))
        if inventory.atoms != atoms or inventory.chains != chains or inventory.operators != operators:
            raise ValueError("preparation substitutes independently reconstructed authentic structure")
        # Read-only metadata view for the already independent export checker;
        # this does not construct a new source identity or scientific record.
        view = SimpleNamespace(source_members=tuple(SimpleNamespace(filename=pdb.lower()+".cif",
            raw_utf8=members["source.original-"+pdb.lower()+"-cif"]) for pdb in ("1BWV","3ZXW")))
        validate_coordinate_export(view,inventory,coordinates)
        disulfides = {pdb:source_disulfide_partners(pdb,members["source.original-"+pdb.lower()+"-cif"],atoms,chains)
            for pdb in ("1BWV","3ZXW")}
    return assess(source,preparation,assets,atoms,chains,disulfides)


def assess_preparation(source, nomination, inventory, coordinates, preparation, assets):
    """Legacy projection of the additive complete independent assignment census.

    Legacy canonical records stay readable. Current positive admission requires
    complete raw topology/PDB/source-origin joins, beyond producer JSON counts.
    Preparation completion remains distinct from geometric, dynamical or kinetic
    validity; the additive record explicitly preserves those unknown findings.
    """
    result = assess_preparation_integrity(source,nomination,inventory,coordinates,preparation,assets)
    return c.PreparationAssessment(
        "product." + c.NAMESPACE + ".preparation-assessment",
        result.source,
        result.preparation,
        source.structural_inventory,
        source.nomination,
        result.model_dispositions,
        result.assignment_disposition,
        nomination.scope,
    )
