# SPDX-License-Identifier: MPL-2.0
"""Supported complete physical network joins and independent closed export."""

from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_network_records import PhysicalSupplierSelection, PhysicalSupplierEvidence
from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_network_read import validate_physical_supplier_inputs, read_physical_suppliers
from empirical_lawhood.api.domain_composition.rubisco_response.native_analysis_export import MEMBERS, export_native_observation_analysis, read_native_observation_analysis


def _text(report):
    lines = ['Conditional physical supplier assessment', '',
        'All original paths, failed rates, competing exits and costs remain in the source analysis.',
        'Processing retains chemistry, product release and substrate-ready return in its complete exit time.',
        'Moment quotients require state-reduction assessment. An elementary chemical rate is not a complete processing rate.',
        'Encounter elimination retains escape and the complete residence time at every selected concentration.',
        'Every whole-run resample retains the same joint rate draw and complete network.', '']
    for key,row in report['networks'].items():
        lines.append(key+': '+row['conditional_memoryless_reduction'])
    for key,row in report['encounter_reductions'].items():
        lines.append(key+': '+row['status'])
    lines.extend(('', 'These conditional calculations establish no physical-model or biological admission.', ''))
    return '\n'.join(lines).encode('utf-8')


def export_physical_suppliers(*, selection, sources, project_root, artifact_writer, output_relative_path):
    return export_native_observation_analysis(namespace='physical-supplier',selection=selection,sources=sources,
        project_root=project_root,artifact_writer=artifact_writer,output_relative_path=output_relative_path,
        validate=validate_physical_supplier_inputs,read=read_physical_suppliers,evidence_kind=PhysicalSupplierEvidence,render=_text)


def read_physical_supplier_export(*, directory_relative_path, sources, artifact_writer):
    return read_native_observation_analysis(validate=validate_physical_supplier_inputs, directory_relative_path=directory_relative_path,sources=sources,
        artifact_writer=artifact_writer,selection_kind=PhysicalSupplierSelection,evidence_kind=PhysicalSupplierEvidence,
        read=read_physical_suppliers,render=_text)


__all__ = ('MEMBERS','validate_physical_supplier_inputs','read_physical_suppliers','export_physical_suppliers','read_physical_supplier_export')
