# SPDX-License-Identifier: MPL-2.0
"""Retain and read original operational cost evidence through guarded custody."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.storage.development_native_custody import read_development_native_payload
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.execution.work_costs import MAX_COST_EVIDENCE_BYTES, MAX_COST_SOURCE_BYTES, CostCoverage, CostQuantity, CostWorkScope, WorkCostAccount, WorkCostMeasurement, WorkCostOutcome, record_cost_evidence, summarize_work_cost


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("cost evidence repeats a JSON field")
        result[key] = value
    return result


def _json(raw):
    def invalid(value):
        raise ValueError("cost evidence contains a nonfinite JSON number: " + value)
    return json.loads(raw, object_pairs_hook=_pairs, parse_float=Decimal, parse_constant=invalid)


def _field(document, pointer):
    value = document
    for key in pointer:
        if type(value) is dict and key in value:
            value = value[key]
        elif type(value) is list and key.isdecimal() and str(int(key)) == key and int(key) < len(value):
            value = value[int(key)]
        else:
            raise ValueError("cost evidence omits its selected original JSON field/index")
    return value


def _measured_value(document, pointer):
    if pointer is None:
        return None
    value = _field(document, pointer)
    if type(value) is dict and set(value) == {"decimal"}:
        value = value["decimal"]
    if value is None:
        return None
    if type(value) not in (str, int, Decimal):
        raise ValueError("cost measurement source is not an exact decimal observation")
    try:
        result = Decimal(value)
    except InvalidOperation as error:
        raise ValueError("cost source does not contain the stated measured number") from error
    if not result.is_finite() or result < 0:
        raise ValueError("cost source contains a negative or nonfinite observation")
    return result


def _record_body(source, document):
    identity = source.record_identity
    if identity is None:
        return None
    if (type(document) is not dict or set(document) != {"schema", "version", "value"}
            or (document["schema"], document["version"]) != (identity.object_schema, identity.object_version)
            or type(document["value"]) is not dict):
        raise ValueError("cost evidence changes its original canonical record envelope")
    return document["value"]


def _physical_work(account, documents, evidence_bytes):
    """A changed receipt or a contact alias cannot create a second attempt."""
    sources = {row.evidence_id:row for row in account.evidence}
    scopes = {row.scope_id:row for row in account.work}
    keys, seen = {}, set()
    for row in account.work:
        source = sources[row.evidence_id]
        body = _record_body(source, documents[row.evidence_id])
        schema = None if source.record_identity is None else source.record_identity.object_schema
        if schema in ('empirical-lawhood/runtime/canonical-task-receipt',
                      'empirical-lawhood/runtime/native-effect-contact'):
            key = ('attempt', body['run_id'], body['task_id'], body['attempt_id'])
            if schema.endswith('/canonical-task-receipt') and row.outcome.value != body['operational_status']:
                raise ValueError("cost account changes the original attempt's operational outcome")
            if schema.endswith('/native-effect-contact') and row.outcome is not WorkCostOutcome.UNKNOWN:
                raise ValueError("contact alone supplies no known completion or recovery cost work")
        elif schema == 'empirical-lawhood/runtime/native-subwork-definition':
            contact = body['parent_contact']['value']
            key = ('native', contact['run_id'],contact['task_id'],contact['attempt_id'],body['subwork_id'])
            # The original roster and contact chain establish which entered
            # subwork this is. No supplied label can turn a selected slot into work.
            witnesses = [sources[name] for name in row.witness_evidence_ids]
            by_schema = {}
            for witness in witnesses:
                if witness.record_identity is not None:
                    by_schema.setdefault(witness.record_identity.object_schema, []).append(witness)
            begins = [value for value in by_schema.get('empirical-lawhood/runtime/native-subwork-begin', ())
                      if documents[value.evidence_id]['value']['definition'] == row.subject.to_document()]
            contacts = [value for value in by_schema.get('empirical-lawhood/runtime/native-subwork-contact', ())
                        if any(documents[value.evidence_id]['value']['begin'] == begin.record_identity.to_document() for begin in begins)]
            rosters = [value for value in by_schema.get('empirical-lawhood/runtime/native-subwork-roster', ())
                       if row.subject.to_document() in documents[value.evidence_id]['value']['subworks']]
            if len(begins) != 1 or len(contacts) != 1 or len(rosters) != 1:
                raise ValueError("native cost work lacks its exact original entered roster/begin/contact chain")
            roster = documents[rosters[0].evidence_id]['value']
            if roster['parent_contact'] != body['parent_contact'] or roster['roster_id'] != body['roster_id']:
                raise ValueError("native cost work changes its original roster and parent contact")
            parent = scopes.get(row.parent_scope_id)
            if roster['parent_subwork'] is not None and (parent is None or parent.subject.to_document() != roster['parent_subwork']):
                raise ValueError("nested cost scope changes its original native parent")
            if roster['parent_subwork'] is None and (parent is None or parent.subject.object_schema not in (
                    'empirical-lawhood/runtime/canonical-task-receipt','empirical-lawhood/runtime/native-effect-contact')):
                raise ValueError("initial native work must retain its ordinary containing attempt")
            completions = [value for value in by_schema.get('empirical-lawhood/runtime/native-subwork-completion', ())
                           if documents[value.evidence_id]['value']['definition'] == row.subject.to_document()
                           and documents[value.evidence_id]['value']['contact'] == contacts[0].record_identity.to_document()]
            if row.outcome is not WorkCostOutcome.UNKNOWN and (
                    len(completions) != 1 or documents[completions[0].evidence_id]['value']['operational_status'] != row.outcome.value):
                raise ValueError("native cost outcome lacks its exact original completion")
            if completions:
                from empirical_lawhood.execution.native_subwork import NativeSubworkCompletion, require_native_completion_receipt
                from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
                completed = decode_canonical_bytes(evidence_bytes[completions[0].evidence_id],
                    NativeSubworkCompletion,maximum_bytes=MAX_COST_SOURCE_BYTES)
                receipts = []
                for witness in by_schema.get(CanonicalTaskReceipt.SCHEMA, ()):
                    receipt = decode_canonical_bytes(evidence_bytes[witness.evidence_id],
                        CanonicalTaskReceipt,maximum_bytes=MAX_COST_SOURCE_BYTES)
                    try:
                        require_native_completion_receipt(completed,receipt)
                    except ValueError:
                        continue
                    receipts.append(receipt)
                if len(receipts) != 1:
                    raise ValueError("native cost completion lacks its exact primary receipt")
        else:
            if row.outcome not in (WorkCostOutcome.OBSERVED_INVOCATION, WorkCostOutcome.RECOVERY):
                raise ValueError("generic cost evidence can bind an observation, not manufacture an executed attempt")
            key = ('observation',source.sha256)
        if key in seen:
            raise ValueError("original work appears twice through changed receipts or source aliases")
        seen.add(key); keys[row.scope_id] = key
    for row in account.work:
        key = keys[row.scope_id]
        if key[0] != 'native':
            continue
        current = scopes.get(row.parent_scope_id)
        while current is not None and keys[current.scope_id][0] == 'native':
            if keys[current.scope_id][1:4] != key[1:4]:
                raise ValueError("nested cost work substitutes its original ordinary attempt")
            current = scopes.get(current.parent_scope_id)
        if current is None or keys[current.scope_id] != ('attempt', *key[1:4]):
            raise ValueError("native costs require their original containing ordinary attempt")
        ordinary = documents[current.evidence_id]['value']
        original_parent = documents[row.evidence_id]['value']['parent_contact']['value']
        if any(ordinary[name] != original_parent[name] for name in (
                'run_id','task_id','attempt_id','implementation_commit','input_materialization_ids')):
            raise ValueError("native costs change the containing attempt's original source or inputs")


def validate_work_cost_evidence(*, account: WorkCostAccount, evidence_bytes: dict[str, bytes]) -> dict:
    """Check complete sources, exact values and actual operational identities.

    Source bytes and numbers are authenticated here. The observer still owns
    physical instrumentation and its declared inclusive/exclusive scope. This
    does not certify the meter, import a scientific source or infer a baseline.
    """
    if type(account) is not WorkCostAccount:
        raise TypeError("cost evidence requires a typed current account")
    account.__post_init__()
    if set(evidence_bytes) != {row.evidence_id for row in account.evidence}:
        raise ValueError("cost evidence changes its complete original source census")
    from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
    from empirical_lawhood.execution.native_effects import NativeEffectContact
    from empirical_lawhood.execution.native_subwork import NativeSubworkBegin, NativeSubworkContact, NativeSubworkCompletion, NativeSubworkDefinition, NativeSubworkRoster
    original_codecs = {kind.SCHEMA:kind for kind in (CanonicalTaskReceipt,NativeEffectContact,NativeSubworkBegin,
        NativeSubworkContact,NativeSubworkCompletion,NativeSubworkDefinition,NativeSubworkRoster)}
    documents = {}
    for source in account.evidence:
        raw = evidence_bytes[source.evidence_id]
        if type(raw) is not bytes or (len(raw),sha256(raw).hexdigest()) != (source.size_bytes,source.sha256):
            raise ValueError("original cost evidence bytes differ from their exact source binding")
        document = _json(raw)
        _record_body(source, document)
        if source.record_identity is not None and source.record_identity.object_schema in original_codecs:
            decode_canonical_bytes(raw,original_codecs[source.record_identity.object_schema],maximum_bytes=MAX_COST_SOURCE_BYTES)
        documents[source.evidence_id] = document
    _physical_work(account, documents, evidence_bytes)
    for row in account.measurements:
        if _measured_value(documents[row.evidence_id], row.value_pointer) != row.value:
            raise ValueError("stated cost measurement differs from its original observed value")
    for row in account.billing_windows:
        original = documents[row.evidence_id]
        if (_measured_value(original,row.value_pointer) != row.billed_usd
                or _field(original,row.resource_pointer) != row.resource_id
                or _field(original,row.started_pointer) != row.started_at_utc
                or _field(original,row.ended_pointer) != row.ended_at_utc):
            raise ValueError("billed value, resource or interval differs from its original observation")
    return summarize_work_cost(account)


def _relative(directory, writer, *, for_write):
    destination = Path(directory)
    root = Path(writer.root.contract.canonical_path)
    if not destination.is_absolute() or '..' in destination.parts:
        raise ValueError("cost custody requires an explicit absolute guarded destination")
    relative = destination.relative_to(root).as_posix()
    return relative, writer.root.resolve(relative, for_write=for_write)


def retain_work_cost_account(*, account: WorkCostAccount, artifact_writer, output_directory: Path,
                            evidence_paths: dict[str, Path] | None = None,
                            evidence_bytes: dict[str, bytes] | None = None) -> dict:
    """Publish original permitted operational metadata and its derived account.

    Read scientific sources through their owning access-controlled workflow
    before selecting permitted cost metadata. Raw paths here supply no outcome
    access or scientific qualification. A failed publication is retained; it
    neither repeats work nor overwrites an earlier cost account.
    """
    if type(account) is not WorkCostAccount:
        raise TypeError("cost custody requires its exact typed account")
    if (evidence_paths is None) == (evidence_bytes is None):
        raise ValueError("select original paths or already admitted bytes, exactly once")
    selected = evidence_paths if evidence_paths is not None else evidence_bytes
    if set(selected) != {row.evidence_id for row in account.evidence}:
        raise ValueError("cost custody requires every original source and no replacement")
    relative, destination = _relative(output_directory, artifact_writer, for_write=True)
    if destination.exists():
        raise FileExistsError("cost account requires a new explicit custody destination")
    sources = {} if evidence_bytes is None else dict(evidence_bytes)
    if evidence_paths is not None:
        for row in account.evidence:
            path = Path(evidence_paths[row.evidence_id])
            if not path.is_absolute():
                raise ValueError("select exact absolute original cost evidence paths")
            sources[row.evidence_id] = read_bounded_bytes(path, maximum_bytes=row.size_bytes)
    report = validate_work_cost_evidence(account=account,evidence_bytes=sources)
    packet_id = 'work-cost.' + account.fingerprint()[:24]
    def request(name, payload, schema, profile, media_type='application/json'):
        return ArtifactWriteRequest(packet_id + '.' + name.removesuffix('.json'), relative + '/' + name,
            schema,profile,media_type,packet_id,relative,payload,
            VisibilityCeiling.DEVELOPMENT_ONLY,(),OutcomeAccess.DEVELOPMENT_VISIBLE)
    requests = [request('account.json',account.canonical_bytes(),account.SCHEMA,ArtifactProfile.CANONICAL_JSON),
                request('summary.json',canonical_json_bytes(report),report['schema'],ArtifactProfile.CANONICAL_JSON)]
    requests.extend(request(f'evidence.{index:04}.json',sources[row.evidence_id],
        'empirical-lawhood/source/checksummed-uninterpreted-public-bytes',ArtifactProfile.RAW_SOURCE_BYTES,'text/plain')
        for index,row in enumerate(account.evidence))
    artifact_writer.write_batch(tuple(requests))
    return {"directory":str(destination),"account_path":str(destination / 'account.json'),
            "summary_path":str(destination / 'summary.json'),"summary":report,
            "original_evidence_count":len(sources),"new_execution":False}


def read_work_cost_account(*, directory: Path, artifact_writer) -> dict:
    """Authenticate retained bytes and reconstruct accounting without execution."""
    relative, destination = _relative(directory, artifact_writer, for_write=False)
    def read(name, schema, profile, maximum):
        path = relative + '/' + name
        manifest = artifact_writer.read_manifest(path)
        if (manifest.materialization.relative_path != path or manifest.logical.payload_schema != schema
                or manifest.logical.profile is not profile):
            raise ValueError("retained cost member changes its original path or contract")
        return read_development_native_payload(artifact_writer,manifest,maximum_bytes=maximum)
    account = decode_canonical_bytes(read('account.json',WorkCostAccount.SCHEMA,
        ArtifactProfile.CANONICAL_JSON,MAX_COST_EVIDENCE_BYTES),WorkCostAccount,maximum_bytes=MAX_COST_EVIDENCE_BYTES)
    sources = {row.evidence_id:read(f'evidence.{index:04}.json',
        'empirical-lawhood/source/checksummed-uninterpreted-public-bytes',ArtifactProfile.RAW_SOURCE_BYTES,MAX_COST_SOURCE_BYTES)
        for index,row in enumerate(account.evidence)}
    report = validate_work_cost_evidence(account=account,evidence_bytes=sources)
    if read('summary.json',report['schema'],ArtifactProfile.CANONICAL_JSON,MAX_COST_EVIDENCE_BYTES) != canonical_json_bytes(report):
        raise ValueError("retained cost summary differs from its original complete evidence")
    return {"directory":str(destination),"account":account,"summary":report,"new_execution":False,
            "read_cpu_seconds":None,"read_elapsed_seconds":None,"read_peak_rss_bytes":None}


def project_attempt_cost_work(original, *, parent_scope_id=None):
    """Project one actual receipt/contact already obtained through its owner."""
    from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
    from empirical_lawhood.execution.native_effects import NativeEffectContact

    if type(original) is CanonicalTaskReceipt:
        if original.operational_status.value not in ('SUCCEEDED','FAILED'):
            raise ValueError("cost work requires an actually attempted terminal receipt or original uncertain contact")
        object_id, outcome = original.receipt_id, WorkCostOutcome(original.operational_status.value)
    elif type(original) is NativeEffectContact:
        object_id, outcome = 'contact.' + original.fingerprint(), WorkCostOutcome.UNKNOWN
    else:
        raise TypeError("attempt cost work requires its original receipt or native contact")
    evidence = record_cost_evidence(original,evidence_id='evidence.'+original.fingerprint(),object_id=object_id,
        description='Original ordinary task attempt receipt or uncertain contact.')
    scope = CostWorkScope('work.'+original.fingerprint(),evidence.record_identity,evidence.evidence_id,
        (evidence.evidence_id,),outcome,'Original attempted work, with unmeasured exclusive overhead retained.',parent_scope_id)
    return {"work":scope,"evidence":(evidence,),"measurements":(),
            "evidence_bytes":{evidence.evidence_id:original.canonical_bytes()}}


def project_native_cost_work(inspection, *, roster, parent_scope_id, coverage: CostCoverage):
    """Bind an authenticated original entered subwork and its recorded costs.

    The caller selects the original meter's inclusion rule explicitly. Original
    peak RSS remains a component observation: this projection does not promote
    a process-lifetime maximum into the current account's aggregate peak.
    """
    from empirical_lawhood.execution.native_subwork import NativeSubworkInspection, NativeSubworkRoster, require_native_completion_receipt
    if (type(inspection) is not NativeSubworkInspection or type(roster) is not NativeSubworkRoster
            or type(coverage) is not CostCoverage or inspection.begin is None or inspection.contact is None):
        raise ValueError("native cost projection requires original entered work, roster and explicit meter coverage")
    definition = inspection.definition
    if (definition.identity not in roster.subworks or roster.parent_contact != definition.parent_contact
            or roster.roster_id != definition.roster_id):
        raise ValueError("native cost projection changes the selected original roster")
    rows, payloads = [], {}
    def bind(record, object_id):
        source = record_cost_evidence(record,evidence_id='evidence.'+record.fingerprint(),object_id=object_id,
            description='Original native operational record: '+record.SCHEMA)
        rows.append(source); payloads[source.evidence_id] = record.canonical_bytes()
        return source
    source = bind(definition,definition.subwork_id)
    bind(roster,roster.roster_id)
    bind(inspection.begin,inspection.contact.begin.object_id)
    contact_id = (inspection.completion.contact.object_id if inspection.completion is not None else
                  inspection.call_entry.contact.object_id if inspection.call_entry is not None else
                  'contact.'+inspection.contact.fingerprint())
    bind(inspection.contact,contact_id)
    outcome = WorkCostOutcome.UNKNOWN
    measurements = []
    scope_id = 'work.'+definition.fingerprint()
    if inspection.completion is not None:
        if inspection.receipt is None:
            raise ValueError("native cost projection requires its original completion receipt")
        require_native_completion_receipt(inspection.completion,inspection.receipt)
        completion = bind(inspection.completion,inspection.receipt.task_id+'.completion')
        bind(inspection.receipt,inspection.receipt.receipt_id)
        outcome = WorkCostOutcome(inspection.completion.operational_status.value)
        for field, quantity in (('cpu_seconds',CostQuantity.CPU_SECONDS),
                                ('wall_seconds',CostQuantity.ELAPSED_SECONDS),
                                ('retained_bytes',CostQuantity.RETAINED_BYTES)):
            measurements.append(WorkCostMeasurement(scope_id+'.'+field,scope_id,coverage,quantity,
                getattr(inspection.completion.cost,field),completion.evidence_id,('value','cost','value',field),
                inspection.completion.cost_scope))
    scope = CostWorkScope(scope_id,source.record_identity,source.evidence_id,
        tuple(sorted(row.evidence_id for row in rows)),outcome,
        'Original entered native subwork. Parent and child measurements retain their original inclusion scopes.',parent_scope_id)
    return {"work":scope,"evidence":tuple(sorted(rows,key=lambda row:row.evidence_id)),
            "measurements":tuple(sorted(measurements,key=lambda row:row.measurement_id)),"evidence_bytes":payloads,
            "original_component_peak_rss_bytes":None if inspection.completion is None else inspection.completion.peak_rss_bytes}


__all__ = ["project_attempt_cost_work", "project_native_cost_work", "read_work_cost_account",
           "retain_work_cost_account", "validate_work_cost_evidence"]
