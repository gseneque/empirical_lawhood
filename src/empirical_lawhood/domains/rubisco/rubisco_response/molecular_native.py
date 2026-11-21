# SPDX-License-Identifier: MPL-2.0
"""Passive molecular force-return custody and complete retained call census.

The existing native-subwork service owns entry, observations and recovery.
This module launches nothing. An admitted supplier must use that service's
invoke_native_subwork boundary and capture its return before scientific guards.
No corrected-xTB or synthetic ethane result is relabelled as enzyme evidence.
"""

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.raw_coupled_return import CoupledEvaluationRequest, RawCoupledReturn, capture_native_return, return_outputs
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.storage.contracts.artifacts import ArtifactManifest, ArtifactProfile, CanonicalTaskReceipt
from empirical_lawhood.execution.native_subwork import NativeSubworkBegin, NativeSubworkCallEntry, NativeSubworkCallReturn, NativeSubworkCompletion, NativeSubworkContact, NativeSubworkDefinition, NativeSubworkPartialOutput, NativeSubworkRoster, NativeSubworkState, require_native_completion_receipt
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation


@dataclass(frozen=True, slots=True)
class MolecularForceProbe(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/molecular-force-probe"
    probe_id: str
    representation: ObjectIdentity
    coordinates: ObjectIdentity
    physical_atom_count: int
    hamiltonian: ObjectIdentity
    native_method: ObjectIdentity
    native_stock: ObjectIdentity
    sources: tuple[ObjectIdentity, ...]
    unresolved_requirement_ids: tuple[str, ...]
    interpretation: str = "SELECTED_COMPLETE_FORCE_PROBE_WITHOUT_EXECUTION_AUTHORITY"

    def __post_init__(self):
        validate_stable_id(self.probe_id)
        for row in (self.representation, self.coordinates, self.hamiltonian, self.native_method, self.native_stock):
            exact(row, ObjectIdentity)
        if type(self.physical_atom_count) is not int or self.physical_atom_count <= 0:
            raise ValueError("force probe needs its complete physical atom denominator")
        identities(self.sources)
        if not {self.representation, self.coordinates, self.hamiltonian, self.native_method, self.native_stock}.issubset(self.sources):
            raise ValueError("force probe omits its exact selected molecular/Hamiltonian/native source closure")
        require_sorted_unique_strings(self.unresolved_requirement_ids, field_name="unresolved_requirement_ids")
        if self.interpretation != "SELECTED_COMPLETE_FORCE_PROBE_WITHOUT_EXECUTION_AUTHORITY":
            raise ValueError("force-probe selection cannot grant execution or scientific admission")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.probe_id, self)


def force_probe_request(probe, representation, producing_provenance, *, gradient_unit="Eh/ASH-Bohr"):
    exact(probe, MolecularForceProbe)
    exact(representation, MolecularRepresentation)
    exact(producing_provenance, NumericalProducingProvenance)
    if (probe.representation != representation.identity or probe.coordinates != representation.arrays.identity
            or probe.physical_atom_count != len(representation.atoms)):
        raise ValueError("force probe substitutes actual full molecular coordinates or atom order")
    if not set(representation.sources).issubset(probe.sources):
        raise ValueError("force probe drops the original molecular source closure")
    return CoupledEvaluationRequest(probe.probe_id + ".evaluation", probe.identity,
        representation.identity, representation.arrays.identity, producing_provenance.identity, len(representation.atoms),
        gradient_unit=gradient_unit)


def force_probe_definition(probe, representation, producing_provenance, *, parent_contact,
                           input_materialization_ids, streams=(), gradient_unit="Eh/ASH-Bohr"):
    """Pure definition; prepare/begin still authenticate actual inputs and authority."""
    request = force_probe_request(probe, representation, producing_provenance, gradient_unit=gradient_unit)
    sources = tuple(sorted({*probe.sources, probe.identity, producing_provenance.identity},
                           key=lambda row: row.object_id))
    return NativeSubworkDefinition(probe.probe_id, "rubisco-response.molecular-force-probe",
        parent_contact, request.identity, sources, producing_provenance.code_sources_sha256,
        producing_provenance.dependency_lock_sha256, input_materialization_ids, streams, return_outputs())


def force_probe_roster(probes, representations, producing_provenance, *, parent_contact, input_materialization_ids,
                      gradient_unit="Eh/ASH-Bohr"):
    """Derive the complete selected initial roster; publish it through progress."""
    if type(probes) is not tuple or type(representations) is not tuple or not probes or len(probes) != len(representations):
        raise ValueError("force roster needs every selected probe and exact physical representation")
    require_sorted_unique_ids(probes, attribute="probe_id", field_name="probes")
    definitions = tuple(force_probe_definition(probe, model, producing_provenance,
        parent_contact=parent_contact, input_materialization_ids=input_materialization_ids, gradient_unit=gradient_unit)
        for probe, model in zip(probes, representations, strict=True))
    return NativeSubworkRoster("selected.native-subwork", parent_contact, tuple(row.identity for row in definitions)), definitions


def capture_force_probe_return(probe, representation, producing_provenance,
                              energy, gradient, progress, entry, *, gradient_unit="Eh/ASH-Bohr"):
    """Retain actual returned values, including wrong shape, NaN and partial capture.

    This does not invoke the supplier, complete its call, erase open prerequisites
    or reinterpret an error as a successful molecular calculation.
    """
    request = force_probe_request(probe, representation, producing_provenance, gradient_unit=gradient_unit)
    expected = force_probe_definition(probe, representation, producing_provenance,
        parent_contact=entry.definition.parent_contact,
        input_materialization_ids=entry.definition.input_materialization_ids,
        streams=entry.definition.streams, gradient_unit=gradient_unit)
    if entry.definition != expected:
        raise ValueError("force return substitutes its actual selected native definition")
    return capture_native_return(request, energy, gradient, progress, entry)


@dataclass(frozen=True, slots=True)
class MolecularProbeOutcome(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/molecular-probe-outcome"
    request: CoupledEvaluationRequest
    definition: NativeSubworkDefinition
    state: NativeSubworkState
    begin: NativeSubworkBegin | None
    contact: NativeSubworkContact | None
    call_entry: NativeSubworkCallEntry | None
    call_return: NativeSubworkCallReturn | None
    completion: NativeSubworkCompletion | None
    receipt: CanonicalTaskReceipt | None
    outputs: tuple[ArtifactManifest, ...]
    partial_outputs: tuple[NativeSubworkPartialOutput, ...]
    partial_output_manifests: tuple[ArtifactManifest, ...]
    returned: RawCoupledReturn | None

    def __post_init__(self):
        exact(self.request, CoupledEvaluationRequest)
        exact(self.definition, NativeSubworkDefinition)
        if self.definition.configuration != self.request.identity or self.definition.outputs != return_outputs():
            raise ValueError("probe outcome changes its exact request or declared output slots")
        if type(self.state) is not NativeSubworkState:
            raise ValueError("probe outcome loses its actual native progress state")
        for row, kind in ((self.begin, NativeSubworkBegin), (self.contact, NativeSubworkContact),
                          (self.call_entry, NativeSubworkCallEntry), (self.call_return, NativeSubworkCallReturn),
                          (self.completion, NativeSubworkCompletion), (self.receipt, CanonicalTaskReceipt)):
            if row is not None:
                exact(row, kind)
        if (self.state is NativeSubworkState.NOT_ENTERED) != (self.begin is None):
            raise ValueError("probe outcome changes its recorded begin state")
        if (self.state in {NativeSubworkState.UNKNOWN_COMPLETION, NativeSubworkState.COMPLETED}) != (self.contact is not None):
            raise ValueError("probe outcome changes its recorded contact state")
        if self.begin is not None and self.begin.definition != self.definition.identity:
            raise ValueError("probe begin names another selected definition")
        if self.contact is not None and (self.begin is None
                or self.contact.begin.object_schema != self.begin.SCHEMA
                or self.contact.begin.object_version != self.begin.VERSION
                or self.contact.begin.object_fingerprint != self.begin.fingerprint()):
            raise ValueError("probe contact names another selected begin")
        if self.call_entry is not None and (self.contact is None
                or self.call_entry.definition != self.definition.identity
                or self.call_entry.contact.object_schema != self.contact.SCHEMA
                or self.call_entry.contact.object_version != self.contact.VERSION
                or self.call_entry.contact.object_fingerprint != self.contact.fingerprint()):
            raise ValueError("probe call observation names another physical contact")
        if self.call_return is not None and (self.call_entry is None
                or self.call_return.entry.object_schema != self.call_entry.SCHEMA
                or self.call_return.entry.object_version != self.call_entry.VERSION
                or self.call_return.entry.object_fingerprint != self.call_entry.fingerprint()):
            raise ValueError("probe return observation names another call entry")
        if any(type(rows) is not tuple for rows in (self.outputs, self.partial_outputs, self.partial_output_manifests)):
            raise ValueError("probe outcome needs the complete retained output and partial census")
        for row in self.outputs:
            exact(row, ArtifactManifest)
        if self.contact is None and (self.outputs or self.partial_outputs):
            raise ValueError("probe cannot retain native outputs before any recorded contact")
        for row in self.partial_outputs:
            exact(row, NativeSubworkPartialOutput)
            if row.definition != self.definition.identity:
                raise ValueError("probe partial bytes belong to another definition")
            if (self.contact is None or row.contact.object_schema != self.contact.SCHEMA
                    or row.contact.object_fingerprint != self.contact.fingerprint()):
                raise ValueError("probe partial bytes belong to another actual contact")
        if len(self.partial_outputs) != len(self.partial_output_manifests):
            raise ValueError("probe outcome drops an original partial-prefix manifest")
        for row, manifest in zip(self.partial_outputs, self.partial_output_manifests, strict=True):
            exact(manifest, ArtifactManifest)
            if (manifest.logical.profile is not ArtifactProfile.NATIVE_SUBWORK_PREFIX
                    or manifest.logical.payload_schema != "empirical-lawhood/runtime/native-subwork-received-prefix"
                    or (manifest.materialization.size_bytes, manifest.materialization.physical_sha256)
                    != (row.received_size_bytes, row.received_physical_sha256)
                    or {value.identity for value in manifest.logical.lineage_parents} != {row.definition, row.contact}):
                raise ValueError("probe partial manifest changes its exact received bytes or original lineage")
        output_ids = tuple(row.logical.logical_artifact_id for row in self.outputs)
        if output_ids != tuple(sorted(set(output_ids))):
            raise ValueError("probe output census duplicates or reorders retained products")
        completed = self.state is NativeSubworkState.COMPLETED
        if completed != (self.completion is not None) or completed != (self.receipt is not None):
            raise ValueError("probe cannot invent a known completion or drop its original receipt")
        if completed:
            require_native_completion_receipt(self.completion, self.receipt)
            if (self.receipt.run_id != self.definition.parent_contact.run_id
                    or self.receipt.implementation_commit != self.definition.parent_contact.implementation_commit
                    or not set(self.definition.input_materialization_ids).issubset(self.receipt.input_materialization_ids)):
                raise ValueError("probe receipt changes its original run, source or exact input custody")
            if (self.completion.definition != self.definition.identity
                    or self.completion.contact.object_schema != self.contact.SCHEMA
                    or self.completion.contact.object_version != self.contact.VERSION
                    or self.completion.contact.object_fingerprint != self.contact.fingerprint()
                    or self.call_entry is not None and self.completion.contact != self.call_entry.contact
                    or set(self.completion.output_ids) | set(self.completion.omitted_output_ids)
                    != {row.output_id for row in self.definition.outputs}):
                raise ValueError("probe completion changes its full output/omission denominator")
            if tuple(sorted((*self.completion.consumed_streams, *self.completion.unconsumed_streams,
                             *self.completion.unknown_streams), key=lambda row: row.object_id)) != self.definition.streams:
                raise ValueError("probe completion changes its complete random-stream denominator")
            expected_ids = {self.receipt.task_id + ".output." + key for key in self.completion.output_ids}
            if set(output_ids) != expected_ids:
                raise ValueError("probe completion drops a retained output from its census")
            for row in self.outputs:
                if (row.logical not in self.receipt.output_logical_artifacts
                        or row.materialization not in self.receipt.output_materializations):
                    raise ValueError("probe output differs from its actual completion receipt")
        if self.returned is not None:
            exact(self.returned, RawCoupledReturn)
            if not completed or self.returned.request != self.request.identity:
                raise ValueError("probe cannot admit an unreceipted or substituted raw return")
            raw = self.returned.canonical_bytes()
            manifest = tuple(row for row in self.outputs if row.logical.payload_schema == RawCoupledReturn.SCHEMA)
            if (len(manifest) != 1 or manifest[0].materialization.size_bytes != len(raw)
                    or manifest[0].materialization.physical_sha256 != sha256(raw).hexdigest()):
                raise ValueError("probe return differs from its actual retained canonical bytes")
            if any(row is not None and row.artifact_manifest not in self.outputs
                   for row in (self.returned.energy, self.returned.gradient)):
                raise ValueError("probe capture substitutes a retained raw operand")
        elif completed and any(row.logical.payload_schema == RawCoupledReturn.SCHEMA for row in self.outputs):
            raise ValueError("probe outcome drops its actual completed raw return")

    @property
    def cost(self):
        return InquiryCost(None, None, None) if self.completion is None else self.completion.cost


@dataclass(frozen=True, slots=True)
class MolecularProbeCensus(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/molecular-probe-census"
    roster: NativeSubworkRoster
    outcomes: tuple[MolecularProbeOutcome, ...]

    def __post_init__(self):
        exact(self.roster, NativeSubworkRoster)
        if type(self.outcomes) is not tuple:
            raise ValueError("probe census must preserve its immutable complete outcomes")
        for row in self.outcomes:
            exact(row, MolecularProbeOutcome)
        if (tuple(row.definition.identity for row in self.outcomes) != self.roster.subworks
                or any(row.definition.parent_contact != self.roster.parent_contact
                       or row.definition.roster_id != self.roster.roster_id for row in self.outcomes)):
            raise ValueError("probe census drops, adds or substitutes a frozen selected native call")


def read_force_probe_outcome(probe, representation, producing_provenance, definition, progress, *,
                             gradient_unit="Eh/ASH-Bohr"):
    """Read all progress, including uncertain/partial outcomes, without re-entry."""
    request = force_probe_request(probe, representation, producing_provenance, gradient_unit=gradient_unit)
    expected = force_probe_definition(probe, representation, producing_provenance,
        parent_contact=definition.parent_contact, input_materialization_ids=definition.input_materialization_ids,
        streams=definition.streams, gradient_unit=gradient_unit)
    if definition != expected:
        raise ValueError("retained probe reader substitutes the selected native definition")
    found = progress.inspect(definition)
    if found.definition != definition:
        raise ValueError("retained probe progress belongs to another selected definition")
    returned = None
    if found.state is NativeSubworkState.COMPLETED:
        original = progress.recover(definition)
        if original != found:
            raise ValueError("completed probe changed during retained recovery")
        selected = tuple(row for row in found.outputs if row.logical.payload_schema == RawCoupledReturn.SCHEMA)
        if selected:
            if len(selected) != 1:
                raise ValueError("completed probe duplicates its raw return")
            size = selected[0].materialization.size_bytes
            raw = b"".join(progress.iter_completed_output(definition, "raw.return"))
            returned = decode_canonical_bytes(raw, RawCoupledReturn, maximum_bytes=size)
    return MolecularProbeOutcome(request, definition, found.state, found.begin, found.contact,
        found.call_entry, found.call_return, found.completion, found.receipt, found.outputs,
        found.partial_output_records, found.partial_outputs, returned)


def read_force_probe_census(probes, representations, producing_provenance, definitions, progress, *, roster,
                            gradient_unit="Eh/ASH-Bohr"):
    """Preserve every selected force probe; no cherry-picked successful subset."""
    if any(type(rows) is not tuple for rows in (probes, representations, definitions)):
        raise ValueError("force census needs complete immutable selected rosters")
    require_sorted_unique_ids(probes, attribute="probe_id", field_name="probes")
    if (not probes or len(probes) != len(representations) or len(probes) != len(definitions)
            or tuple(row.subwork_id for row in definitions) != tuple(row.probe_id for row in probes)):
        raise ValueError("force census drops a selected endpoint/call definition")
    if tuple(row.identity for row in definitions) != roster.subworks:
        raise ValueError("force census drops part of the original selected native roster")
    outcomes = tuple(read_force_probe_outcome(probe, model, producing_provenance, definition, progress, gradient_unit=gradient_unit)
        for probe, model, definition in zip(probes, representations, definitions, strict=True))
    return MolecularProbeCensus(roster, outcomes)
