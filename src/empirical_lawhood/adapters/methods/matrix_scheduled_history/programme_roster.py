# SPDX-License-Identifier: MPL-2.0
"""One exact E4 role, factor, matched-group and wave census validator."""

from decimal import Decimal
from itertools import product

from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import validate_stable_id


def validate_programme_roster(self, *, bank_schema, declared_group_count=None, declared_confidence=None,
        family_sampling_rule='BALANCED_FIXED_FOUR_FAMILY_GROUPS'):
    from .programme_records import MODES, MAXIMUM_PROGRAMME_BYTES, ScheduledProgrammeCase, ScheduledProgrammeFactor, ScheduledProgrammeWave
    from .records import ScheduledSource
    validate_stable_id(self.programme_id)
    if self.mode not in MODES:
        raise ValueError('programme has no declared E4 scientific phase')
    role, groups = MODES[self.mode]
    # Historical callers preserve their exact original frozen selections.
    # Additive current records must pass their explicit declared design.
    if declared_group_count is not None:
        groups = declared_group_count
    confidence = Decimal('.95') if declared_confidence is None else declared_confidence
    if (type(self.minimum_group_count) is not int or self.minimum_group_count != groups
            or type(self.confidence) is not Decimal or self.confidence != confidence
            or self.bank.object_schema != bank_schema
            or tuple(f.factor_id for f in self.factors) != ('temperature', 'friction', 'coupling')):
        raise ValueError('programme changes global role, group denominator, confidence or factor axes')
    if (any(type(f) is not ScheduledProgrammeFactor for f in self.factors)
            or any(type(c) is not ScheduledProgrammeCase for c in self.cases)
            or any(type(w) is not ScheduledProgrammeWave for w in self.waves)
            or any(type(s) is not ObjectIdentity or s.object_schema != ScheduledSource.SCHEMA
                or s.object_version != ScheduledSource.VERSION for s in self.source_census)):
        raise ValueError('programme requires closed original source and subdivision record types')
    roots = tuple(c.root_id for c in self.cases)
    if roots != tuple(sorted(set(roots))) or len(roots) != groups*9 or any(c.role != role for c in self.cases):
        raise ValueError('programme drops or relabels its complete global case census')
    families = tuple(sorted(FOUR_FAMILY_PREPARATION_IDS))
    by_group = {}
    for case in self.cases:
        by_group.setdefault(case.independent_group_id, []).append(case)
    expected_grid = {*product(*((f.low, f.high) for f in self.factors)), tuple(f.center for f in self.factors)}
    if len(by_group) != groups:
        raise ValueError('programme treats coordinate cases as independent groups')
    family_counts = {family: 0 for family in families}
    for rows in by_group.values():
        if (len(rows) != 9 or {c.factor_values for c in rows} != expected_grid
                or len({c.family_id for c in rows}) != 1 or len({c.streams_sha256 for c in rows}) != 1):
            raise ValueError('programme changes original symmetric nine-case matched group')
        family = rows[0].family_id
        if family not in family_counts:
            raise ValueError('programme changes its four preparation families')
        family_counts[family] += 1
    if family_sampling_rule not in ('BALANCED_FIXED_FOUR_FAMILY_GROUPS', 'IID_UNIFORM_FOUR_FAMILIES_NO_REDRAW'):
        raise ValueError('programme changes its declared preparation-family allocation rule')
    if family_sampling_rule == 'BALANCED_FIXED_FOUR_FAMILY_GROUPS' and any(count != groups//4 for count in family_counts.values()):
        raise ValueError('programme changes global balanced preparation-family roster')
    if (tuple(s.object_id for s in self.source_census) != tuple(sorted({s.object_id for s in self.source_census}))
            or not {c.source for c in self.cases} <= set(self.source_census)):
        raise ValueError('programme drops the complete original source/role census')
    if tuple(w.wave_id for w in self.waves) != tuple(sorted({w.wave_id for w in self.waves})) or not self.waves:
        raise ValueError('programme aliases or omits its bounded waves')
    all_groups, all_roots = [], []
    for wave in self.waves:
        selected = tuple(c for c in self.cases if c.independent_group_id in wave.group_ids)
        if tuple(c.root_id for c in selected) != wave.root_ids:
            raise ValueError('programme subdivision changes whole-group membership')
        all_groups.extend(wave.group_ids)
        all_roots.extend(wave.root_ids)
    if (tuple(sorted(all_groups)) != tuple(sorted(by_group)) or tuple(sorted(all_roots)) != roots):
        raise ValueError('programme waves overlap or omit a global group/case')
    if len(self.canonical_bytes()) > MAXIMUM_PROGRAMME_BYTES:
        raise ValueError('explicit scientific programme record exceeds its unchanged 16MiB bound')
