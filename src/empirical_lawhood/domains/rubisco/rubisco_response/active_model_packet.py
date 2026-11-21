# SPDX-License-Identifier: MPL-2.0
"""Closed all-site material preparation; arrays remain exact external operands."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_assessment import ActiveSeedAssessment
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_preparation import ActivePreparationProtocol, PreparedCatalyticSite
from empirical_lawhood.domains.rubisco.rubisco_response.active_state_geometry import CatalyticStateSeed
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


@dataclass(frozen=True, slots=True)
class ActiveModelPreparation(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/active-model-preparation'
    preparation_id: str
    representation: ObjectIdentity
    prototype: ObjectIdentity
    protocol: ActivePreparationProtocol
    sites: tuple[PreparedCatalyticSite, ...]
    seeds: tuple[CatalyticStateSeed, ...]
    assessments: tuple[ActiveSeedAssessment, ...]

    def __post_init__(self):
        validate_stable_id(self.preparation_id)
        exact(self.representation, ObjectIdentity)
        exact(self.prototype, ObjectIdentity)
        exact(self.protocol, ActivePreparationProtocol)
        for rows, kind in ((self.sites, PreparedCatalyticSite), (self.seeds, CatalyticStateSeed),
                (self.assessments, ActiveSeedAssessment)):
            if type(rows) is not tuple:
                raise ValueError('active model requires its complete immutable all-site census')
            for row in rows:
                exact(row, kind)
        if (len(self.sites) != 8 or tuple(s.path.reactive_site_id for s in self.sites)
                != tuple(sorted({s.path.reactive_site_id for s in self.sites}))
                or any(s.protocol != self.protocol.identity or s.path.representation != self.representation for s in self.sites)):
            raise ValueError('active model changes its original eight sites, representation or chemical protocol')
        site_map = {s.identity: s for s in self.sites}
        expected = {(site.identity, graph.identity, occupancy) for site in self.sites for graph in self.protocol.graphs
            for occupancy in (('OCCUPIED', 'UNOCCUPIED') if graph.label.startswith('reactive-') else ('AS_CONSTRUCTED',))}
        observed = {(s.site, s.graph, s.water_occupancy) for s in self.seeds}
        if (observed != expected or len(self.seeds) != len(expected)
                or tuple(s.seed_id for s in self.seeds) != tuple(sorted({s.seed_id for s in self.seeds}))
                or any(s.protocol != self.protocol.identity or s.physical_atom_count != site_map[s.site].path.physical_atom_count
                    for s in self.seeds)):
            raise ValueError('active model drops, duplicates or changes a declared site/state alternative')
        if (len(self.assessments) != len(self.seeds)
                or any((a.seed, a.site, a.physical_atom_count) != (s.identity, s.site, s.physical_atom_count)
                    for s, a in zip(self.seeds, self.assessments, strict=True))):
            raise ValueError('active model omits or substitutes a seed assessment')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.preparation_id, self)
