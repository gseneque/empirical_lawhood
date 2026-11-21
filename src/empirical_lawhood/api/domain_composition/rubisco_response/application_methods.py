# SPDX-License-Identifier: MPL-2.0
"""Declared method explanations; references cannot select executable modules."""

from copy import deepcopy


_METHODS = "domains/rubisco/rubisco_response/"
_API = "api/domain_composition/rubisco_response/"
_GUIDE = "programmes/biology/photosynthesis/workflows/rubisco-response/"


def _method(key, title, lead, steps, sources, guides, *, formula=None):
    return {"id": "rubisco." + key, "title": title, "lead": lead,
        "steps": [{"title": title, "body": body} for title, body in steps],
        "sources": [{"path": path, "symbols": list(symbols)} for path, symbols in sources],
        "guides": [_GUIDE + name for name in guides], "formula": formula,
        "status": "DECLARED_METHOD_NOT_EVIDENCE_OF_PHYSICAL_SUPPLY",
        "runtime": {"original_native_versions": None,
            "meaning": "Original native versions require their own authenticated observation. The installed reader is a separate source."}}


_CATALOGUE = (
    _method("root", "Joint receiver and evidence admission",
        "The receiver is the joint turnover and specificity decision. It determines the required physical evidence.", (
            ("Bind the question", "Keep the paired materials, assay, chemical alternatives, strict turnover threshold and inclusive specificity threshold."),
            ("Check evidence connections", "Source, contrast and joint-support reviews retain their exact scope. A construction is not a physical admission."),
            ("Reconstruct before aggregation", "The independent assessor checks each conjunction, then applies the original alternative and processing policies.")),
        ((_METHODS + "initial_root.py", ("calculate_initial_root", "assess_initial_root")),
         (_METHODS + "initial_root_requirements.py", ("initial_root_requirement_graph", "project_initial_root_connection"))),
        ("initial-root-v1.md", "initial-model-v1.md"), formula="T = 1 / (w/qₐ + (1−w)/qᵣ) > 1; S = qᴅ × qχ ≥ 1"),
    _method("receiver", "Define the receiving calculation",
        "Preparation is assessed against the next receiving calculation and its physical scope.", (
            ("Select the quantity", "Bind the signed quantity, physical clock or measure, accuracy allowance and information cutoff."),
            ("Declare preparation freedoms", "State which coordinates, state, history, constraints and chemical alternatives may vary."),
            ("Assess at the destination", "A numerical admission does not supply molecular admission.")),
        ((_METHODS + "initial_root_requirements.py", ("initial_root_scope",)),
         (_METHODS + "paired_receiver_bound.py", ("bound_paired_receiver", "assess_paired_receiver_bound"))),
        ("initial-root-v1.md", "restrained-formation-v1.md")),
    _method("preparation", "From construction to an admissible state",
        "Establish the actual paired state required by the receiver, with its original topology, chemistry and complete coordinates.", (
            ("Authenticate the pair", "Keep selected seeds, atom census, cell, topology and returned endpoint arrays with the complete trace."),
            ("Test each endpoint", "Check finite arrays, starting state, force convergence, energy and step history, SCF returns, stereochemistry, proton allocation and clashes."),
            ("Assess the matched pair", "A stationary endpoint supplies neither equilibrium populations nor a physical rate.")),
        ((_API + "active_relaxation.py", ("assess_matched_active_relaxation",)),
         (_API + "construction_operations.py", ("run_construction_operation",)),
         (_API + "molprobity_validation.py", ("validate_structure",)),
         (_API + "kcx_backbone_read.py", ("assess_files",)),
         (_API + "forecast_returns.py", ("read_forecast_returns",)),
         (_METHODS + "active_relaxation_assessment.py", ("assess_active_endpoint", "assess_endpoint_trace", "endpoint_geometry")),
         (_METHODS + "periodic_probe_native.py", ())), ("initial-root-v1.md", "restrained-formation-v1.md")),
    _method("closure", "Chemical and kinetic applicability",
        "The paired physical assay needs an applicable chemical model and kinetic closure.", (
            ("Preserve chemical alternatives", "Retain proton allocation, Mg and water state, oxygen spin and electron-transfer assumptions."),
            ("Justify reduced kinetics", "Keep consequential reversals, productive exits and return waits."),
            ("Preserve missing alternatives", "Unsupported alternatives remain visible under the original aggregation policy.")),
        ((_METHODS + "initial_model.py", ("read_initial_model",)),
         (_METHODS + "physical_rate_network_science.py", ("assess_network_dynamics",))),
        ("initial-model-v1.md", "activation-rate-connection.md")),
    _method("formation", "Formation receiver and rate connection",
        "The formation path follows transferred H3 between substrate C3 and the accepting KCX oxygen in matched full assemblies.", (
            ("Define the physical coordinate", "Retain atom roles, natural masses, periodic images, shared hydrogen and atomic correspondence."),
            ("Assess the integral or bound", "The restrained estimate retains paired block uncertainty. A bound needs actual stiffness, centres, domain and remainder premises."),
            ("Admit the rate connection", "Supply finite-restraint, measure, state, prefactor and transmission corrections. The restrained integral alone is not qₐ.")),
        ((_METHODS + "formation_coordinate.py", ("prepare_formation_coordinate",)),
         (_METHODS + "restrained_formation.py", ("read_restrained_formation",)),
         (_METHODS + "paired_receiver_bound.py", ("bound_paired_receiver", "assess_paired_receiver_bound"))),
        ("restrained-formation-v1.md", "activation-rate-connection.md"),
        formula="ξ = d(C3,H3) − d(H3,O_KCX); ∂Aₖ(s)/∂s = k(s − ⟨ξ⟩ₛ)"),
    _method("processing", "Productive carbon processing",
        "Keep the probability of productive completion and the time in the consequential cycle.", (
            ("Retain exits and return waits", "Include failures and regeneration with the original source-bound rate-network records."),
            ("Share carbon commitment", "Processing and commitment can use the same carbon evidence. They remain dependent."),
            ("Join supported relative operands", "Actual ratios or sufficient bounds require physical applicability and joint support.")),
        ((_METHODS + "initial_contributions.py", ("read_initial_contributions",)),
         (_METHODS + "physical_rate_network_science.py", ("assess_network_dynamics",))),
        ("initial-model-v1.md",), formula="qᵣ = q(P_C) / q(τ_C)"),
    _method("oxygen", "Carbon versus oxygen addition",
        "Start from the same reactive-state ensemble and retain the mutation's oxygen contribution.", (
            ("Bind chemical alternatives", "Keep gas access, partition, atom roles, charge, spin and electronic-state assumptions."),
            ("Assess electronic and dynamical evidence", "Retain state, trajectory, failures and uncertainty at their original scope."),
            ("Supply paired discrimination", "A foreign absolute barrier or assumed oxygen ratio of one supplies no mutant contrast.")),
        ((_METHODS + "electronic_ensemble_science.py", ()), (_METHODS + "reactive_flux_science.py", ("assess_flux_controls",)),
         (_API + "tagged_products.py", ("read_oxygen_bound_products", "assess_tagged_flux_panel")),
         (_API + "crossing_orbitals.py", ("read_crossing_orbitals",)),
         (_API + "crossed_fields.py", ("read_crossed_fields",)),
         (_API + "interface_forecast.py", ("measure_interface_transfer",)),
         (_METHODS + "initial_contributions.py", ("read_initial_contributions",))),
        ("initial-model-v1.md",), formula="qᴅ = (cM / oM) / (cW / oW)"),
    _method("commitment", "Productive versus returning branches",
        "Specificity depends on productive completion after carbon or oxygen addition.", (
            ("Keep competing exits", "Retain product probabilities, residence times and consequential reverse paths."),
            ("Keep shared evidence", "Reuse of the same carbon observation does not create another independent measurement."),
            ("Assess the paired quotient", "Preserve oxygen commitment and joint uncertainty. Missing operands have no neutral default.")),
        ((_METHODS + "initial_contributions.py", ("read_initial_contributions",)),
         (_METHODS + "physical_rate_network_science.py", ("assess_network_dynamics",))),
        ("initial-model-v1.md",), formula="qχ = q(P_C) / q(P_O)"),
    _method("support", "Simultaneous evidence and dependence",
        "The decision needs support for joint mutation contrasts at their original physical and uncertainty scope.", (
            ("Bind the review", "Keep the same materials, assay, chemical alternative and source evidence."),
            ("Preserve dependence", "Shared evidence is not independently resampled. Samples are not universal enclosures."),
            ("Assess before aggregation", "An admitted adverse endpoint can contradict the conjunction. Missing realizations remain empty.")),
        ((_METHODS + "initial_model.py", ("read_initial_model",)), (_METHODS + "initial_root.py", ("assess_initial_root",))),
        ("initial-root-v1.md", "initial-model-v1.md")),
    _method("force", "Full force actions and receiver fidelity",
        "A molecular action must match the physical direction and the quantity consumed by the receiving calculation.", (
            ("Retain the coupled operator", "Keep periodic electrostatics, topology, image handling, link-atom pullback and units."),
            ("Assess the actual action", "Energy, gradient and displacement checks establish numerical behavior at the selected geometry."),
            ("Admit the receiver interface", "A force control alone establishes neither an ensemble nor a mutant rate or receiver error bound.")),
        ((_METHODS + "periodic_probe_native.py", ()),
         (_METHODS + "periodic_mm_remainder.py", ("periodic_mm_remainder", "pullback_qm_gradient"))),
        ("initial-root-v1.md", "restrained-formation-v1.md")),
    _method("retained", "Original molecular construction and controls",
        "Retained constructions and numerical controls preserve their original scope without launching a successor.", (
            ("Keep constructed alternatives", "Material preparations, site partitions and starting hypotheses are not independent biological replicates."),
            ("Keep control scope", "A baseline and displaced points at one WT geometry supply no paired mutant rate or relaxed ensemble."),
            ("Carry limitations forward", "Physical preparation, chemical applicability and contrast gaps remain with the original receiver.")),
        ((_METHODS + "initial_model.py", ("read_initial_model",)),
         (_METHODS + "initial_root_requirements.py", ("initial_root_requirement_graph",))),
        ("initial-root-v1.md", "initial-model-v1.md")),
)


def method_descriptions():
    return deepcopy(list(_CATALOGUE))


def preparation_response_methods():
    """Explain the registered local reader without asserting acquired evidence."""
    return [_method("preparation-response", "Local preparation and finite response",
        "Read the frozen paired design, retained safe states and six independently assessed questions at their original local scope.", (
            ("Preserve preparation history", "Initial and later WT/I95M positions are nested within one construction. A continued prefix retains original returns and consumes only its remaining allowance; unknown contact refuses continuation."),
            ("Separate acquisition from assessment", "Complete diagnostic returns supply local directional comparisons. Withheld finite responses and any optional refinement require their recorded inquiry decisions."),
            ("Retain all six questions", "Keep signed quantities, missing and adverse outcomes, empirical two-scale sensitivity and the complete denominators. These findings supply no biological replication or kinetic admission."),
            ("Assess use at the destination", "Contribution authentication, supply assessment and destination admission remain separate from preparation, return publication and display.")),
        ((_API + "active_preparation.py", ("prepare_prefix_continuation",)),
         (_API + "preparation_response_analysis.py", ("read_preparation_stage", "read_response_stage", "read_response_analysis")),
         (_METHODS + "preparation_response_assessment.py", ("assess_response_operands",)),
         (_METHODS + "preparation_supply_policy.py", ("supply_owners",))),
        ("preparation-response-v1.md",))]


def method_for_requirement(requirement, graph):
    """Editorial names over already decoded requirements; never create graph edges."""
    key = requirement.requirement_id
    if key == graph.root_requirement_id:
        return "rubisco.root", "Paired endpoint question"
    if key == graph.numerical_requirement_id:
        return "rubisco.root", "Numerical reconstruction"
    suffixes = (
        ("actual-paired-physical-preparation", "preparation", "Paired physical preparation"),
        ("chemical-model-and-closure-applicability", "closure", "Chemical and kinetic applicability"),
        ("contrast.a", "formation", "Formation · qₐ"),
        ("contrast.r_c", "processing", "Processing · qᵣ"),
        ("contrast.c_over_o", "oxygen", "Gas discrimination · qᴅ"),
        ("contrast.chi_c_over_chi_o", "commitment", "Branch commitment · qχ"),
        ("joint-mutation-contrasts", "support", "Simultaneous joint support"),
        ("retained-inputs", "retained", "Retained inputs"),
        ("relative-operand-supply", "root", "Relative operands"),
        ("paired-integral-bound", "formation", "Paired integral bound"),
        ("retained-response-actions", "force", "Retained force actions"),
        ("physical-preparation", "preparation", "Physical preparation"),
        ("receiver-definition", "receiver", "Receiving calculation"),
        ("compatible-states", "preparation", "Compatible states"),
        ("direction-action-interface", "force", "Physical direction interface"),
        ("durable-preparation-state", "preparation", "Durable safe state"),
        ("activation-connection", "formation", "Activation connection"),
        ("restraint-and-domain", "formation", "Restraint and domain"),
        ("physical-applicability", "closure", "Physical applicability"),
        ("joint-support", "support", "Joint support"),
    )
    for suffix, method, label in suffixes:
        if key.endswith(suffix):
            return "rubisco." + method, label
    return "rubisco.root", requirement.condition
