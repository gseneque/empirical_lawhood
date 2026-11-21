# SPDX-License-Identifier: MPL-2.0
"""Noncontact dependency observations for the documented native environments."""

from __future__ import annotations

from enum import Enum
from importlib import metadata
import platform

from empirical_lawhood.api.models import DoctorDependencySummary
from empirical_lawhood.adapters.composition.generated_public_facets import ENVIRONMENT_DECLARATIONS
from empirical_lawhood.execution.discovery_descriptors import EnvironmentDeclaration


class EnvironmentRoute(str, Enum):
    REACTOR = "reactor"
    PREPARED_RESPONSE = 'prepared-response'
    OPEN_SIMULATORS = "open-simulators"
    REACTION_RESPONSE = 'reaction-response'
    GRID2OP = "grid2op"
    RC_CHALLENGES = "rc-challenges"
    FINITE_RESPONSE_LAW = "finite-response-law"
    PREPARATION_APPLICABILITY = "preparation-applicability"


def environment_routes() -> tuple[EnvironmentDeclaration, ...]:
    """Return closed code-owned facts, without inspecting an environment."""
    return ENVIRONMENT_DECLARATIONS


def environment_by_id(route: str) -> EnvironmentDeclaration:
    """Legacy Enum callers and new adapter route IDs share the same lookup."""
    identifier = route.value if isinstance(route, EnvironmentRoute) else route
    if isinstance(identifier, str):
        for declaration in ENVIRONMENT_DECLARATIONS:
            if declaration.route_id == identifier:
                return declaration
    raise ValueError(f"unknown environment route: {route}")


def inspect_route_dependencies(
    route: EnvironmentRoute | str | None,
) -> tuple[DoctorDependencySummary, ...]:
    """Read distribution metadata only; never import or initialize a simulator."""

    declaration = None if route is None else environment_by_id(route)
    # Preserve the original default inspection's two observations and no CPython
    # assertion. This narrow report still makes no workflow-readiness claim.
    selected = (tuple(row for row in environment_by_id("open-simulators").distribution_versions
                      if row[0] in ("gymtorax", "torax"))
                if declaration is None else declaration.distribution_versions)
    observations: list[tuple[str, str | None, str]] = []
    if declaration is not None:
        python = platform.python_version() if platform.python_implementation() == declaration.python_implementation else None
        observations.append((declaration.python_implementation.lower(), python, declaration.python_version))
    for distribution, expected in selected:
        try:
            installed = metadata.version(distribution)
        except metadata.PackageNotFoundError:
            installed = None
        observations.append((distribution, installed, expected))
    return tuple(
        DoctorDependencySummary(
            dependency_id=name,
            available=installed is not None,
            required_for_actions=("gym-torax-substrate" if declaration is None else declaration.route_id,),
            reason_codes=(
                (f"DEPENDENCY_{name.upper()}_ABSENT",) if installed is None else
                (f"DEPENDENCY_{name.upper()}_VERSION_MISMATCH",) if installed != expected else ()
            ),
            installed_version=installed,
            required_version=expected,
            version_matches=installed == expected,
        )
        for name, installed, expected in observations
    )
