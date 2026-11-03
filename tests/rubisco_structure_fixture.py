# SPDX-License-Identifier: MPL-2.0
"""Complete exposed historical products; no receipt authority or new science."""

import gzip
from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.adapters.methods.rubisco_insilico_structure import contracts as c
from empirical_lawhood.kernel.decoding import decode_canonical_bytes


def historical_products():
    root = Path(__file__).parent / "fixtures/rubisco/structure"
    census = json.loads((root / "historical-product-census.json").read_bytes())
    if (
        census["evidence_role"] != "EXPOSED_SOFTWARE_CONFORMANCE_ONLY"
        or census["scientific_qualification"] != "NOT_PERFORMED"
        or census["fresh_independent_units"] != 0
        or census["contains_execution_receipts"]
        or census["thinning"] != "NONE_COMPLETE_CANONICAL_PRODUCTS"
        or set(census["members"]) != {name + "-historical-v1.json.gz" for name in ("inventory", "coordinates", "assessment")}
    ):
        raise ValueError("exposed structural fixture changes complete census/evidence role")
    products = {}
    for name, codec in (("inventory", c.StructuralInventory), ("coordinates", c.AssemblyCoordinates), ("assessment", c.StructuralAssessment)):
        filename = name + "-historical-v1.json.gz"
        expected = census["members"][filename]
        compressed = (root / filename).read_bytes()
        if len(compressed) != expected["compressed_bytes"] or sha256(compressed).hexdigest() != expected["compressed_sha256"]:
            raise ValueError("exposed structural fixture compressed source changed")
        raw = gzip.decompress(compressed)
        if len(raw) != expected["raw_bytes"] or sha256(raw).hexdigest() != expected["raw_sha256"]:
            raise ValueError("exposed structural fixture complete product changed")
        products[name] = decode_canonical_bytes(raw, codec, maximum_bytes=None)
    return products
