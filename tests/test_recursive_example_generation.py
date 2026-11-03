# SPDX-License-Identifier: MPL-2.0
"""Frozen input identities remain distinct from current unrestricted builders."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import runpy

import pytest

from empirical_lawhood.adapters.composition.recursive_examples import (
    materials_partial_draft,
    rc_scientific_examples,
)
from empirical_lawhood.adapters.methods.battery_recursive_construction.examples import (
    battery_wave_a_draft,
)
from empirical_lawhood.adapters.methods.rc_prerequisite_chain.recursive_translation import (
    rc_recursive_draft,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft


ROOT = Path(__file__).resolve().parents[1]
FROZEN_SHA256 = {
    "battery-wave-a.json": "c97154850db52e0064c6232e1d148ada70d90ace127990631093e582c25a164f",
    "materials-partial.json": "cc4fe5c22061b4834ffee5443a90bbcc228f0e1686206fa6566c9cd4566572c3",
    "rc-budget-v3-scientific.json": "a343c067c6bea41e63865532808eb27e9cab720fc30d0b6931c9af0217ada21c",
    "rc-budget-v3.json": "664c581ee189c7b568d726e066110d7721b4e04b30109bd103a4db8080ecfe1b",
    "rc-menu-v2-scientific.json": "ac6116b555fdc096351e6cfe8da95ed34ac1c175023c51083e4af32aa8012613",
    "rc-menu-v2.json": "461ad7608ed74335ddc75ff18a1a3a182abdde355ba71facc4f580dd082121dd",
    "rc-original-scientific.json": "e74a55ba0f3118e0d6f0d2a7dfe0580b07530b6e024912320339adce3da3ecab",
    "rc-original.json": "ba4a8166716237434b86d5e12648ff2ce60b2f64834f53673c977ba0789b744d",
}


@pytest.fixture(scope="module")
def generated_examples():
    generator = runpy.run_path(str(ROOT / "scripts/generate_recursive_examples.py"))
    return generator["examples"]()


def test_generator_reproduces_every_original_canonical_input(generated_examples):
    assert {Path(path).name for path in generated_examples} == set(FROZEN_SHA256)
    for relative, raw in generated_examples.items():
        assert sha256(raw).hexdigest() == FROZEN_SHA256[Path(relative).name]
        assert (ROOT / relative).read_bytes() == raw


def test_current_builders_remain_unrestricted_without_changing_scientific_operands(
    generated_examples,
):
    current = {
        "materials-partial.json": materials_partial_draft(),
        "battery-wave-a.json": battery_wave_a_draft(),
    }
    by_name = {Path(path).name: raw for path, raw in generated_examples.items()}
    for name, config in rc_scientific_examples().items():
        current[f"rc-{name}.json"] = rc_recursive_draft(
            config, draft_id=f"draft.rc-chain.{name}"
        )
        assert config.canonical_bytes() == by_name[f"rc-{name}-scientific.json"]
    assert len(current) == 5
    for name, draft in current.items():
        assert (draft.maximum_objects, draft.maximum_links, draft.maximum_depth) == (
            None, None, None
        )
        raw = by_name[name]
        historical = decode_canonical_bytes(raw, RecursiveStudyDraft, maximum_bytes=len(raw))
        assert (
            historical.maximum_objects, historical.maximum_links, historical.maximum_depth
        ) == (256, 1024, 32)
        assert historical.canonical_bytes() == raw
        assert replace(
            historical, maximum_objects=None, maximum_links=None, maximum_depth=None
        ) == draft
        assert historical.fingerprint() != draft.fingerprint()
