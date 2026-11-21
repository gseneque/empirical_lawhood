# SPDX-License-Identifier: MPL-2.0
"""Lazy scientific family selection; no result archive or native execution."""
from importlib import import_module

from empirical_lawhood.science.joint_description import FAMILIES


def family_module(family_id):
    if family_id not in FAMILIES:
        raise ValueError("select one new scientific family R01--R22")
    number = int(family_id[1:])
    name = ("circuits.joint_description" if number <= 2 else
            "matrix.joint_description.experiments" if number <= 12 else
            "reactor.joint_description" if number in (20, 21) else "joint_description_native")
    return import_module("empirical_lawhood.domains." + name)


def preset(family_id):
    selected = tuple(row for row in family_module(family_id).presets() if row["family_id"] == family_id)
    if len(selected) != 1:
        raise ValueError("family catalogue must resolve exactly one scientific definition")
    return selected[0]


def presets():
    return tuple(preset(family) for family in FAMILIES)
