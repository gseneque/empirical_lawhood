# SPDX-License-Identifier: MPL-2.0
"""Disclosed release-validation populations; no native/authority evidence.

The selected32/64/64 counts, factor levels, confidence and resource choices are
explicit release fixtures, never production defaults or fresh scientific units.
"""
from empirical_lawhood.kernel.provenance import ObjectIdentity

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_history_analysis.records import MatrixHistorySeed, HISTORY_PURPOSES
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as old
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as r
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as p
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponsePanel
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledCalibrationCriterion, ScheduledResponseSelection
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from tests.test_matrix_selected_e3_e4_bridge import selected_bridge, transfer  # noqa: F401
from tests.test_matrix_selected_protected import unpublished


@pytest.fixture(scope="module")
def selected_e4_populations(selected_bridge):  # noqa: F811
    return build_selected_e4_populations(selected_bridge)


def build_selected_e4_populations(bridge, *, counts=(32, 64, 64), family_counts=None):
    base = bridge.bank
    matched = getattr(base.forecast_design.package.specification.measurement, 'is_matched', False)
    families = tuple(sorted(FOUR_FAMILY_PREPARATION_IDS))
    selections = tuple((label, role, count) for label, role, count in zip(('DEV', 'CAL', 'CONF'),
        (MatrixProgrammeRole.DEVELOPMENT, MatrixProgrammeRole.CALIBRATION, MatrixProgrammeRole.CONFIRMATION), counts, strict=True))
    roots, scopes = [], []
    for label, role, count in selections:
        for family_index, family in enumerate(families):
            coordinates = tuple(value for value in base.reservation.allocation.coordinates if value.family_id == family)
            assigned_count = count // len(families) if family_counts is None else family_counts[label][family_index]
            groups = tuple(f"group.selected-e4.release.{label.lower()}.{family_index}.{index:02}" for index in range(assigned_count))
            for group in groups:
                streams = tuple(MatrixHistorySeed(purpose, sha256(("DISCLOSED_E4_RELEASE." + group + purpose).encode()).hexdigest())
                    for purpose in HISTORY_PURPOSES)
                for index, coordinate in enumerate(coordinates):
                    root = old.MatrixProgrammeRoot(f"root.{group}.{index}", group, "regime." + coordinate.coordinate_id,
                        coordinate.coordinate_id, role, coordinate.clock_id)
                    roots.append(old.ScheduledRoot(root, old.coordinate_identity(coordinate), streams))
            if groups:
                scopes.append(old.ScheduledMatchedScope(f"scope.selected-e4.release.{label.lower()}.{family_index}", role, groups,
                    tuple(old.coordinate_identity(value) for value in coordinates),
                    "COMMON_DECLARED_INITIAL_STATE_AND_FOUR_PURPOSE_PCG64DXSM_NOISE_COORDINATE_SPECIFIC_OU"))
    allocation = replace(base.reservation.allocation, allocation_id="allocation.selected-e4.release",
        roots=tuple(sorted(roots, key=lambda value: value.root.root_id)),
        matched_scopes=tuple(sorted(scopes, key=lambda value: value.scope_id)))
    reservation = old.ScheduledReservation("reservation.selected-e4.release", allocation,
        unpublished(allocation, "publication.selected-e4.release-allocation"))
    selection = replace(base.specification.selection, selection_id="selection.selected-e4.release",
        reservation=old.identity(reservation))
    specification = old.ScheduledSpecification("specification.selected-e4.release", selection,
        unpublished(selection, "publication.selected-e4.release-selection"))
    design = replace(base.forecast_design, record_id="forecast-design.selected-e4.release", allocation=old.identity(allocation))
    prototype = base.response_selection.protocols[0]
    banks, programmes = {}, {}
    index=ScheduledSourceIndex.from_shared(reservation=reservation,specification=specification,provenances=base.provenances)
    for label, role, count in selections:
        subjects=tuple(index.resolve(index.reference(source_id="source."+value.root.root_id,
            root_id=value.root.root_id,provenance=base.provenances[0].identity))
            for value in allocation.roots if value.root.role is role)
        protocols = []
        for source in subjects:
            templates = replace(prototype.templates, operand_id="templates." + source.root_id,
                source=old.identity(source), producers=(old.identity(source),))
            protocols.append(replace(prototype, protocol_id="protocol." + source.root_id,
                public_source=ScheduledPublicSource.from_source(source), templates=templates))
        panels = []
        for group in sorted({value.root.root.independent_group_id for value in subjects}):
            root = next(value for value in allocation.roots if value.root.independent_group_id == group)
            panels.append((group, tuple(ScheduledResponsePanel("panel." + group + "." + str(index), group, panel_role,
                "ORIGINAL_COMPLETED_PREFIX_GENERATOR_STATES" if index == 0 else "FRESH_DECLARED_FUTURE_START_AT_CUTOFF",
                root.streams if index == 0 else tuple(MatrixHistorySeed(purpose,
                    sha256(("DISCLOSED_E4_RELEASE_FUTURE." + group + purpose).encode()).hexdigest()) for purpose in HISTORY_PURPOSES))
                for index, panel_role in enumerate(("COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE")))))
        criterion = None if role is not MatrixProgrammeRole.CALIBRATION else ScheduledCalibrationCriterion(
            "criterion.selected-e4.release-native-construction", "unit.selected-e4.whole-group", count, D(0), () if matched else families,
            'WHOLE_GROUP_MAX_POSITIVE_PAIRED_LOG_RESIDUAL_NINE_COORDINATES_FACTOR58' if matched else
                "COMPLETE_MATCHED_GROUP_MAX_ALL15_POSITIVE_LOG_ERROR_MINUS_PRE_FUTURE_POINT_NONUSE_INFINITY")
        responses = ScheduledResponseSelection("responses.selected-e4.release." + label.lower(), ObjectIdentity.from_record(allocation.allocation_id, allocation),
            tuple(protocols), tuple(panels), base.response_selection.template_publications, criterion)
        responses.validate_allocation(allocation)
        population_design = replace(base.design, record_id="design.selected-e4.release." + label.lower(),
            group_count=count, confidence=D(".95"), wave_group_count=4,
            family_sampling_rule='IID_UNIFORM_FOUR_FAMILIES_NO_REDRAW' if matched and label != 'DEV'
                else 'BALANCED_FIXED_FOUR_FAMILY_GROUPS')
        values = ("bank.selected-e4.release." + label.lower(), reservation, specification, base.provenances,
            tuple(value.reference for value in subjects), base.audit, base.audit_publication,
            design, responses, unpublished(responses, "publication.responses.selected-e4.release." + label.lower()), population_design)
        bank = r.SelectedE3E4DevelopmentBank(*values) if label == "DEV" else p.SelectedE4PhaseBank(*values,
            "CALIBRATION" if label == "CAL" else "CONFIRMATION")
        programme = (r.SelectedE3E4DevelopmentProgramme.from_selected_bank(bank, programme_id="programme.selected-e4.release.dev")
            if label == "DEV" else p.SelectedE4PhaseProgramme.from_bank(bank,
                programme_id="programme.selected-e4.release." + label.lower()))
        banks[label], programmes[label] = bank, programme
    return SimpleNamespace(development=programmes["DEV"], calibration=programmes["CAL"], confirmation=programmes["CONF"],
        development_bank=banks["DEV"], calibration_bank=banks["CAL"], confirmation_bank=banks["CONF"], selected=bridge.selected,
        secondary_target=bridge.secondary_target, secondary_readout=bridge.secondary_readout)
