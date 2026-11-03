#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Explicit source-bound continuations; scientific methods belong to adapters.

Import and --help perform no scientific entry. Each selected invocation has new
paths, producing-source attribution, complete receipts and measured custody.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import resource
import shutil
import time
import traceback
import zipfile

D = Decimal


def file_sha256(path):
    digest = sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def census(root):
    return {p.relative_to(root).as_posix(): {'bytes': p.stat().st_size, 'sha256': file_sha256(p)}
            for p in sorted(root.rglob('*')) if p.is_file()}


def cpu():
    return sum(r.ru_utime + r.ru_stime for r in
               (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))


def write_json(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def add_custody_location_arguments(parser):
    """Require the complete operational selection for a new invocation."""
    for name in ('working-root', 'logs-root', 'durable-root', 'custody-mount'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('custody-filesystem', 'custody-profile'):
        parser.add_argument('--' + name, required=True)


def selected_locations(args):
    """Resolve explicit, disjoint operational paths before creating anything.

    Existing records retain their exact paths and profiles. A new invocation
    selects all locations and its filesystem/profile explicitly; this changes
    operational custody, not the scientific record or resource budget.
    """
    names = ('working_root', 'logs_root', 'durable_root', 'custody_mount',
             'custody_filesystem', 'custody_profile')
    values = tuple(getattr(args, name, None) for name in names)
    if any(value is None for value in values):
        raise ValueError('explicit custody requires all three paths, mount, filesystem and profile')
    working, logs, durable, mount = (Path(value) for value in values[:4])
    if any(not path.is_absolute() or path != path.resolve() for path in (working, logs, durable, mount)):
        raise ValueError('select absolute canonical operational paths without symlink aliases')
    if working == mount or not working.is_relative_to(mount):
        raise ValueError('selected custody root must be below its explicit mount')
    roots = (working, logs, durable)
    if any(a == b or a.is_relative_to(b) or b.is_relative_to(a)
           for i, a in enumerate(roots) for b in roots[i + 1:]):
        raise ValueError('selected working, logs and durable trees must be disjoint')
    protected = [Path(args.project_root).resolve()]
    if getattr(args, 'prior_root', None) is not None:
        protected.append(Path(args.prior_root).resolve())
    if any(a == b or a.is_relative_to(b) or b.is_relative_to(a) for a in roots for b in protected):
        raise ValueError('selected outputs overlap the producing checkout or historical custody')
    filesystem, profile = values[4:]
    if not isinstance(filesystem, str) or not filesystem or not isinstance(profile, str) or not profile:
        raise ValueError('select the exact custody filesystem and profile')
    return working, logs, durable, mount, (filesystem,), profile


class SelectedProgramme:
    def __init__(self, args):
        self.project = args.project_root.resolve(strict=True)
        self.terminal_product_format = getattr(args, 'terminal_product_format', 'documents')
        if self.terminal_product_format not in ('documents', 'references'):
            raise ValueError('select documents or references for terminal product presentation')
        self.label = args.label
        (self.root, self.logs, self.durable, custody_mount,
         custody_filesystems, custody_profile) = selected_locations(args)
        for path in (self.root, self.logs, self.durable):
            if path.exists() or path.is_symlink():
                raise FileExistsError('selected fresh continuation path already exists: ' + str(path))
        for path in (self.root, self.logs):
            path.mkdir(parents=True)
        self.started, self.started_cpu = time.monotonic(), cpu()
        self.preflight = json.loads(args.source_preflight.read_text())
        archive = Path(self.preflight['archive'])
        if (archive.stat().st_size != self.preflight['bytes']
                or sha256(archive.read_bytes()).hexdigest() != self.preflight['sha256']):
            raise ValueError('producing source archive differs from its selected preflight')
        with zipfile.ZipFile(archive) as bundle:
            archive_names = bundle.namelist()
            declared_names = [row['path'] for row in self.preflight['members']]
            if (len(archive_names) != len(set(archive_names))
                    or len(declared_names) != len(set(declared_names))
                    or set(archive_names) != set(declared_names)):
                raise ValueError('producing archive loses complete member census')
            for row in self.preflight['members']:
                raw = bundle.read(row['path'])
                if len(raw) != row['bytes'] or sha256(raw).hexdigest() != row['sha256']:
                    raise ValueError('producing archive member differs: ' + row['path'])
        from empirical_lawhood.api.recursive_authoring import implementation_binding
        from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
        from empirical_lawhood.runtime.artifacts import ExternalRootContract
        self.source = implementation_binding(self.project)
        if self.source.to_document() != self.preflight['implementation']:
            raise ValueError('selected project differs from archived actual producing implementation')
        import empirical_lawhood
        if Path(empirical_lawhood.__file__).resolve().parent != self.project / 'src/empirical_lawhood':
            raise ValueError('selected interpreter imports a different package checkout')
        self.launcher_sha = sha256(Path(__file__).read_bytes()).hexdigest()
        archived_members = {row['path']: row for row in self.preflight['members']}
        expected_package = {f'src/empirical_lawhood/{name}': digest for name, digest in self.source.package_sources}
        actual_package = {name: row['sha256'] for name, row in archived_members.items()
                          if name.startswith('src/empirical_lawhood/')}
        if actual_package != expected_package:
            raise ValueError('archived complete package inventory differs from actual producing binding')
        if (archived_members.get('uv.lock', {}).get('sha256') != self.source.dependency_lock_sha256
                or archived_members.get('scripts/run_applied_el_broad_programme.py', {}).get('sha256') != self.launcher_sha):
            raise ValueError('archived lock or launcher differs from its actual producing bytes')
        contract = ExternalRootContract(getattr(args, 'storage_root_id', None) or 'storage.applied-el.' + args.label,
            'Explicitly selected source-bound scientific continuation', str(self.root), str(custody_mount),
            custody_profile, 0, allowed_filesystem_types=custody_filesystems)
        self.plane = ExternalArtifactPlane(GuardedExternalRoot(contract))
        self.plane.root.verify(for_write=True)
        self.report = {'status': 'ENTERED', 'label': args.label, 'domain': args.domain,
                       'producing_source': self.source.to_document(), 'source_archive': self.preflight['archive'],
                       'source_archive_sha256': self.preflight['sha256'], 'launcher_sha256': self.launcher_sha,
                       'selected_roots': {'tmpfs': str(self.root), 'logs': str(self.logs), 'durable': str(self.durable)},
                       'phases': {}, 'waves': {}, 'native_contacts': 0, 'new_biological_units': 0,
                       'new_physical_units': 0, 'cost_limits': None, 'automatic_retry': False,
                       'unknown_costs': ['Historical engineering and interpretation', 'Final record writes and process exit tail']}
        if getattr(args, 'working_root', None) is not None:
            self.report['selected_roots'] = {'working': str(self.root), 'logs': str(self.logs),
                                            'durable': str(self.durable)}
            self.report['selected_custody'] = {'mount': str(custody_mount),
                'filesystem_types': list(custody_filesystems), 'profile': custody_profile}
        write_json(self.logs / 'programme-entry.json', self.report)

    def check_source(self):
        from empirical_lawhood.api.recursive_authoring import implementation_binding
        if (implementation_binding(self.project) != self.source
                or sha256(Path(__file__).read_bytes()).hexdigest() != self.launcher_sha):
            raise ValueError('actual producing package or launcher changed before an operation')

    def measured(self, name, call):
        start, start_cpu = time.monotonic(), cpu()
        size = sum(v['bytes'] for v in census(self.root).values())
        outcome = 'COMPLETED'
        try:
            return call()
        except BaseException as error:
            outcome = type(error).__name__ + ': ' + str(error)
            raise
        finally:
            self.report['phases'][name] = {'status': outcome, 'cpu_seconds': cpu() - start_cpu,
                'wall_seconds': time.monotonic() - start,
                'retained_bytes_growth': sum(v['bytes'] for v in census(self.root).values()) - size,
                'nonadditive_nested_window': True}

    def origins(self, draft, parent=None, *, parents=None):
        from empirical_lawhood.kernel.provenance import ObjectIdentity
        from empirical_lawhood.planning.recursive_input_origins import RecursiveInputOrigin, RecursiveInputOriginKind, RecursiveInputOrigins
        if parent is not None and parents is not None:
            raise ValueError('select singular or multiple contribution parents')
        selected = tuple(parents) if parents is not None else (() if parent is None else (parent,))
        if len({row.contribution_id for row in selected}) != len(selected):
            raise ValueError('duplicate contribution parents')
        rows = []
        for external in draft.external_inputs:
            matches = tuple((owner, product) for owner in selected for product in owner.products
                if product.artifact.sha256 == external.expected_content_sha256)
            if len(matches) > 1:
                raise ValueError('ambiguous authentic contributed product')
            if matches:
                owner, product = matches[0]
                rows.append(RecursiveInputOrigin(external.input_id, RecursiveInputOriginKind.CONTRIBUTION,
                    external.expected_content_sha256, product.role.value,
                    ObjectIdentity.from_record(owner.contribution_id, owner), product.product_id, product.producing_receipt))
            else:
                rows.append(RecursiveInputOrigin(external.input_id, RecursiveInputOriginKind.SOURCE,
                    external.expected_content_sha256, external.scientific_role))
        return RecursiveInputOrigins(tuple(sorted(rows, key=lambda v: v.input_id)))

    def bindings(self, draft, records):
        from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
        from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
        by_hash = {r.fingerprint(): r for r in records}
        bindings = []
        for external in draft.external_inputs:
            record = by_hash.get(external.expected_content_sha256)
            if record is None:
                continue
            relative = f'programme-inputs/{draft.draft_id}/{external.input_id}.json'
            self.plane.write(ArtifactWriteRequest(external.logical_artifact_id, relative, record.SCHEMA,
                ArtifactProfile.CANONICAL_JSON, 'application/json', draft.draft_id, f'programme-inputs/{draft.draft_id}',
                record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
            bindings.append((external.input_id, self.root / relative))
        return tuple(bindings)

    def wave(self, name, draft, records, *, parent=None, contribution=None, decision=None, supplier_directory=None,
             human_fork=False, parents=None, contributions=None):
        from empirical_lawhood.api.recursive_authoring import author_recursive_wave
        from empirical_lawhood.api.recursive_execution import read_recursive_wave, run_recursive_wave
        from empirical_lawhood.api.recursive_inquiry import author_inquiry_successor, run_inquiry_successor
        from empirical_lawhood.kernel.provenance import ObjectIdentity
        directory = self.root / name
        start, start_cpu = time.monotonic(), cpu()
        retained_before = sum(v['bytes'] for v in census(self.root).values())
        result = {'draft': draft.to_document(), 'directory': str(directory)}
        self.report['waves'][name] = result
        try:
            if contribution is not None and contributions is not None:
                raise ValueError('select singular or multiple contribution directories')
            contribution_arguments = ({'contribution_dirs': tuple(contributions)} if contributions is not None
                else {'contribution_dir': contribution})
            bindings = self.measured(name + '.source-bindings', lambda: self.bindings(draft, records))
            origins = self.origins(draft, parent, parents=parents)
            self.check_source()
            if decision is None:
                self.measured(name + '.author', lambda: author_recursive_wave(draft=draft, project_root=self.project,
                    artifact_writer=self.plane, output_dir=directory, input_bindings=bindings, origins=origins,
                    **contribution_arguments))
            else:
                self.measured(name + '.author', lambda: author_inquiry_successor(decision_directory=decision,
                    supplier_directory=supplier_directory, origins=origins, project_root=self.project,
                    artifact_writer=self.plane, output_dir=directory, input_bindings=bindings, **contribution_arguments,
                    human_fork_draft=draft if human_fork else None))
            self.check_source()
            runner = run_recursive_wave if decision is None else run_inquiry_successor
            result['run_report'] = self.measured(name + '.run', lambda: runner(directory=directory,
                project_root=self.project, artifact_writer=self.plane,
                terminal_product_format=self.terminal_product_format))
            self.report['native_contacts'] += result['run_report']['new_native_contact_count']
            report, products, _, _ = self.measured(name + '.read', lambda: read_recursive_wave(
                directory=directory, artifact_writer=self.plane, include_products=True,
                terminal_product_format=self.terminal_product_format))
            result['report'] = report
            result['operational_census'] = products['operational_census']
            result['receipt_identities'] = {attempt: ObjectIdentity.from_record(receipt.receipt_id, receipt).to_document()
                for attempt, receipt in products['attempt_receipts'].items()}
            before = census(directory)
            recovered = self.measured(name + '.recover', lambda: read_recursive_wave(
                directory=directory, artifact_writer=self.plane, include_products=True,
                terminal_product_format=self.terminal_product_format))
            if recovered[0] != report or recovered[1] != products or census(directory) != before:
                raise ValueError('receipt recovery changed scientific products or custody')
            result['recovery'] = {'new_native_contacts': 0, 'scheduler_entered': False, 'exact_census_unchanged': True}
            if report['status'] != 'SUCCEEDED':
                raise ValueError('selected scientific operation did not complete: ' + name)
            return directory, products, result
        except BaseException as error:
            result['exception'] = {'type': type(error).__name__, 'message': str(error)}
            if (directory / 'authored-wave.json').exists():
                try:
                    report, products, _, _ = read_recursive_wave(directory=directory, artifact_writer=self.plane,
                        include_products=True, terminal_product_format=self.terminal_product_format)
                    result['report'], result['operational_census'] = report, products['operational_census']
                except BaseException as read_error:
                    result['read_error'] = {'type': type(read_error).__name__, 'message': str(read_error)}
            raise
        finally:
            result['measured_invocation'] = {'cpu_seconds': cpu() - start_cpu,
                'wall_seconds': time.monotonic() - start,
                'retained_bytes': sum(v['bytes'] for v in census(self.root).values()) - retained_before}

    def contribution(self, name, directory):
        from empirical_lawhood.api.recursive_contributions import authenticate_recursive_contribution, export_recursive_contribution
        target = self.root / name
        self.check_source()
        self.measured(name + '.export', lambda: export_recursive_contribution(directory=directory, output_dir=target,
            project_root=self.project, artifact_writer=self.plane))
        authenticated = self.measured(name + '.authenticate', lambda: authenticate_recursive_contribution(
            directory=target, artifact_writer=self.plane))
        return target, authenticated[2]

    def decision_cost_paths(self, name, directory, result, existing_measured_event_paths=None):
        """Preserve exact existing costs; an aggregate cannot identify many attempts."""
        from empirical_lawhood.api.recursive_inquiry import retain_measured_attempt_cost
        if existing_measured_event_paths is not None:
            return tuple(existing_measured_event_paths)
        if len(result.get('operational_census', ())) != 1 or result.get('measured_invocation') is None:
            result['attempt_cost_attribution'] = {'measured_event_paths': [],
                'actual_attempt_costs': 'UNKNOWN', 'aggregate_invocation_reallocated': False}
            return ()
        invocation = result['measured_invocation']
        measured_dir = self.root / (name + '-measured-attempt')
        self.measured(name + '.retain-cost', lambda: retain_measured_attempt_cost(
            authoring_directory=directory, cpu_seconds=D(str(invocation['cpu_seconds'])),
            wall_seconds=D(str(invocation['wall_seconds'])), retained_bytes=D(invocation['retained_bytes']),
            artifact_writer=self.plane, output_dir=measured_dir))
        return ((measured_dir / 'measured-attempt-cost.json').relative_to(self.root).as_posix(),)

    def decision(self, name, directory, result, *, endpoint, question, next_draft=None,
                 next_manifest=None, previous=None, human_choice=None,
                 act_outcomes=('useful-supply',), next_manifests=None, existing_measured_event_paths=None):
        """Commit a receipt-backed domain outcome before authoring its successor."""
        from empirical_lawhood.api.recursive_authoring import load_authored_wave
        from empirical_lawhood.api.recursive_inquiry import (
            commit_inquiry_decision, project_inquiry_state, read_inquiry_decision,
        )
        from empirical_lawhood.kernel.recursive_inquiry import InquiryCost, InquiryOutcomeChoice, InquirySpecification, identity
        from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
        from empirical_lawhood.planning.recursive_inquiry import InquiryAction, InquiryAlternative, InquiryMenu, InquiryPolicy
        from empirical_lawhood.runtime.recursive_inquiry import InquiryStateSources, InquiryWaveSource
        packet, draft, _, _ = load_authored_wave(directory=directory, artifact_writer=self.plane)
        # State projection authenticates existing events against the actual
        # attempt/receipt. A whole-wave measurement stays separate in its report.
        measured_paths = self.decision_cost_paths(name, directory, result, existing_measured_event_paths)
        paths = () if previous is None else (previous.relative_to(self.root).as_posix(),)
        sources = InquiryStateSources((InquiryWaveSource(directory.relative_to(self.root).as_posix(),
            identity(packet, packet.packet_id), True),),
            measured_event_paths=measured_paths,
            previous_decision_paths=paths)
        predecessor = None if previous is None else read_inquiry_decision(directory=previous, artifact_writer=self.plane)[1]['specification.json']
        outcomes = ('scoped-failure', 'unresolved', 'useful-supply')
        if not set(act_outcomes) <= set(outcomes) or (act_outcomes != ('useful-supply',) and human_choice is None):
            raise ValueError('a new question from adverse evidence requires an explicit human-directed choice')
        choices = tuple(InquiryOutcomeChoice(outcome, ('stop', 'use')
            if next_draft is not None and outcome in act_outcomes else ('stop',)) for outcome in outcomes)
        specification = InquirySpecification('inquiry.' + self.label + '.' + name, question,
            ('The code-owned supplier/consumer independently determines scientific adequacy.',
             'An assessed numerical procedure does not grant biological or physical qualification.'),
            draft.operations[0].config_identity, choices, endpoint,
            'Use actual authenticated source/receipt products; preserve adverse and missing-evidence dispositions.',
            predecessor_specification=None if predecessor is None else identity(predecessor, predecessor.specification_id))
        cutoff = InformationCutoff('cutoff.' + self.label + '.' + name, endpoint.clock_id, CausalPhase.POST_OUTCOME, D(0))
        state = self.measured(name + '.project-state', lambda: project_inquiry_state(
            specification=specification, state_id='state.' + self.label + '.' + name,
            information_cutoff=cutoff, sources=sources, artifact_writer=self.plane))
        sid, tid = identity(specification, specification.specification_id), identity(state, state.state_id)
        alternatives = [InquiryAlternative('stop', sid, tid, InquiryAction.STOP,
            ('scoped-failure', 'unresolved', 'useful-supply'), (), D(0), InquiryCost(D(0), D(0), D(0)))]
        if next_draft is not None:
            if next_manifest is None and not next_manifests:
                raise ValueError('ACT lacks its authenticated proposed supplier manifest')
            if next_manifest is not None and next_manifests is not None:
                raise ValueError('select singular or multiple proposed manifests')
            origins = self.origins(next_draft, next_manifest, parents=next_manifests)
            operation = next_draft.operations[0]
            alternatives.append(InquiryAlternative('use', sid, tid, InquiryAction.ACT, tuple(act_outcomes),
                tuple(row.evidence_id for row in state.stock), D(2), InquiryCost(None, None, None),
                identity(next_draft, next_draft.draft_id), operation.config_identity,
                identity(origins, 'inquiry-input-origins'), operation.selection.selection_id))
        menu = InquiryMenu('menu.' + self.label + '.' + name, sid, tid, tuple(alternatives))
        policy = InquiryPolicy('policy.' + self.label + '.' + name, sid, InquiryCost(None, None, None), None, None, None)
        target = self.root / (name + '-inquiry-decision')
        self.check_source()
        decision_packet, records = self.measured(name + '.commit-decision', lambda: commit_inquiry_decision(
            specification=specification, state=state, sources=sources, menu=menu, policy=policy,
            campaign=draft.campaign, right=draft.campaign.decision_rights[0],
            actor_id=draft.campaign.decision_rights[0].decision_maker_id, project_root=self.project,
            artifact_writer=self.plane, output_dir=target, human_choice=human_choice))
        result['committed_inquiry'] = {'packet': decision_packet.to_document(), 'state': state.to_document(),
            'decision': records['decision.json'].to_document(),
            'intent': None if records.get('intent.json') is None else records['intent.json'].to_document()}
        if read_inquiry_decision(directory=target, artifact_writer=self.plane) != (decision_packet, records):
            raise ValueError('saved inquiry does not reproduce the committed decision')
        expected = 'stop' if next_draft is None else 'use'
        if records['decision.json'].selected_alternative_id != expected:
            raise ValueError('actual supplier outcome refused the selected successor; retain its scientific disposition')
        return target

    def finish(self):
        self.report['actual_registered_operations'] = sum(len(v.get('operational_census', ())) for v in self.report['waves'].values())
        self.report['custody_members'] = census(self.root)
        self.report['measured_through_pre_copy'] = {'cpu_seconds': cpu() - self.started_cpu,
                                                   'wall_seconds': time.monotonic() - self.started}
        write_json(self.logs / 'programme-report.json', self.report)
        before = census(self.root)
        shutil.copytree(self.root, self.durable)
        if census(self.root) != before or census(self.durable) != before:
            raise ValueError('full durable custody copy differs from actual operational bytes')
        shutil.copy2(self.logs / 'programme-entry.json', self.durable / 'programme-entry.json')
        shutil.copy2(self.logs / 'programme-report.json', self.durable / 'programme-report.json')
        cost = {'cpu_seconds': cpu() - self.started_cpu, 'wall_seconds': time.monotonic() - self.started,
                'operational_member_count': len(before), 'operational_retained_bytes': sum(v['bytes'] for v in before.values()),
                'full_durable_copy_exact': True, 'unmeasured_tail': 'Final cost writes and process exit',
                'native_contacts': self.report['native_contacts']}
        write_json(self.logs / 'invocation-cost.json', cost)
        write_json(self.durable / 'invocation-cost.json', cost)
        print(json.dumps({'status': self.report['status'], 'report': str(self.durable / 'programme-report.json'), **cost}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--launch-selected-programme', action='store_true')
    parser.add_argument('--domain', choices=('rubisco', 'battery'))
    parser.add_argument('--label')
    parser.add_argument('--project-root', type=Path, default=Path('/home/chevre/gs-ml/empirical_lawhood'))
    parser.add_argument('--source-preflight', type=Path)
    add_custody_location_arguments(parser)
    args = parser.parse_args()
    if not args.launch_selected_programme:
        parser.error('explicit --launch-selected-programme is required for scientific entry')
    if (args.domain is None or args.source_preflight is None or not args.label
            or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.label)):
        parser.error('select exact domain, source preflight and lowercase path label')
    programme = SelectedProgramme(args)
    try:
        if args.domain == 'rubisco':
            run_rubisco(programme)
        else:
            run_battery(programme)
        programme.report['status'] = 'SELECTED_CONTINUATION_COMPLETED'
    except BaseException as error:
        programme.report['status'] = 'RETAINED_ADVERSE_ATTEMPT'
        programme.report['exception'] = {'type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()}
        raise
    finally:
        programme.finish()


def run_rubisco(programme):
    from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry import science as portfolio
    from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry import recursive_translation as portfolio_drafts
    from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry.source_manifest import (
        INITIAL_CANDIDATE_IDS, SOURCE_MANIFEST, SOURCE_PATHS,
    )
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.recursive_inquiry import preview_inquiry_successor

    def source_intake():
        sources = {}
        selected = dict(SOURCE_PATHS)
        target = programme.root / 'portfolio-source-originals'
        target.mkdir()
        for source_id, filename, size, digest in SOURCE_MANIFEST:
            path = Path(selected[source_id])
            if path.is_symlink():
                raise ValueError('selected original source path is a link')
            raw = path.read_bytes()
            if len(raw) != size or sha256(raw).hexdigest() != digest:
                raise ValueError('selected original source changed: ' + source_id)
            with (target / (source_id + '-' + filename)).open('xb') as stream:
                stream.write(raw)
            sources[source_id] = raw
        return portfolio.source_audit_from_bytes(sources, candidate_ids=INITIAL_CANDIDATE_IDS)

    from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry.challenge import YAMORI_BYTES, YAMORI_SHA256

    def new_primary_intake():
        path = Path('/tmp/empirical-lawhood-applied-el-20261011-reopen01/rubisco-portfolio-source-audit/yamori2026-primary.xml')
        raw = path.read_bytes()
        if path.is_symlink() or len(raw) != YAMORI_BYTES or sha256(raw).hexdigest() != YAMORI_SHA256:
            raise ValueError('newly admitted primary-source bytes differ before scientific entry')
        with (programme.root / 'yamori2026-primary.xml').open('xb') as stream:
            stream.write(raw)
        return raw

    yamori = programme.measured('five-finalists.new-primary-intake', new_primary_intake)
    source = programme.measured('portfolio.source-intake', source_intake)
    supplier_draft = portfolio_drafts.supply_draft(source)
    supply_dir, products, result = programme.wave('portfolio-supply', supplier_draft, (source,))
    supplier = unique_product(products, portfolio.PortfolioSupply)
    _, retained_draft, _, _ = load_authored_wave(directory=supply_dir, artifact_writer=programme.plane)
    parent = portfolio_drafts.describe_contributions(retained_draft, products)[0]
    successor = programme.measured('portfolio.preview-successor', lambda: preview_inquiry_successor(
        supplier_directory=supply_dir, artifact_writer=programme.plane))
    decision = programme.decision('portfolio-supply', supply_dir, result, endpoint=supplier.scope,
        question=portfolio.QUESTION, next_draft=successor, next_manifest=parent)
    contribution, authenticated = programme.contribution('portfolio-contribution', supply_dir)
    if authenticated != parent:
        raise ValueError('portable export changed the prior committed actual contribution')
    instance = portfolio.authentic_candidate(supplier)
    use_dir, products, result = programme.wave('portfolio-use', successor, (instance,), parent=parent,
        contribution=contribution, decision=decision, supplier_directory=supply_dir)
    assessment = unique_product(products, portfolio.PortfolioAssessment)
    programme.report['portfolio_assessment'] = assessment.to_document()
    programme.decision('portfolio-use', use_dir, result, endpoint=assessment.scope,
        question='What exact candidate frontier and supported model-use scope follow from the independently checked portfolio?',
        previous=decision)
    kinetic_products = run_rubisco_cycle(programme, source)
    from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry.challenge import challenge_finalists
    challenge = programme.measured('five-finalists.source-and-mechanism-challenge', lambda: challenge_finalists(
        supplier, assessment, kinetic_products, yamori))
    with (programme.root / 'finalist-challenge.json').open('xb') as stream:
        stream.write(challenge.canonical_bytes())
    programme.report['finalist_challenge'] = challenge.to_document()
    if programme.report['native_contacts'] != 0:
        raise ValueError('selected pure Rubisco continuation unexpectedly contacted a native provider')


def unique_product(products, product_type):
    values = tuple(record for outputs in products['records'].values() for record in outputs.values()
                   if type(record) is product_type)
    if len(values) != 1:
        raise ValueError('operation did not retain one complete authentic ' + product_type.__name__)
    return values[0]


def run_rubisco_cycle(programme, macro_source):
    from empirical_lawhood.adapters.methods.rubisco_cycle_constraints import contracts as cycle
    from empirical_lawhood.adapters.methods.rubisco_cycle_constraints import recursive_translation as drafts
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.recursive_inquiry import preview_inquiry_successor

    paths = {
        'cummins2018-primary.xml': Path('/tmp/empirical-lawhood-applied-el-20261011-reopen01/rubisco-cycle-source-audit/cummins2018-primary.xml'),
        'cummins2019-response.html': Path('/tmp/empirical-lawhood-rubisco-20261009/public-inputs/followup-1/cummins2019-response.html'),
    }

    def source_intake():
        target = programme.root / 'cycle-source-originals'
        target.mkdir()
        raw_sources = {}
        for name, size, digest in cycle.SOURCE_MEMBERS:
            path = paths[name]
            raw = path.read_bytes()
            if path.is_symlink() or len(raw) != size or sha256(raw).hexdigest() != digest:
                raise ValueError('selected mechanism original bytes changed before scientific entry')
            with (target / name).open('xb') as stream:
                stream.write(raw)
            raw_sources[name] = raw
        return cycle.source_audit_from_bytes(raw_sources)

    mechanism = programme.measured('cycle.source-intake', source_intake)
    first = drafts.instance_from_source(macro_source, instance_id='instance.rubisco-cycle.first-use',
        candidate_ids=('gp.wt', 'wilson2017-row17'))
    second = drafts.instance_from_source(macro_source, instance_id='instance.rubisco-cycle.subsequent-use',
        candidate_ids=('nt.a369.t391i', 'potato.ps3', 'potato.pst'))
    initial = drafts.supply_draft(mechanism, successor=first, reuse_successor=second)
    directory, products, result = programme.wave('cycle-supply', initial, (mechanism,))
    product = unique_product(products, cycle.CycleSupply)
    programme.report['cycle_procedure_assessment'] = product.check.to_document()
    previous_decision = None
    use_products = []
    for name, instance in (('cycle-use', first), ('cycle-reuse', second)):
        _, retained_draft, _, _ = load_authored_wave(directory=directory, artifact_writer=programme.plane)
        parent = drafts.describe_contributions(retained_draft, products)[0]
        successor = programme.measured(name + '.preview', lambda: preview_inquiry_successor(
            supplier_directory=directory, artifact_writer=programme.plane))
        decision = programme.decision(directory.name, directory, result, endpoint=product.scope,
            question=cycle.QUESTION, next_draft=successor, next_manifest=parent, previous=previous_decision)
        contribution, authenticated = programme.contribution(directory.name + '-contribution', directory)
        if authenticated != parent:
            raise ValueError('cycle portable parent changed the already committed actual inquiry intent')
        supplier_directory = directory
        directory, products, result = programme.wave(name, successor, (macro_source, instance), parent=parent,
            contribution=contribution, decision=decision, supplier_directory=supplier_directory)
        product = unique_product(products, cycle.CycleUseProduct)
        use_products.append(product)
        previous_decision = decision
    programme.report['cycle_uses'] = [product.to_document() for product in use_products]
    programme.decision('cycle-reuse', directory, result, endpoint=product.scope,
        question='Which release-only mechanism claims are excluded at the assessed scope, and what exact candidate evidence remains missing?',
        previous=previous_decision)
    return tuple(use_products)


def run_battery(programme):
    from empirical_lawhood.adapters.methods.battery_thermal_inquiry import science
    from empirical_lawhood.adapters.methods.battery_thermal_inquiry import recursive_translation as drafts
    from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import BatteryInquirySupply, QUESTION
    from empirical_lawhood.adapters.methods.battery_thermal_inquiry.operation_bindings import (
        BatteryInquiryAssessedInstance, BatteryInquiryNativeCensus, native_census,
    )
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.recursive_inquiry import preview_inquiry_successor
    from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition

    source = programme.measured('battery.source-intake', lambda: _battery_source_intake(programme))
    draft = drafts.supply_draft(source)
    directory, products, result = programme.wave('battery-supply', draft, (source,))
    supplier = unique_product(products, BatteryInquirySupply)
    current = supplier
    recipients, censuses = [], []
    previous_decision = None
    for following_name in ('battery-use', 'battery-reuse', None):
        census_product = unique_product(products, BatteryInquiryNativeCensus)
        phase = 'supply' if type(current) is BatteryInquirySupply else current.assessment.instance.phase
        if census_product != native_census(current, phase):
            raise ValueError('battery actual current census differs from retained scientific product')
        censuses.append(census_product)
        programme.report['battery_native_censuses'] = [row.to_document() for row in censuses]
        programme.report['battery_procedure_assessment'] = supplier.check.to_document()
        programme.report['battery_instance_assessments'] = [row.assessment.to_document() for row in recipients]
        allocations = programme.measured(directory.name + '.cost-allocation', lambda: science.cost_allocations(
            supplier, tuple(row.assessment for row in recipients)))
        programme.report['battery_shared_cost_allocations'] = [row.to_document() for row in allocations]
        programme.report['battery_scientific_summary'] = {
            'current_phase': phase, 'current_disposition': current.disposition.value,
            'selected_model': supplier.check.selected_model,
            'conditional_sampled_numerical_scope': True, 'simulated_parameter_families': 1,
            'controller': 'EXPLICITLY_APPROXIMATE_SOURCE_CONSERVATIVE_HYBRID',
            'exact_pointwise_ideal_cccv_established': False,
            'physical_independent_units': 0, 'biological_independent_units': 0,
            'whole_time_physical_plating_degradation_and_global_optimality': 'UNEVALUABLE',
            'complete_total_cost_superiority': 'UNEVALUABLE',
            'formal_qualification_or_issue_authority': False,
            'shared_allocations_are_independent_trials': False,
        }
        programme.report['battery_native_accounting'] = {
            'observed_native_effect_entry_count': programme.report['native_contacts'],
            'retained_native_operation_attempts': sum(len(row.get('operational_census', ()))
                for row in programme.report.get('waves', {}).values()),
            'retained_attempt_receipts': sum(len(row.get('receipt_identities', {}))
                for row in programme.report.get('waves', {}).values()),
            'charging_forecast_provider_attempts': sum(row.native_provider_attempts for row in censuses),
            'charging_solve_step_subcalls': sum(row.backend_solve_calls for row in censuses),
            'charging_subcall_scope': censuses[0].backend_solve_scope,
            'charging_solve_counts_include_initial_state_algebraic_solvers': False,
            'initial_soc_soh_solve_calls': sum(row.initializer_solver_attempts for row in censuses),
            'initializer_scope': 'INITIAL_SOC_SOH_SOLVE_CALLS',
            'internal_consistent_initialization': 'WITHIN_EACH_MAIN_SUBSOLVE_EXPENSE_NOT_SEPARATELY_OBSERVED',
            'native_tier_transitions': sum(len(trace.transitions) for row in censuses for trace in row.traces),
            'initializer_cpu_wall_are_subwindows_of_trace_expense': True,
            'initializer_subwindows_are_additive_with_trace_expense': False,
            'charging_subwindows_are_additive_with_trace_expense': False,
            'recovery_contacts': 0,
        }
        # The saved domain outcome decides whether another native operation is
        # useful. Adverse/unevaluable observations remain actual STOP evidence.
        continue_science = following_name is not None and current.disposition is AssessmentDisposition.SATISFIED
        parent = successor = None
        if continue_science:
            _, retained_draft, _, _ = load_authored_wave(directory=directory, artifact_writer=programme.plane)
            parent = drafts.describe_contributions(retained_draft, products)[0]
            successor = programme.measured(following_name + '.preview', lambda: preview_inquiry_successor(
                supplier_directory=directory, artifact_writer=programme.plane))
            if successor is None:
                raise ValueError('admitted battery outcome lacks its exact registered subsequent inquiry')
        decision = programme.decision(directory.name, directory, result, endpoint=current.scope,
            question=QUESTION, next_draft=successor, next_manifest=parent, previous=previous_decision)
        if not continue_science:
            programme.report['battery_terminal'] = {'phase': phase, 'disposition': current.disposition.value,
                'action': 'STOP', 'remaining_selected_phases': (() if following_name is None else
                    ('use', 'reuse') if phase == 'supply' else ('reuse',)),
                'remaining_phases_status': 'NONATTEMPT'}
            return tuple(recipients)
        contribution, authenticated = programme.contribution(directory.name + '-contribution', directory)
        if authenticated != parent:
            raise ValueError('battery portable parent changed the committed actual inquiry intent')
        instance = (science.compatible_instance(supplier, 'use') if phase == 'supply' else
                    science.compatible_instance(supplier, 'reuse', prior_use=current.assessment))
        supplier_directory = directory
        directory, products, result = programme.wave(following_name, successor, (instance,), parent=parent,
            contribution=contribution, decision=decision, supplier_directory=supplier_directory)
        current = unique_product(products, BatteryInquiryAssessedInstance)
        if current.supplier != supplier or phase == 'use' and current.prior_use != recipients[-1].assessment:
            raise ValueError('battery recipient changed original supply or actual prior-use lineage')
        recipients.append(current)
        previous_decision = decision
    raise AssertionError('battery inquiry failed to retain its final STOP')


def _battery_source_intake(programme, *, manufacturer_source_path=None):
    """Retain original/native/protocol bytes using metadata, without native import."""
    from importlib.metadata import distribution
    from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import (
        BatteryInquirySource, PROTOCOL_SHA256, SOURCE_MEMBERS, SOURCE_VERSION,
    )
    source = BatteryInquirySource()
    target = programme.root / 'battery-source-originals'
    target.mkdir()
    register = []

    def retain(path, name, digest, size=None):
        if path.is_symlink() or not path.is_file():
            raise ValueError('selected battery source is missing or a link: ' + str(path))
        raw = path.read_bytes()
        if sha256(raw).hexdigest() != digest or size is not None and len(raw) != size:
            raise ValueError('selected battery original source differs before native entry: ' + name)
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as stream:
            stream.write(raw)
        if destination.read_bytes() != raw:
            raise ValueError('retained battery original source differs: ' + name)
        register.append({'path': name, 'bytes': len(raw), 'sha256': digest, 'original_path': str(path)})

    retain(programme.project / 'programmes/energy/battery-charging/records/battery-thermal-inquiry-selection.json',
           'battery-thermal-inquiry-selection.json', PROTOCOL_SHA256)
    manufacturer = (Path('/tmp/empirical-lawhood-applied-el-20261011-reopen01/battery-thermal-source-audit/m50-original.pdf')
                    if manufacturer_source_path is None else Path(manufacturer_source_path))
    retain(manufacturer,
           'm50-original.pdf', source.manufacturer_document_sha256, 576273)
    installed = distribution('pybamm')
    if installed.version != SOURCE_VERSION:
        raise ValueError('selected battery installed distribution version differs before native import')
    installed_root = Path(installed.locate_file('pybamm')).resolve(strict=True)
    for name, digest in SOURCE_MEMBERS:
        retain(installed_root / name, 'pybamm/' + name, digest)
    programme.report['battery_source_intake'] = {
        'source': source.to_document(), 'source_sha256': source.fingerprint(),
        'members': register, 'installed_native_source_members': len(SOURCE_MEMBERS),
        'manufacturer_original_url': 'https://www.lithiumelements.com/wp-content/uploads/2023/07/m50.pdf',
        'manufacturer_current_oem_approval': False, 'native_imports_or_contacts': 0,
    }
    write_json(target / 'source-intake-register.json', programme.report['battery_source_intake'])
    return source


if __name__ == '__main__':
    main()
