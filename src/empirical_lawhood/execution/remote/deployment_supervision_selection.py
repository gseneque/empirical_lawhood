# SPDX-License-Identifier: MPL-2.0
"""Bounded authorization and allocation selection shared with the thin controller.

This owner uses only the standard library and inward operational contracts.
It must remain importable in the separate pinned SkyPilot environment.
"""

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath

from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.science.records.serialization import validate_sha256
from empirical_lawhood.execution.deployment_budget import DeploymentAllocation


def _absolute(value):
    if (type(value) is not str or not value.startswith('/') or value == '/'
            or str(PurePosixPath(value)) != value or '..' in PurePosixPath(value).parts):
        raise ValueError('supervision requires normalized absolute paths')
    return value


@dataclass(frozen=True, slots=True)
class SupervisionSelection:
    allocation: DeploymentAllocation
    authorization_path: str
    authorization_sha256: str
    controller_python: str
    controller_source_paths: tuple[str, ...]
    controller_config: str

    def __post_init__(self):
        if type(self.allocation) is not DeploymentAllocation:
            raise TypeError('supervision requires an actual allocation')
        self.allocation.__post_init__()
        for path in (self.authorization_path, self.controller_python, self.controller_config, *self.controller_source_paths):
            _absolute(path)
        if type(self.controller_source_paths) is not tuple or not self.controller_source_paths:
            raise ValueError('select the installed controller and engine source paths')
        validate_sha256(self.authorization_sha256, field_name='original owner authorization')

    @classmethod
    def read(cls, path):
        return cls.from_document(json.loads(read_bounded_bytes(Path(path), maximum_bytes=128*1024)))

    @classmethod
    def from_document(cls, document):
        document = dict(document)
        if document.pop('version', None) != '1.0.0':
            raise ValueError('unsupported supervision selection revision')
        document['allocation'] = DeploymentAllocation.from_document(document['allocation'])
        document['controller_source_paths'] = tuple(document['controller_source_paths'])
        return cls(**document)

    def require_authorization(self):
        raw = read_bounded_bytes(Path(self.authorization_path), maximum_bytes=128*1024)
        if sha256(raw).hexdigest() != self.authorization_sha256:
            raise ValueError('original owner authorization changed')
        authorized = json.loads(raw)
        selected = self.allocation
        expected = {'status': 'OWNER_AUTHORIZED', 'deployment_id': selected.deployment_id,
            'budget_total_usd': selected.budget.total_usd, 'return_reserve_usd': selected.budget.return_reserve_usd,
            'retirement_margin_usd': selected.budget.retirement_margin_usd,
            'maximum_compute_hourly_usd': selected.budget.compute_hourly_usd,
            'keep_volume_id': selected.volume_id, 'zone': selected.zone,
            'financial_actions': ['CANCEL_SELECTED_JOBS', 'RETIRE_SELECTED_COMPUTE_KEEP_VOLUME']}
        if any(authorized.get(key) != value for key, value in expected.items()):
            raise ValueError('original owner authorization does not cover the selected allocation and financial actions')
        return raw

