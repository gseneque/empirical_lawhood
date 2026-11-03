# SPDX-License-Identifier: MPL-2.0
"""Reactor public source-custody names over the shared authoring owner."""

from empirical_lawhood.api.authoring_handoff import (
    authenticate_authoring_source,
    read_authoring_source_companion,
)


def read_reactor_source_companion(*, writer, directory, name, expected_schema):
    return read_authoring_source_companion(writer=writer, directory=directory,
        name=name, expected_schema=expected_schema)


def authenticate_reactor_authoring_source(*, directory, project_root, artifact_writer):
    return authenticate_authoring_source(directory=directory, project_root=project_root,
        artifact_writer=artifact_writer)
