# SPDX-License-Identifier: MPL-2.0
"""Same-origin paired future views and explicit consumer numerical standards.

The original PRIMARY edition and closed historical packages are unchanged.
Exposed finite-dt comparison never supplies freshness or continuum enclosure.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.simulators.six_matrix_response.contracts import SixMatrixResponseNumericalView
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, validate_decimal, validate_sha256, validate_stable_id

from .records import (
    EXPOSED, PREDICTORS, SIGNS, MatrixParameterResponseAllocation, MatrixParameterResponseArrays,
    MatrixParameterResponseNativeEvent, MatrixParameterResponseOrigin, MatrixParameterResponseRoot,
    MatrixParameterResponseSource, identity as original_identity,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.records import MatrixFactorResponseScore

VIEWS = ('FINE','PRIMARY')
SAMPLER = 'PCG64_INTERLEAVED_COARSE_AND_BRIDGE_HERMITIAN_MATRICES_V1'
DISPOSITION_WITHOUT_STANDARD = 'UNASSESSED_NO_FROZEN_CONSUMER_NUMERICAL_STANDARD'


def allocation_roster_fingerprint(allocation):
    return sha256(b''.join(r.canonical_bytes() for r in allocation.roots)).hexdigest()


def identity(record):
    for name in ('source_id','design_id','forecast_id','response_id','assessment_id','standard_id','config_id','grid_id'):
        if hasattr(record,name):
            return ObjectIdentity.from_record(getattr(record,name),record)
    return original_identity(record)


@dataclass(frozen=True, slots=True)
class MatrixPairedNumericalStandard(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-paired/consumer-numerical-standard'
    standard_id: str
    consumer: ObjectIdentity
    common_origin: ObjectIdentity
    receiver_absolute_tolerance: Decimal
    relative_curve_tolerance: Decimal
    scope: str = 'EMPIRICAL_PAIRED_FINITE_DT_FUNCTIONAL_DISCREPANCY_NO_CONTINUUM_ENCLOSURE'

    def __post_init__(self):
        validate_stable_id(self.standard_id)
        for value in (self.receiver_absolute_tolerance,self.relative_curve_tolerance):
            validate_decimal(value,field_name='frozen numerical tolerance',minimum=Decimal(0))
            if value <= 0:
                raise ValueError('consumer standard requires actual positive frozen tolerances')
        if self.common_origin.object_schema != MatrixParameterResponseOrigin.SCHEMA or self.scope != 'EMPIRICAL_PAIRED_FINITE_DT_FUNCTIONAL_DISCREPANCY_NO_CONTINUUM_ENCLOSURE':
            raise ValueError('paired numerical standard changes actual origin or implies continuum enclosure')


@dataclass(frozen=True, slots=True)
class MatrixParameterPairedDesign(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-paired/design'
    design_id: str
    common_origin: MatrixParameterResponseOrigin
    fine_view: SixMatrixResponseNumericalView
    numerical_standard: MatrixPairedNumericalStandard | None = None
    sampler: str = SAMPLER
    standing: str = 'SAME_PRIMARY_STATE_FRAME_FORCE_PULSE_HORIZONS_BOTH_NUMERICAL_VIEWS'

    def __post_init__(self):
        validate_stable_id(self.design_id)
        d = self.common_origin.design
        if (type(self.common_origin) is not MatrixParameterResponseOrigin or type(self.fine_view) is not SixMatrixResponseNumericalView
                or self.fine_view.view_id == d.view.view_id or self.fine_view.timestep != d.coordinate.fine_view.timestep
                or self.fine_view.timestep*2 != d.view.timestep
                or any(getattr(self.fine_view,name) != getattr(d.view,name) for name in
                    ('friction_gamma','bath_temperature','time_unit','precision','integrator','rng_algorithm','rng_version','stream_derivation_rule_id'))
                or self.sampler != SAMPLER or self.standing != 'SAME_PRIMARY_STATE_FRAME_FORCE_PULSE_HORIZONS_BOTH_NUMERICAL_VIEWS'
                or self.numerical_standard is not None and self.numerical_standard.common_origin != original_identity(self.common_origin)):
            raise ValueError('paired design changes same physical origin/force/pulse/clock/source sampler')

    @property
    def primary(self):
        return self.common_origin.design

    def multiplier(self,view):
        if view not in VIEWS:
            raise ValueError('paired design receives unknown numerical view')
        return 1 if view == 'PRIMARY' else 2

    def view(self,name):
        return self.primary.view if name == 'PRIMARY' else self.fine_view if name == 'FINE' else self.multiplier(name)

    def horizon_steps(self,name):
        return tuple(self.multiplier(name)*n for n in self.primary.horizon_steps)

    def native_origin_tick(self,name):
        return self.multiplier(name)*self.primary.origin_tick


@dataclass(frozen=True, slots=True)
class MatrixParameterPairedSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-paired/source'
    source_id: str
    original_source: ObjectIdentity
    original_allocation: ObjectIdentity
    allocation_roster_sha256: str
    requested_roots: int
    requested_independent_groups: int
    root: MatrixParameterResponseRoot
    design: MatrixParameterPairedDesign
    provenance: NumericalProducingProvenance
    historical_enclosing_return: str
    exposure: str = EXPOSED

    def __post_init__(self):
        validate_stable_id(self.source_id)
        validate_sha256(self.allocation_roster_sha256)
        if (self.original_source.object_schema != MatrixParameterResponseSource.SCHEMA
                or self.original_allocation.object_schema != MatrixParameterResponseAllocation.SCHEMA
                or type(self.requested_roots) is not int or self.requested_roots < 1
                or type(self.requested_independent_groups) is not int or not 1 <= self.requested_independent_groups <= self.requested_roots
                or type(self.root) is not MatrixParameterResponseRoot or type(self.design) is not MatrixParameterPairedDesign
                or type(self.provenance) is not NumericalProducingProvenance or self.exposure != EXPOSED
                or self.historical_enclosing_return not in ('ABSENT_CONDITIONAL_DERIVED_HISTORY','REFUSED_CONDITIONAL_DERIVED_HISTORY','AUTHENTIC_ORIGINAL_ORDINARY_RETURN')):
            raise ValueError('paired source changes actual original source/allocation/conditional history')

    def validate_original(self,original,origin):
        if (original_identity(original) != self.original_source or original_identity(original.allocation) != self.original_allocation
                or allocation_roster_fingerprint(original.allocation) != self.allocation_roster_sha256
                or len(original.allocation.roots) != self.requested_roots
                or len({r.independent_group_id for r in original.allocation.roots}) != self.requested_independent_groups
                or self.root != original.root or self.design.common_origin != origin
                or origin.source != original_identity(original.causal) or origin.design != original.design
                or self.historical_enclosing_return != original.historical_enclosing_return
                or origin.root_id != self.root.root_id or origin.independent_group_id != self.root.independent_group_id):
            raise ValueError('paired source substitutes original authenticated allocation/origin/conditional standing')


def source_for(original,design,*,source_id,provenance):
    result = MatrixParameterPairedSource(source_id,original_identity(original),original_identity(original.allocation),
        allocation_roster_fingerprint(original.allocation),len(original.allocation.roots),
        len({r.independent_group_id for r in original.allocation.roots}),original.root,design,provenance,
        original.historical_enclosing_return)
    result.validate_original(original,design.common_origin)
    return result


@dataclass(frozen=True, slots=True)
class MatrixParameterPairedForecast(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-paired/forecast'
    forecast_id: str
    design: ObjectIdentity
    origin: ObjectIdentity
    model: ObjectIdentity
    arrays: MatrixParameterResponseArrays
    dispositions: tuple[tuple[str,str,str|None], ...]

    def __post_init__(self):
        validate_stable_id(self.forecast_id)
        if (self.design.object_schema != MatrixParameterPairedDesign.SCHEMA or self.origin.object_schema != MatrixParameterResponseOrigin.SCHEMA
                or tuple(n for n,_,_ in self.dispositions) != PREDICTORS):
            raise ValueError('paired forecast loses source-free origin/model/complete five-predictor census')


@dataclass(frozen=True, slots=True)
class MatrixParameterPairedNative(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-paired/native-responses'
    response_id: str
    source: ObjectIdentity
    design: ObjectIdentity
    origin: ObjectIdentity
    forecast: ObjectIdentity
    branch_ids: tuple[str, ...]
    arrays: MatrixParameterResponseArrays
    events: tuple[MatrixParameterResponseNativeEvent, ...]

    def __post_init__(self):
        validate_stable_id(self.response_id)
        if (self.source.object_schema != MatrixParameterPairedSource.SCHEMA or self.design.object_schema != MatrixParameterPairedDesign.SCHEMA
                or self.origin.object_schema != MatrixParameterResponseOrigin.SCHEMA
                or self.forecast.object_schema != MatrixParameterPairedForecast.SCHEMA
                or len(self.branch_ids) != 48 or self.branch_ids != tuple(sorted(set(self.branch_ids)))
                or tuple(e.branch_id for e in self.events) != self.branch_ids):
            raise ValueError('paired Native loses complete both-view48 known branch denominator')


@dataclass(frozen=True, slots=True)
class MatrixPairedControl(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-paired/control'
    control_id: str
    branch_id: str
    view: str
    error: Decimal
    tolerance: Decimal
    disposition: str
    denominator_steps: int
    denominator_real_coordinates: int = 192

    def __post_init__(self):
        validate_stable_id(self.control_id)
        validate_stable_id(self.branch_id)
        for value in (self.error,self.tolerance):
            validate_decimal(value,field_name='paired independent residual',minimum=Decimal(0))
        if (self.view not in VIEWS or type(self.denominator_steps) is not int or self.denominator_steps < 1
                or type(self.denominator_real_coordinates) is not int or self.denominator_real_coordinates != 192
                or self.control_id != 'control.' + self.branch_id
                or self.disposition != ('SATISFIED' if self.error <= self.tolerance else 'VIOLATED')):
            raise ValueError('paired control drops full state/transition denominator or changes negative outcome')


@dataclass(frozen=True, slots=True)
class MatrixPairedFunctionalDiscrepancy(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-paired/functional-discrepancy'
    panel_id: str
    action_id: str
    physical_horizon: Decimal
    receiver_absolute_errors: tuple[Decimal, ...]
    relative_curve_error: Decimal | None
    weak_response: bool

    def __post_init__(self):
        validate_stable_id(self.panel_id)
        validate_stable_id(self.action_id)
        validate_decimal(self.physical_horizon,field_name='paired physical horizon',minimum=Decimal(0))
        if self.physical_horizon <= 0:
            raise ValueError('paired functional comparison requires a positive physical horizon')
        if len(self.receiver_absolute_errors) != 48:
            raise ValueError('paired functional comparison drops a declared receiver')
        for value in (*self.receiver_absolute_errors,*(() if self.relative_curve_error is None else (self.relative_curve_error,))):
            validate_decimal(value,field_name='paired functional difference',minimum=Decimal(0))
        if type(self.weak_response) is not bool or self.weak_response != (self.relative_curve_error is None):
            raise ValueError('paired functional comparison invents a resolved weak denominator')


@dataclass(frozen=True, slots=True)
class MatrixParameterPairedAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-paired/assessment'
    assessment_id: str
    source: ObjectIdentity
    native: ObjectIdentity
    forecast: ObjectIdentity
    controls: tuple[MatrixPairedControl, ...]
    functional_discrepancies: tuple[MatrixPairedFunctionalDiscrepancy, ...]
    scores: tuple[tuple[str,MatrixFactorResponseScore], ...]
    native_reference_pass: bool
    numerical_standard: ObjectIdentity | None
    numerical_disposition: str
    requested_horizons: int
    requested_views: tuple[str,str] = VIEWS
    unchanged_e3_transfer: str = 'UNENTERED_FROZEN_MODEL_CALIBRATION_CALLER_REQUIRED'
    standing: str = 'EXPOSED_PAIRED_FINITE_DT_NO_QUALIFICATION_OR_CONTINUUM_ENCLOSURE'

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        if (self.source.object_schema != MatrixParameterPairedSource.SCHEMA
                or self.native.object_schema != MatrixParameterPairedNative.SCHEMA
                or self.forecast.object_schema != MatrixParameterPairedForecast.SCHEMA
                or self.numerical_standard is not None and self.numerical_standard.object_schema != MatrixPairedNumericalStandard.SCHEMA
                or self.requested_views != VIEWS or len(self.controls) != 48
                or type(self.requested_horizons) is not int or self.requested_horizons < 1
                or len(self.functional_discrepancies) != 2*4*self.requested_horizons
                or len(self.scores) != 2*2*4*self.requested_horizons*48*5
                or any(type(control) is not MatrixPairedControl for control in self.controls)
                or any(type(row) is not MatrixPairedFunctionalDiscrepancy for row in self.functional_discrepancies)
                or any(view not in VIEWS or type(score) is not MatrixFactorResponseScore for view,score in self.scores)
                or type(self.native_reference_pass) is not bool or self.native_reference_pass != all(c.disposition == 'SATISFIED' for c in self.controls)
                or self.numerical_standard is None and self.numerical_disposition != DISPOSITION_WITHOUT_STANDARD
                or self.numerical_standard is not None and self.numerical_disposition not in ('COMPATIBLE_WITH_FROZEN_EMPIRICAL_STANDARD','VIOLATED_FROZEN_EMPIRICAL_STANDARD','UNRESOLVED_WEAK_FUNCTIONAL_DENOMINATOR','UNASSESSED_FAILED_NATIVE_REFERENCE')
                or self.unchanged_e3_transfer != 'UNENTERED_FROZEN_MODEL_CALIBRATION_CALLER_REQUIRED'
                or self.standing != 'EXPOSED_PAIRED_FINITE_DT_NO_QUALIFICATION_OR_CONTINUUM_ENCLOSURE'):
            raise ValueError('paired assessment drops denominators or invents adequacy/E3 qualification')
        panels = {score.panel_id for _,score in self.scores}
        actions = {score.action_id for _,score in self.scores}
        horizons = {score.horizon_step for _,score in self.scores}
        if len(panels) != 2 or len(actions) != 4 or len(horizons) != self.requested_horizons:
            raise ValueError('paired assessment substitutes its declared panel/action/horizon counts')
        keys = {(view,score.panel_id,score.action_id,score.horizon_step,score.receiver_index,score.predictor)
                for view,score in self.scores}
        expected = {(view,panel,action,horizon,receiver,predictor)
                    for view in VIEWS for panel in panels for action in actions for horizon in horizons
                    for receiver in range(48) for predictor in PREDICTORS}
        roles = {panel: {score.panel_role for _,score in self.scores if score.panel_id == panel} for panel in panels}
        if (len(keys) != len(self.scores) or keys != expected
                or any(len(values) != 1 for values in roles.values())
                or {next(iter(values)) for values in roles.values()} != {'COMMON_NOISE_PANEL','INDEPENDENT_FUTURE'}):
            raise ValueError('paired assessment substitutes the complete unique view/panel/action/horizon/receiver/predictor census')
        controls = {(control.view,control.branch_id) for control in self.controls}
        expected_controls = {(view,f'{view.lower()}.{panel}.{action}.{sign.lower()}')
                             for view in VIEWS for panel in panels for action in actions for sign in SIGNS}
        if (len(controls) != len(self.controls) or controls != expected_controls
                or any(control.denominator_steps != max(horizons) * (2 if control.view == 'FINE' else 1)
                       for control in self.controls)):
            raise ValueError('paired assessment substitutes the complete unique branch/view transition census')
        physical_horizons = {row.physical_horizon for row in self.functional_discrepancies}
        discrepancies = {(row.panel_id,row.action_id,row.physical_horizon) for row in self.functional_discrepancies}
        expected_discrepancies = {(panel,action,horizon) for panel in panels for action in actions for horizon in physical_horizons}
        if (len(physical_horizons) != self.requested_horizons or len(discrepancies) != len(self.functional_discrepancies)
                or discrepancies != expected_discrepancies
                or len({Fraction(physical)/step for physical,step in zip(sorted(physical_horizons),sorted(horizons),strict=True)}) != 1):
            raise ValueError('paired assessment substitutes the complete unique physical-horizon discrepancy census')


@dataclass(frozen=True, slots=True)
class MatrixPairedGridCell(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-paired/grid-cell'
    cell_id: str
    root_id: str
    independent_group_id: str
    coordinate: ObjectIdentity
    view: str
    disposition: str
    assessment: ObjectIdentity | None = None

    def __post_init__(self):
        for value in (self.cell_id,self.root_id,self.independent_group_id):
            validate_stable_id(value)
        if (self.coordinate.object_schema != 'empirical-lawhood/simulators/six-matrix-response/parameter-coordinate'
                or self.view not in VIEWS or self.disposition not in ('UNENTERED','COMPLETED','NO_ORIGIN','UNSUPPORTED_NUMERICAL_DOMAIN','UNKNOWN_CONTACT','FAILED','REFUSED_SOURCE')
                or self.assessment is not None and self.assessment.object_schema != MatrixParameterPairedAssessment.SCHEMA
                or (self.assessment is not None) != (self.disposition == 'COMPLETED')):
            raise ValueError('paired grid cell loses negative/unentered/unknown state')


@dataclass(frozen=True, slots=True)
class MatrixPairedGridCensus(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-paired/grid-census'
    grid_id: str
    allocation: ObjectIdentity
    cells: tuple[MatrixPairedGridCell, ...]
    requested_roots: int
    requested_independent_groups: int
    complete_independent_groups: tuple[str, ...]
    role: str = EXPOSED

    def __post_init__(self):
        validate_stable_id(self.grid_id)
        require_sorted_unique_ids(self.cells,attribute='cell_id',field_name='complete paired grid cells')
        if (self.allocation.object_schema != 'empirical-lawhood/matrix-parameter-history/allocation'
                or type(self.requested_roots) is not int or self.requested_roots < 1
                or type(self.requested_independent_groups) is not int or self.requested_independent_groups < 1
                or len(self.cells) != 2*self.requested_roots or any(type(cell) is not MatrixPairedGridCell for cell in self.cells)
                or self.role != EXPOSED):
            raise ValueError('paired grid drops complete coordinate/view/group denominator')
        roots = {cell.root_id for cell in self.cells}
        groups = {cell.independent_group_id for cell in self.cells}
        keys = {(cell.root_id,cell.view) for cell in self.cells}
        if (len(roots) != self.requested_roots or len(groups) != self.requested_independent_groups
                or len(keys) != len(self.cells) or keys != {(root,view) for root in roots for view in VIEWS}):
            raise ValueError('paired grid substitutes its complete unique root/view/group census')
        by_root = {}
        for cell in self.cells:
            if by_root.setdefault(cell.root_id,(cell.independent_group_id,cell.coordinate)) != (cell.independent_group_id,cell.coordinate):
                raise ValueError('paired grid changes a root coordinate or group between numerical views')
        complete = tuple(sorted(group for group in groups
            if all(cell.disposition == 'COMPLETED' for cell in self.cells if cell.independent_group_id == group)))
        if self.complete_independent_groups != complete:
            raise ValueError('paired grid completion does not equal the complete actual group cell outcomes')


def grid_census(allocation,cells,*,grid_id):
    roots = {r.root.root_id:r for r in allocation.roots}
    expected = {(root,view) for root in roots for view in VIEWS}
    if len(cells) != len(expected) or {(c.root_id,c.view) for c in cells} != expected:
        raise ValueError('paired grid omits complete declared root/view cells')
    for cell in cells:
        root = roots[cell.root_id]
        if cell.coordinate != root.coordinate or cell.independent_group_id != root.root.independent_group_id:
            raise ValueError('paired grid substitutes actual coordinate or matched root group')
    groups = tuple(sorted({r.root.independent_group_id for r in roots.values()}))
    complete = tuple(group for group in groups if all(c.disposition == 'COMPLETED' for c in cells if c.independent_group_id == group))
    from empirical_lawhood.adapters.methods.matrix_parameter_history.records import identity as history_identity
    return MatrixPairedGridCensus(grid_id,history_identity(allocation),tuple(sorted(cells,key=lambda c:c.cell_id)),len(roots),len(groups),complete)
