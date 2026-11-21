# SPDX-License-Identifier: MPL-2.0
"""Assemble label-free SSU queries and matched source ratios from selected inputs."""

from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
import re
import tarfile

from empirical_lawhood.domains.rubisco.rubisco_prediction.interface_transfer import (
    ENDPOINTS,
    NAMES,
    aligned_weights,
    fit_predict,
    log_ratio,
    site_vector,
)
from .genbank import _translate_complete_cds

DESIGN_SHA256 = "eed23570de29bda56c9fc40a44d8c78c7976593c31f402434c45b3774fdf35e1"
ALA = ("S16A", "L18A", "P19A", "Y32A", "E43A", "W73A", "L78A", "P79A", "F81A", "E92A")
POTATO = {
    "pS2": ("T22S", "Q88E", "C90A", "N92K"),
    "pS3": ("T22S", "N55H", "K57S", "C90A"),
}
DONOR = (("9.5", "6.9"), ("56.3", "52.6"))


def hashed(data):
    return sha256(data).hexdigest()


def change(sequence, substitutions, offset=0):
    result = list(sequence)
    for edit in substitutions:
        index = int(edit[1:-1]) - 1 + offset
        if result[index] != edit[0]:
            raise ValueError(
                f"Parent identity differs at {edit} with biological offset {offset}"
            )
        result[index] = edit[-1]
    return "".join(result)


def protein_embl(raw):
    flat = "\n".join(
        line[5:] for line in raw.decode().splitlines() if line.startswith("FT")
    )
    for until_next in re.findall(r"(?m)^CDS[^\n]*\n((?:[ ]+[^\n]*\n)+)", flat + "\n"):
        if '/gene="rbcS"' in until_next:
            return "".join(
                re.search(r'/translation="([^"]+)"', until_next).group(1).split()
            )
    raise ValueError("The deposited construct lacks an SSU translation")


def predict(evidence: Path, archive: Path):
    design = (evidence / "transfer-design.json").read_bytes()
    if hashed(design) != DESIGN_SHA256:
        raise ValueError("Changed frozen design")
    geometry = (evidence / "geometry.json").read_bytes()
    geo = json.loads(geometry)["result"]
    recipe = (evidence / "hybrid-recipes.json").read_bytes()
    hybrid = json.loads(recipe)
    if hybrid["source_sha256"] != hashed(
        (evidence / "sources/hybrid-supp-0.pdf").read_bytes()
    ):
        raise ValueError("Changed deposited hybrid supplement")
    training, queries = [], []
    sources = {
        "design": hashed(design),
        "geometry": hashed(geometry),
        "engineered_recipes": hashed(recipe),
    }
    backgrounds = {}

    def row(label, background, model, parent, variant):
        source = geo[model]
        native = {int(i): r["weight"] for i, r in source["sites"].items()}
        weights = aligned_weights(parent, source["sequence"], native)
        vector, substitutions = site_vector(parent, variant, weights)
        return {
            "id": label,
            "background": background,
            "structure": model,
            "features": vector,
            "changes": substitutions,
            "parent_sha256": hashed(parent.encode()),
            "variant_sha256": hashed(variant.encode()),
            "observed_parent_sites": len(weights),
        }

    from empirical_lawhood.domains.rubisco.rubisco_portfolio_inquiry.source_manifest import (
        SOURCE_MANIFEST,
    )

    published = {
        f"macro/{key}--{name}": pin for key, name, _size, pin in SOURCE_MANIFEST
    }
    with tarfile.open(archive) as t:

        def get(path):
            raw = t.extractfile(path).read()
            sources[path] = hashed(raw)
            if path in published and sources[path] != published[path]:
                raise ValueError(
                    "Published source differs from its original manifest: " + path
                )
            return raw

        panel = json.loads(get("macro/source.000--wilson2017-panel.json"))["value"][
            "rows"
        ]
        te = [r["value"] for r in panel if r["value"]["native_rbcl_edits"] == "P415A"]
        (anchor,) = [r for r in te if r["name"] == "Te-P415A"]
        readings = {"turnover": "KCAT_C", "specificity": "SPECIFICITY_CO"}

        def endpoints(material):
            return {
                label: next(
                    e["value"]
                    for e in material["endpoints"]
                    if e["value"]["kind"] == kind
                )
                for label, kind in readings.items()
            }

        native = anchor["te_protein_specification"]["value"]
        baseline = endpoints(anchor)
        backgrounds["Te-P415A"] = hashed(native["large_subunit_sequence"].encode())
        for r in te:
            if r is anchor:
                continue
            spec = r["te_protein_specification"]["value"]
            if spec["large_subunit_sequence"] != native["large_subunit_sequence"]:
                raise ValueError("Training contrast changes its LSU")
            data = row(
                r["native_rbcs_edits"].replace(", ", "/"),
                "Te-P415A",
                "3ZXW",
                native["small_subunit_sequence"],
                spec["small_subunit_sequence"],
            )
            out = endpoints(r)
            data["responses"] = {
                ep: [out[ep]["mean"]["decimal"], baseline[ep]["mean"]["decimal"]]
                for ep in ENDPOINTS
            }
            data["native_endpoints"] = out
            training.append(data)
        if [r["id"] for r in training] != json.loads(design)["training"]["rows"]:
            raise ValueError("Training material census differs")
        for label in ("M1", "V1"):

            def seq(id_):
                raw = get(f"structural/gp.ssu.{id_}.{label.lower()}.fasta")
                return "".join(raw.decode().splitlines()[1:])

            p, v = seq("wt"), seq("i95m")
            if p != geo[label]["sequence"] or change(p, ["I95M"]) != v:
                raise ValueError(
                    "The selected red-algal material differs from the deposited forecast core"
                )
            queries.append(row("Gp-" + label, "Galdieria", label, p, v))
        potato = protein_embl(get("macro/source.005--MT596798.1.embl"))
        trichome = protein_embl(get("macro/source.006--MT596799.1.embl"))
        for k, material in {
            **{k: change(potato, sub, 2) for k, sub in POTATO.items()},
            "pST": trichome,
        }.items():
            queries.append(row("potato-" + k, "potato", "4RUB", potato, material))
    parent = hybrid["parent"]
    if parent != geo["1GK8"]["sequence"]:
        raise ValueError(
            "Published algal parent differs from selected structural sequence"
        )
    for edit in ALA:
        queries.append(
            row("alga-" + edit, "Chlamydomonas", "1GK8", parent, change(parent, [edit]))
        )
    for name in ("spinach", "arabidopsis", "sunflower"):
        material = hybrid["hybrids"][name]
        if _translate_complete_cds(material["dna"]) != material["protein"]:
            raise ValueError(
                "The engineered SSU translation differs from the supplement"
            )
        queries.append(
            row("hybrid-" + name, "Chlamydomonas", "1GK8", parent, material["protein"])
        )
    coeff, predicted = fit_predict(training, queries)
    donor = [float(log_ratio(*p)) for p in DONOR]
    for label in ("Gp-M1", "Gp-V1"):
        predicted[label]["donor"] = donor
    return {
        "design_sha256": DESIGN_SHA256,
        "sources": sources,
        "engine": {k: version(k) for k in ("numpy", "rapidfuzz")},
        "descriptors": NAMES,
        "background_sequence_digests": backgrounds,
        "matched_donor_parent": baseline,
        "training": training,
        "queries": queries,
        "coefficients": coeff,
        "predictions": predicted,
        "donor_applicability": "Only the Gp target queries have the assigned homologous I/V-to-M contrast.",
    }
