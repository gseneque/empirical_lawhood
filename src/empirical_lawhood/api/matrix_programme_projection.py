# SPDX-License-Identifier: MPL-2.0
"""Operation-local Matrix projections over authenticated C and actual children."""
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling, inherited_visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.planning.experiment_inputs import (
    ExperimentFileInputSelection, ExperimentInputBinding,
)
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, derived_outcome_access, lineage_parent_sort_key
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection, ExperimentInputDerivationResult


class MatrixProgrammePrerequisite(ValueError):
    """A genuine missing current operand, without a scientific result claim."""
    def __init__(self, phase, code, detail):
        super().__init__(detail)
        self.phase, self.code, self.detail = phase, code, detail


def record_identity(record):
    """Use actual current owner identifiers, never a substituted source hash."""
    from empirical_lawhood.kernel.experimental_design import UnitAllocation
    from empirical_lawhood.planning.campaigns import CampaignSpec
    if type(record) is CampaignSpec:
        return ObjectIdentity.from_record(record.campaign_id, record)
    if type(record) is UnitAllocation:
        return ObjectIdentity.from_record(record.allocation_id, record)
    if type(record) is ExperimentFileInputSelection:
        return ObjectIdentity.from_record(record.selection_id, record)
    pin = getattr(record, 'identity', None)
    if type(pin) is not ObjectIdentity or (pin.object_schema, pin.object_version, pin.object_fingerprint) != (
            record.SCHEMA, record.VERSION, record.fingerprint()):
        raise TypeError('programme projection requires its exact owning record identity')
    return pin


def _record_publication_request(context, phase, name, record, *, identity=None, lineage_parents=()):
    directory = context.metadata_directory(phase)
    relative = (directory / name).relative_to(context.writer.root.contract.canonical_path).as_posix()
    budget = context.plan.specification.operations.metadata_budget
    if record.canonical_size_bytes() > min(budget.output_bytes, budget.memory_bytes):
        raise ValueError('programme derived record exceeds the actual selected metadata budget')
    pin = record_identity(record) if identity is None else identity
    if type(pin) is not ObjectIdentity or (pin.object_schema, pin.object_version, pin.object_fingerprint) != (
            record.SCHEMA, record.VERSION, record.fingerprint()):
        raise ValueError('programme metadata substitutes its exact actual record identity')
    parents = tuple(sorted(set(lineage_parents), key=lineage_parent_sort_key))
    access = derived_outcome_access(OutcomeAccess.OUTCOME_BLIND, *(row.outcome_access for row in parents))
    ceilings = tuple(row.visibility_ceiling for row in parents)
    visibility = inherited_visibility(ceilings, access) if parents else VisibilityCeiling.PROSPECTIVE
    return ArtifactWriteRequest(pin.object_id, relative, record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', context.namespace + '.programme',
        directory.relative_to(context.writer.root.contract.canonical_path).as_posix(), record.canonical_bytes(),
        visibility, ceilings, access, lineage_parents=parents)


def _original_e3_selection_binding(selected):
    """Keep exact immutable companion content without its full decoded body.

    These hashes establish equality within the existing live read only. They
    neither authenticate a new selection nor retain an authorization verdict.
    Noncanonical/custom companions keep their original object comparison.
    """
    from empirical_lawhood.api.prospective_experiment import RetainedProspectiveExperiment
    from empirical_lawhood.kernel.serialization import CanonicalRecord

    if type(selected) is not RetainedProspectiveExperiment:
        return selected
    records = (selected.association, selected.instance, selected.candidate,
        selected.projection, selected.implementation, selected.draft)
    if (any(not isinstance(record, CanonicalRecord) or not record._is_cacheable() for record in records)
            or any(type(name) is not str or type(raw) is not bytes for name, raw in selected.payloads.items())):
        return selected
    return (RetainedProspectiveExperiment,
        tuple((type(record), record.SCHEMA, record.VERSION, record.fingerprint()) for record in records),
        tuple(sorted((name, len(raw), sha256(raw).hexdigest()) for name, raw in selected.payloads.items())),
        selected.original_input_access)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeE3Originals:
    public: object
    original_e3: object
    preparation: object
    original_preparation: object
    assay: object
    original_assay: object
    products: tuple
    require_current: object
    require_access: object


@dataclass(frozen=True, slots=True)
class MatrixProgrammeProjectionContext:
    """Transient actual operands; never serialized as another population index."""
    service: object
    plan: object
    inputs: object
    directory: Path
    bindings: dict
    observations: dict
    operation: object = None
    pending_bindings: dict = field(default_factory=dict)
    _read_lifetime: object = field(default=None, repr=False, compare=False)
    _e3_products: list = field(default_factory=list, repr=False, compare=False)
    phase_origins: dict = field(default_factory=dict, repr=False, compare=False)
    continuation_records: list = field(default_factory=list, repr=False, compare=False)
    amendment_records: list = field(default_factory=list, repr=False, compare=False)
    retained_execution_reports: dict = field(default_factory=dict, repr=False, compare=False)
    retained_terminal_pins: dict = field(default_factory=dict, repr=False, compare=False)
    retained_e3: list = field(default_factory=list, repr=False, compare=False)
    prepared_inputs: dict = field(default_factory=dict, repr=False, compare=False)
    authored_reports: dict = field(default_factory=dict, repr=False, compare=False)

    @property
    def writer(self):
        return self.service.artifact_writer

    @property
    def execution(self):
        return ExecutionSelection(self.plan.workers, self.plan.environment_id,
            self.plan.source_snapshot, self.plan.output_root)

    @property
    def design(self):
        return self.inputs.scientific_design

    @property
    def commitments(self):
        return self.inputs.commitments

    @property
    def namespace(self):
        return self.commitments.namespace

    def metadata_directory(self, phase):
        if phase in self.phase_origins:
            return self.phase_origins[phase].metadata_directory(phase)
        from empirical_lawhood.adapters.methods.matrix_researcher_programme.frontier import PHASES
        if phase not in PHASES:
            raise ValueError('unsupported current Matrix phase')
        return self.directory / 'derived' / phase

    def child_directory(self, phase):
        if phase in self.phase_origins:
            return self.phase_origins[phase].child_directory(phase)
        self.metadata_directory(phase)
        return self.directory / 'children' / phase

    def binding(self, phase):
        return self.bindings[phase]

    def report(self, phase):
        return self.observations[phase].report

    def method_inputs(self, phase):
        from empirical_lawhood.api.experiment_preparation import load_experiment_inputs
        binding = self.binding(phase)
        _, specification = self.bound_specification(binding)
        sources = self.writer.root.resolve(binding.sources.relative_path, for_write=False)
        return load_experiment_inputs(specification, sources, artifact_writer=self.writer).method_inputs

    def bound_specification(self, binding):
        from empirical_lawhood.api.matrix_researcher_programme_lineage import authenticate_phase_binding
        return authenticate_phase_binding(self.phase_origins.get(binding.phase, self), binding)

    def native_training_locator(self):
        from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import MatrixFiniteDtTrainingLocator
        from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_enabled
        from empirical_lawhood.api.recursive_authoring import load_authored_wave
        from empirical_lawhood.api.recursive_execution import _retained_plans
        from empirical_lawhood.api.native_training_banks import _read_instance
        directory = self.child_directory('train')
        if scientific_reconstruction_enabled():
            packet, draft, _, payloads = load_authored_wave(directory=directory,
                artifact_writer=self.writer, lazy_payloads=True)
            run, plan, _ = _retained_plans(payloads, draft)
            _, request, _ = _read_instance(payloads)
        else:
            from empirical_lawhood.api.experiment_execution_read import load_development_execution_controls
            packet, run, plan, _, _, _ = load_development_execution_controls(
                directory=directory, artifact_writer=self.writer)
        locator = MatrixFiniteDtTrainingLocator(directory.relative_to(
            self.writer.root.contract.canonical_path).as_posix(), run.run_plan_id,
            ObjectIdentity.from_record(packet.packet_id, packet),
            ObjectIdentity.from_record(plan.execution_plan_id, plan))
        if not scientific_reconstruction_enabled():
            from empirical_lawhood.api.matrix_programme_e4_inputs import _recorded_training_operands
            _, request = _recorded_training_operands(self.writer, locator)
        origin = self.phase_origins.get('train', self)
        if request.input_commitments != origin.plan.specification.input_commitments:
            raise PermissionError('programme TRAIN changes the original C publication')
        return locator

    @contextmanager
    def original_e3_products(self, *, selected, package, run_id, reveal_authority_id):
        """Reuse original science only within its still-live outer operation.

        Each consumer rechecks exact custody and current permission. Export
        metadata is still authenticated or published by its ordinary owner.
        """
        from empirical_lawhood.api.domain_composition.matrix_configured_protected_response.scientific_read import read_protected_e3_original_products
        if self._read_lifetime is None:
            reading = read_protected_e3_original_products(selected=selected, artifact_writer=self.writer,
                run_id=run_id, expected_package=package, reveal_authority_id=reveal_authority_id)
            del selected, package
            with reading as products:
                yield products
            return
        from empirical_lawhood.api.models import ExperimentPackage
        package_binding = ((ExperimentPackage, package.fingerprint())
            if type(package) is ExperimentPackage and package._is_cacheable() else package)
        binding = (_original_e3_selection_binding(selected), package_binding, run_id, reveal_authority_id)
        if not self._e3_products:
            reading = read_protected_e3_original_products(selected=selected, artifact_writer=self.writer,
                run_id=run_id, expected_package=package, reveal_authority_id=reveal_authority_id)
            del selected, package
            products = self._read_lifetime.enter_context(reading)
            self._e3_products.append((binding, products))
        else:
            del selected, package
            original, products = self._e3_products[0]
            if original != binding:
                raise PermissionError('programme changes its live original E3 read binding')
        products.require_current()
        try:
            yield products
        finally:
            products.require_current()

    @contextmanager
    def programme_e3_products(self):
        """Keep original evidence distinct from optional numerical reconstruction."""
        from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_enabled
        if scientific_reconstruction_enabled():
            selected, _, authority, package, run, _ = self.authority('e3')
            with self.original_e3_products(selected=selected, package=package,
                    run_id=run.run_plan_id, reveal_authority_id=authority.reveal_authority_id) as read:
                yield read
            return
        from .recorded_e3_products import recorded_programme_e3_products
        from .matrix_researcher_programme_lineage import retained_run_binding
        origin = self.phase_origins.get('e3', self)
        binding = ('RECORDED', retained_run_binding(origin, 'e3'), self.operation)
        if self._read_lifetime is None:
            with recorded_programme_e3_products(self) as read:
                yield read
            return
        if not self._e3_products:
            read = self._read_lifetime.enter_context(recorded_programme_e3_products(self))
            self._e3_products.append((binding, read))
        else:
            previous, read = self._e3_products[0]
            if previous != binding:
                raise PermissionError('programme changes its live recorded E3 product selection')
        read.require_access()
        yield read
        read.require_access()

    def require_original_access(self):
        """Refresh live original-product access without a whole byte replay."""
        pending, seen, products_seen = [self], set(), set()
        while pending:
            context = pending.pop()
            if id(context) in seen:
                continue
            seen.add(id(context))
            pending.extend(context.phase_origins.values())
            for _, products in context._e3_products:
                if id(products) in products_seen:
                    continue
                products_seen.add(id(products))
                products.require_access()

    @contextmanager
    def e3_originals(self, *, publish=False):
        from empirical_lawhood.api.matrix_researcher_programme_e4_lineage import programme_e3_originals
        with programme_e3_originals(self, publish=publish) as originals:
            yield originals

    def development_product(self, phase):
        from empirical_lawhood.api.matrix_researcher_programme_prepared_lineage import programme_development_product
        return programme_development_product(self, phase)

    def original_product(self, phase, schema):
        from empirical_lawhood.api.matrix_researcher_programme_lineage import programme_original_product
        return programme_original_product(self, phase, schema)

    def authority(self, phase, component_id=None):
        from empirical_lawhood.api.matrix_researcher_programme_lineage import select_programme_authority
        return select_programme_authority(self.phase_origins.get(phase, self), phase, component_id=component_id)

    def publish_record(self, phase, name, record, *, identity=None, lineage_parents=(), require_current=None):
        """Preserve actual inherited access for every outcome-bearing body."""
        request = _record_publication_request(self, phase, name, record,
            identity=identity, lineage_parents=lineage_parents)
        if require_current is not None:
            require_current()
        return self.writer.write(request)

    def publish_records(self, phase, records, *, lineage_parents=(), require_current=None):
        """Publish one finite copied-input group at its actual custody boundary.

        Existing members keep their original closed publication contracts.
        Custom writers keep each original single-record call and guard.
        """
        from empirical_lawhood.infrastructure.artifacts import supports_closed_batch_writes
        if not records:
            raise ValueError('programme record publication requires a nonempty group')
        if not supports_closed_batch_writes(self.writer):
            return tuple(self.publish_record(phase, name, record, identity=pin,
                lineage_parents=lineage_parents, require_current=require_current)
                for name, record, pin in records)
        budget = self.plan.specification.operations.metadata_budget
        if sum(record.canonical_size_bytes() for _, record, _ in records) > min(
                budget.output_bytes, budget.memory_bytes):
            raise ValueError('programme derived record group exceeds the selected metadata budget')
        requests = tuple(_record_publication_request(self, phase, name, record,
            identity=pin, lineage_parents=lineage_parents) for name, record, pin in records)
        paths = tuple(name for request in requests
            for name in (request.relative_path, request.relative_path + '.manifest.json'))
        with self.writer.root.read_paths(paths) as selected:
            existing = any(path.exists() or path.is_symlink() for path in selected.values())
        same_batch = False
        if existing:
            from empirical_lawhood.runtime.artifacts import artifact_publication_intent_relative_path
            publication = self.writer._preflight_publication(requests, compact_manifests=True).publication
            with self.writer.root.read_paths((publication.commit_marker_relative_path,
                    artifact_publication_intent_relative_path(publication.publication_scope,
                        publication.publication_batch_id))) as controls:
                same_batch = any(path.exists() or path.is_symlink() for path in controls.values())
        if existing and not same_batch:
            return tuple(self.publish_record(phase, name, record, identity=pin,
                lineage_parents=lineage_parents, require_current=require_current)
                for name, record, pin in records)
        if require_current is not None:
            require_current()
        try:
            return self.writer.write_compact_batch(requests)
        finally:
            if require_current is not None:
                require_current()

    def derive(self, phase, specification, records, *, files=(), output_name='inputs/sources.json',
            lineage_parents=(), require_current=None, sibling_selector=False):
        """Use the installed ordinary deriver with actual current typed inputs."""
        directory = self.metadata_directory(phase)
        originals = directory / 'original-inputs'
        selected_records = []
        bindings = []
        for key, record in sorted(records.items()):
            pin = record_identity(record)
            selected_records.append(('original-inputs/' + key + '.json', record, pin))
            bindings.append(ExperimentInputBinding(key, pin, key + '.json', record.canonical_size_bytes()))
        from empirical_lawhood.api.experiment_preparation import _protocol
        selector = ExperimentFileInputSelection('sources.' + specification.fingerprint(),
            _protocol(specification).protocol_id, tuple(bindings), tuple(files))
        selected_records.extend((('original-inputs/specification.json', specification, None),
            ('original-inputs/sources.json', selector, ObjectIdentity.from_record(selector.selection_id, selector))))
        publications = self.publish_records(phase, tuple(selected_records),
            lineage_parents=lineage_parents, require_current=require_current)
        metadata = originals / 'metadata' if sibling_selector else directory / 'produced'
        output = originals / 'derived-sources.json' if sibling_selector else metadata / output_name
        from empirical_lawhood.api.experiment_runtime_bindings import experiment_runtime_binding
        owner = experiment_runtime_binding(_protocol(specification))
        if owner is None or owner.derive_inputs is None:
            # A normal copied-input protocol has no preprocessing transition.
            # Its exact installed binder and preparer still validate every
            # operand; no fabricated deriver or weaker preparation is used.
            return self.result(phase, specification, selector,
                originals / 'specification.json', originals / 'sources.json', tuple(publications),
                lineage_parents=lineage_parents, require_current=require_current)
        result = self.service.derive_inputs(specification_path=originals / 'specification.json',
            source_selection_path=originals / 'sources.json', metadata_directory=metadata,
            output_selection_path=output, execution=self.execution)
        members = {row.materialization.relative_path: row for row in publications}
        for row in result.publications:
            previous = members.get(row.materialization.relative_path)
            if previous is not None and (previous.logical, previous.materialization,
                    previous.manifest_materialization) != (row.logical, row.materialization,
                    row.manifest_materialization):
                raise PermissionError('programme derivation aliases distinct actual publications')
            members[row.materialization.relative_path] = row
        if result.target_specification is None:
            if (result.preparation.specification_record != specification
                    or result.preparation.specification != specification.identity):
                raise PermissionError('same-protocol derivation substitutes its exact copied specification')
            result = replace(result, target_specification=specification,
                target_specification_path=originals / 'specification.json')
        return replace(result, publications=tuple(members[key] for key in sorted(members)))

    def result(self, phase, specification, selector, specification_path, selector_path,
            publications, *, original_specification=None, lineage_parents=(), require_current=None):
        """Wrap an actual direct composition in the normal derivation result."""
        from empirical_lawhood.api.experiment_preparation import load_experiment_inputs
        inputs = load_experiment_inputs(specification, selector_path, artifact_writer=self.writer)
        preparation = self.service.prepare(specification, scientific_inputs=inputs.scientific_inputs,
            method_inputs=inputs.method_inputs, execution=self.execution)
        raw = canonical_json_bytes({'schema': 'empirical-lawhood/operational/experiment-input-requirements',
            'version': '1.0.0', 'value': {'specification': specification.identity,
                'original_commitments': self.plan.specification.input_commitments.record,
                'source_selection': ObjectIdentity.from_record(selector.selection_id, selector),
                'native_contact': 'NONE', 'scientific_authority': 'NONE'}})
        relative = (self.metadata_directory(phase) / ('requirements.' + sha256(raw).hexdigest() + '.json')).relative_to(
            self.writer.root.contract.canonical_path).as_posix()
        parents = tuple(sorted(set(lineage_parents), key=lineage_parent_sort_key))
        access = derived_outcome_access(OutcomeAccess.OUTCOME_BLIND, *(row.outcome_access for row in parents))
        ceilings = tuple(row.visibility_ceiling for row in parents)
        visibility = inherited_visibility(ceilings, access) if parents else VisibilityCeiling.PROSPECTIVE
        if require_current is not None:
            require_current()
        requirements = self.writer.write(ArtifactWriteRequest('requirements.' + sha256(raw).hexdigest(),
            relative, 'empirical-lawhood/operational/experiment-input-requirements', ArtifactProfile.CANONICAL_JSON,
            'application/json', self.namespace + '.programme', Path(relative).parent.as_posix(), raw,
            visibility, ceilings, access, lineage_parents=parents))
        return ExperimentInputDerivationResult(original_specification or specification.identity, selector,
            Path(selector_path), preparation, (*publications, requirements), requirements,
            specification, Path(specification_path))
