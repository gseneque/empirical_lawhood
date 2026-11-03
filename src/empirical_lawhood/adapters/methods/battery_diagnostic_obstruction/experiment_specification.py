# SPDX-License-Identifier: MPL-2.0
"""Concise retained-history selections, separate from operational custody.

Original negative MODEL evidence and UNKNOWN completion retain their exact
meaning. Selecting references creates no new physical unit or replay grant.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.artifacts import ExternalRootContract
from .contracts import CustodyMember, ObstructionOperationConfig, ObstructionSource, QUESTION


PROTOCOL_ID = "battery.diagnostic-obstruction.retained-reassessment"
AUTHENTICATED_NODE = "battery-diagnostic-obstruction.reassess-authenticated"


@dataclass(frozen=True, slots=True)
class ObstructionExperimentSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-diagnostic-obstruction/experiment-specification"
    specification_id: str
    source: ObjectIdentity
    parent: ObjectIdentity
    question: str = QUESTION
    evidence_scope: str = "EXPOSED_RETAINED_OPERATIONAL_HISTORY"

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        for ref, kind in ((self.source, ObstructionSource), (self.parent, ContributionManifest)):
            if (type(ref) is not ObjectIdentity
                    or (ref.object_schema, ref.object_version) != (kind.SCHEMA, kind.VERSION)):
                raise ValueError("obstruction experiment needs its exact original source and prior contribution types")
            ref.__post_init__()
        if len({self.specification_id, self.source.object_id, self.parent.object_id}) != 3:
            raise ValueError("obstruction experiment aliases its specification, source or prior parent")
        if self.question != QUESTION or self.evidence_scope != "EXPOSED_RETAINED_OPERATIONAL_HISTORY":
            raise ValueError("obstruction experiment cannot change retained UNKNOWN history into numerical qualification")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


@dataclass(frozen=True, slots=True)
class ObstructionSourceCustodySelection(CanonicalRecord):
    """Exact original operational locations, with no copied custody population."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-diagnostic-obstruction/source-custody-selection"
    selection_id: str
    storage: ExternalRootContract
    source: ObjectIdentity
    report: CustodyMember
    cost: CustodyMember

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        if (type(self.storage) is not ExternalRootContract or type(self.source) is not ObjectIdentity
                or (self.source.object_schema, self.source.object_version) != (ObstructionSource.SCHEMA, ObstructionSource.VERSION)
                or type(self.report) is not CustodyMember or type(self.cost) is not CustodyMember):
            raise ValueError("obstruction custody requires its exact guarded root, source and report/cost byte contracts")
        for record in (self.storage, self.source, self.report, self.cost):
            record.__post_init__()
        if self.report.relative_path == self.cost.relative_path or self.selection_id == self.source.object_id:
            raise ValueError("obstruction custody aliases its original operational roles")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)


@dataclass(frozen=True, slots=True)
class AuthenticatedObstructionConfig(CanonicalRecord):
    """Add operational source authentication without revising historical science."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-diagnostic-obstruction/authenticated-operation-config"
    config_id: str
    scientific: ObstructionOperationConfig
    custody: ObstructionSourceCustodySelection

    def __post_init__(self):
        from hashlib import sha256
        from .contracts import identity

        if (self.config_id != "config." + AUTHENTICATED_NODE
                or type(self.scientific) is not ObstructionOperationConfig
                or type(self.custody) is not ObstructionSourceCustodySelection):
            raise ValueError("authenticated obstruction requires its exact original scientific config and operational custody")
        self.scientific.__post_init__()
        self.custody.__post_init__()
        source = self.scientific.source
        cost = source.invocation_cost_raw_utf8.encode()
        if (self.custody.source != identity(source)
                or self.custody.report.sha256 != source.invocation_report_sha256
                or (self.custody.cost.size_bytes, self.custody.cost.sha256) != (len(cost), sha256(cost).hexdigest())):
            raise ValueError("authenticated obstruction custody substitutes original source, report or complete cost bytes")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id, self)

    @property
    def operands(self):
        return self.scientific.operands

    @property
    def source(self):
        return self.scientific.source
