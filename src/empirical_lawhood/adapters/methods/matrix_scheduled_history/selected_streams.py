# SPDX-License-Identifier: MPL-2.0
"""Explicit pure E4 history and independent-future stream derivation."""

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_sha256, validate_stable_id


STREAM_RULE = "SHA256_SELECTED_E4_GROUP_PURPOSE_V1"


@dataclass(frozen=True, slots=True)
class SelectedE4StreamRecipe(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/stream-recipe"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    prefix_seed_material_sha256: str
    future_seed_material_sha256: str
    derivation_rule_id: str
    family_seed_material_sha256: str | None = None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value in (self.prefix_seed_material_sha256, self.future_seed_material_sha256):
            validate_sha256(value)
        if self.prefix_seed_material_sha256 == self.future_seed_material_sha256 or self.derivation_rule_id != STREAM_RULE:
            raise ValueError("selected E4 streams require separate explicit history/future material and the exact declared rule")
        if self.family_seed_material_sha256 is not None:
            validate_sha256(self.family_seed_material_sha256)
            if self.family_seed_material_sha256 in (self.prefix_seed_material_sha256, self.future_seed_material_sha256):
                raise ValueError('selected E4 family draws require separate declared random material')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    def streams(self, group_id, *, future):
        if type(future) is not bool:
            raise TypeError("selected E4 stream role requires an exact bool")
        validate_stable_id(group_id)
        material = self.future_seed_material_sha256 if future else self.prefix_seed_material_sha256
        return tuple(MatrixHistorySeed(purpose, sha256(canonical_json_bytes((
            self.derivation_rule_id, material, group_id, purpose,
        ))).hexdigest()) for purpose in HISTORY_PURPOSES)

    def family(self, group_id):
        """One uniform two-bit draw per assigned group; never balance or redraw."""
        from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
        self.__post_init__()
        validate_stable_id(group_id)
        if self.family_seed_material_sha256 is None:
            raise ValueError('IID E4 family allocation requires its separately committed draw material')
        digest = sha256(canonical_json_bytes(('SHA256_SELECTED_E4_UNIFORM_FAMILY_V1',
            self.family_seed_material_sha256, group_id))).digest()
        return tuple(sorted(FOUR_FAMILY_PREPARATION_IDS))[digest[0] & 3]
