# SPDX-License-Identifier: MPL-2.0
"""Operation-local E4 reveal selection, separate from original data identity.

This value conveys no authority. Every actual access reloads the selected
grant from the ordinary store; original scientific locators stay unchanged.
"""
from dataclasses import dataclass, replace
from types import SimpleNamespace

from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_records import SelectedE4WaveLocator, pin


@dataclass(frozen=True, slots=True)
class SelectedE4CurrentAccess:
    waves: tuple[SelectedE4WaveLocator, ...]

    def __post_init__(self):
        if (type(self.waves) is not tuple or not self.waves
                or any(type(value) is not SelectedE4WaveLocator for value in self.waves)
                or tuple(value.wave_id for value in self.waves)!=tuple(sorted({value.wave_id for value in self.waves}))
                or len({value.run_id for value in self.waves})!=len(self.waves)):
            raise ValueError('current E4 access requires one explicit current locator per original wave and run')
        for value in self.waves:
            value.__post_init__()

    def authority_binding(self, original):
        if type(original) is not SelectedE4WaveLocator:
            raise TypeError('current E4 access requires its exact original data locator')
        original.__post_init__()
        selected=tuple(value for value in self.waves if value.wave_id==original.wave_id)
        if len(selected)!=1 or replace(selected[0],reveal_authority=original.reveal_authority)!=original:
            raise PermissionError('current E4 access changes its original wave, run, package, issue, execution or plan')
        return SimpleNamespace(issued_study=original.issued_study,execution_authority=original.execution_authority,
            reveal_authority=selected[0].reveal_authority)

    def require_originals(self, originals):
        if (type(originals) is not tuple or tuple(value.wave_id for value in originals)!=
                tuple(value.wave_id for value in self.waves)):
            raise PermissionError('current E4 access changes its complete original wave roster')
        for original in originals:
            self.authority_binding(original)


def select_current_e4_access(records):
    """Project copied current locators without creating or checking authority."""
    if (type(records) is not tuple or not records
            or any(type(record) is not SelectedE4WaveLocator for record in records)):
        raise TypeError('current E4 access requires its exact canonical wave locators')
    return SelectedE4CurrentAccess(tuple(sorted(records, key=lambda record: record.wave_id)))


def selected_e4_authority_binding(original, current_access=None):
    if current_access is None:
        return original
    if type(current_access) is not SelectedE4CurrentAccess:
        raise TypeError('current E4 access requires its exact operation-local selection')
    return current_access.authority_binding(original)


def require_current_e4_access(*, writer, originals, current_access=None):
    """Fresh store/clock check after original custody and final physical guards."""
    from empirical_lawhood.api.recursive_qualified_parents import _actual_package, _require_parent_authorities_current
    if (type(originals) is not tuple or any(type(value) is not SelectedE4WaveLocator for value in originals)
            or tuple(value.wave_id for value in originals)!=tuple(sorted({value.wave_id for value in originals}))):
        raise TypeError('current E4 access requires the exact original wave locator census')
    if current_access is not None:
        if type(current_access) is not SelectedE4CurrentAccess:
            raise TypeError('current E4 access requires its exact operation-local selection')
        current_access.require_originals(originals)
    entries=[]
    for original in originals:
        package=_actual_package(writer,original.run_id)
        if pin(package,'package_id')!=original.package:
            raise PermissionError('current E4 access substitutes its actual original package')
        entries.append((selected_e4_authority_binding(original,current_access),package))
    _require_parent_authorities_current(tuple(entries),writer)
