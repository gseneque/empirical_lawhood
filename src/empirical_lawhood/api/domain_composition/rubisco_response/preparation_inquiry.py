# SPDX-License-Identifier: MPL-2.0
"""Project selected molecular suppliers below their authenticated original root."""

from dataclasses import dataclass
from pathlib import Path

from empirical_lawhood.api.recursive_inquiry_read import inquiry_projection_read
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import require_response_design
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_policy import rooted_preparation_campaign, rooted_preparation_menu, rooted_preparation_specification, supply_owners
from empirical_lawhood.science.inquiry.recursive_inquiry import identity
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import RobustInquirySpecification, WorkBoundInquiryState
from empirical_lawhood.science.models.time import CausalPhase, InformationCutoff
from empirical_lawhood.design.recursive_authoring import RecursiveStudyDraft
from empirical_lawhood.design.campaigns import CampaignSpec
from empirical_lawhood.design.recursive_input_origins import RecursiveInputOrigins
from empirical_lawhood.design.recursive_inquiry_policy import RobustInquiryMenu, RobustInquiryPolicy
from empirical_lawhood.execution.recursive_inquiry import InquiryStateSources, InquiryWaveSource


@dataclass(frozen=True, slots=True)
class PreparationInquiry:
    specification: RobustInquirySpecification
    state: WorkBoundInquiryState
    sources: InquiryStateSources
    menu: RobustInquiryMenu
    policy: RobustInquiryPolicy
    draft: RecursiveStudyDraft
    origins: RecursiveInputOrigins
    campaign: CampaignSpec


def project_preparation_inquiry(*, root_directory, prospective_directory, design, previous_decision_directories,
                               information_cutoff, artifact_writer, completed_supplier_directories=()):
    """Read actual custody; shared inquiry services own preview, commit and entry.

    The prospective directory is an ordinary authored, unentered supplier
    package. It provides exact current work semantics without a native call.
    An owner-directed fork retains its real predecessor contributions.
    """
    with inquiry_projection_read(artifact_writer) as reading:
        return _project_preparation_inquiry(root_directory=root_directory, prospective_directory=prospective_directory,
            design=design, previous_decision_directories=previous_decision_directories,
            information_cutoff=information_cutoff, artifact_writer=reading.writer,
            completed_supplier_directories=completed_supplier_directories, reading=reading)


def _project_preparation_inquiry(*, root_directory, prospective_directory, design, previous_decision_directories,
                               information_cutoff, artifact_writer, completed_supplier_directories, reading):
    require_response_design(design)
    exact(information_cutoff, InformationCutoff)
    if information_cutoff.phase is not CausalPhase.POST_OUTCOME:
        raise ValueError('rooted preparation inquiry requires its explicit original-outcome cutoff')
    root = Path(artifact_writer.root.contract.canonical_path)
    def relative(directory):
        path = Path(directory)
        if not path.is_absolute() or '..' in path.parts or any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError('preparation inquiry requires exact original guarded custody paths')
        return path.resolve(strict=True).relative_to(root).as_posix()
    root_path, candidate_path = relative(root_directory), relative(prospective_directory)
    original = reading.wave(directory=root_directory, include_products=True)
    root_packet, root_draft, root_products = original.packet, original.draft, original.products
    prospective = reading.wave(directory=prospective_directory, include_products=False, require_unentered=True)
    candidate, draft = prospective.packet, prospective.draft
    _, _, _, origins_for = supply_owners(draft)
    predecessors = tuple(sorted(relative(path) for path in previous_decision_directories))
    if not predecessors or len(set(predecessors)) != len(predecessors):
        raise ValueError('preparation inquiry requires distinct original predecessor decisions')
    # The shared state owner authenticates the complete predecessor history
    # within this same read before projecting any retained findings.
    waves = {root_path: InquiryWaveSource(root_path, identity(root_packet, root_packet.packet_id), True),
        candidate_path: InquiryWaveSource(candidate_path, identity(candidate, candidate.packet_id), False)}
    if root_path == candidate_path:
        raise ValueError('the selected supplier cannot replace its original completed root')
    completed = []
    for directory in completed_supplier_directories:
        path = relative(directory)
        if path in waves:
            raise ValueError('preparation inquiry repeats or disguises a completed source')
        original = reading.wave(directory=directory, include_products=True)
        packet, products, actual = original.packet, original.products, original.draft
        _, _, owner, _ = supply_owners(actual)
        owner.actual_products(actual, products)
        completed.append((actual, products))
        waves[path] = InquiryWaveSource(path, identity(packet, packet.packet_id), True)
    completed = tuple(completed)
    specification = rooted_preparation_specification(root_draft=root_draft, root_products=root_products,
        draft=draft, design=design, completed=completed)
    if information_cutoff.clock_id != specification.endpoint.clock_id:
        raise ValueError('preparation inquiry changes the original root closure clock')
    sources = InquiryStateSources(tuple(waves[path] for path in sorted(waves)), previous_decision_paths=predecessors)
    state = reading.project_state(specification=specification,
        state_id='state.rooted-preparation.' + draft.fingerprint() + '.' + information_cutoff.fingerprint()[:24],
        information_cutoff=information_cutoff, sources=sources)
    menu, policy = rooted_preparation_menu(root_draft=root_draft, root_products=root_products, draft=draft,
        design=design, specification=specification, state=state, completed=completed)
    campaign = rooted_preparation_campaign(root_draft=root_draft, draft=draft, design=design)
    return PreparationInquiry(specification, state, sources, menu, policy, draft, origins_for(draft), campaign)
