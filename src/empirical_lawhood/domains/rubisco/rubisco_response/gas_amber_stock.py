# SPDX-License-Identifier: MPL-2.0
"""Scoped copies of the original Gp source's gas parameter stock.

Original numerical and charge tokens survive. Gas-specific type names prevent
these files from overriding existing protein, substrate or solvent parameters.
This is a source transformation, without force-field or kinetic admission.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from hashlib import sha256
import re
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import SourceMember
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.preparation import _prepi_rows, _frcmod_sections
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


_BASE = 'https://raw.githubusercontent.com/kacarlab/RuBisCO_evolution/e6c621656ca1a8eb7e09381d6405da5d412274a1/data/systems_for_MD/parameters/'
PINS = {
    'CO2': ('32f61cd3d23deb7f6b45b05da967450bd36e33d9826ccdff68e902d2134deaa6',
        '0ce20d91d82fa84ca85fca927ac2bcfbba1a229347bea40901c91d20f3a297df'),
    'O2': ('81d8989f9db3112287b45ff9dcf982c3bbeda7006b6de8e8fc5fc5929c458301',
        'dd606cce82c17d14ca3a1c0b8e475fa1692bc485fd9591f368e34da2ff692153'),
}
ALIASES = {'CO2': (('c1','G1'),('o','G2')), 'O2': (('o','G0'),)}
_WIDTHS = {'MASS':1, 'BOND':2, 'ANGLE':3, 'DIHE':4, 'IMPROPER':4, 'NONBON':1}
_SCOPE = 'EXACT_SOURCE_GAS_PARAMETER_ALIASING_NOT_BULK_OR_REACTIVE_MODEL_ADMISSION'


def _scope_text(prepi, frcmod, aliases):
    """Reuse the existing Amber token readers; replace type tokens only."""
    mapping = dict(aliases)
    replacements = {}
    used = set()
    for line,tokens in _prepi_rows(prepi):
        typ = tokens[2].group()
        if typ == 'DU':
            continue
        if typ not in mapping:
            raise ValueError('gas template contains an unselected atom type')
        used.add(typ)
        token = tokens[2]
        replacements[line] = line[:token.start()]+mapping[typ]+line[token.end():]
    if used != set(mapping):
        raise ValueError('gas template omits a selected atom type')
    scoped_prepi = ''.join(replacements.get(line,line) for line in prepi.splitlines(keepends=True))
    replacements = {}
    for section,lines in _frcmod_sections(frcmod).items():
        count = _WIDTHS[section]
        for line in lines:
            if count == 1:
                token = next(re.finditer(r'\S+',line))
                if token.group() not in mapping:
                    raise ValueError('gas parameter file contains an unselected atom type')
                replacements[line] = line[:token.start()]+mapping[token.group()]+line[token.end():]
            else:
                width = 3*count-1
                types = tuple(v.strip() for v in line[:width].split('-'))
                if len(types) != count or any(t not in mapping for t in types):
                    raise ValueError('gas parameter tuple loses a selected atom type')
                replacements[line] = '-'.join(mapping[t] for t in types)+line[width:]
    return scoped_prepi, ''.join(replacements.get(line,line) for line in frcmod.splitlines(keepends=True))


@dataclass(frozen=True, slots=True)
class GasAmberStock(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/gas-amber-stock'
    gas: str
    original_prepi: SourceMember
    original_frcmod: SourceMember
    aliases: tuple[tuple[str,str], ...]
    scoped_prepi_utf8: str
    scoped_frcmod_utf8: str
    scope: str = _SCOPE

    def __post_init__(self):
        self._validate_sources()
        if (self.scoped_prepi_utf8,self.scoped_frcmod_utf8) != _scope_text(
                self.original_prepi.raw_utf8,self.original_frcmod.raw_utf8,self.aliases):
            raise ValueError('gas stock changes original numerical or non-type tokens')

    def _validate_sources(self):
        for value in (self.original_prepi,self.original_frcmod):
            exact(value,SourceMember)
        if (self.gas not in PINS or self.scope != _SCOPE or self.aliases != ALIASES[self.gas]
                or (self.original_prepi.sha256,self.original_frcmod.sha256) != PINS[self.gas]):
            raise ValueError('gas stock changes its exact original source or selected type scope')
        for source,suffix in ((self.original_prepi,'prepi'),(self.original_frcmod,'frcmod')):
            name = self.gas.lower()+'.'+suffix
            if (source.member_id,source.original_url) != ('source.gas-amber.'+name,_BASE+name):
                raise ValueError('gas stock changes the original source identity or revision')

    @property
    def identity(self):
        return ObjectIdentity.from_record('gas-amber-stock.'+self.fingerprint(),self)


def prepare_gas_amber_stock(*, gas, original_prepi_bytes, original_frcmod_bytes, existing_atom_types):
    """Prepare only the source-selected types; retain all original bytes."""
    if gas not in PINS or type(existing_atom_types) not in (tuple,frozenset):
        raise ValueError('select a supported gas and the immutable existing type census')
    if any(type(t) is not str or not t for t in existing_atom_types):
        raise ValueError('existing gas-host atom types must be explicit nonempty names')
    if {v for _,v in ALIASES[gas]} & set(existing_atom_types):
        raise ValueError('gas alias collides with an existing host atom type')
    sources = []
    for raw,suffix,digest in zip((original_prepi_bytes,original_frcmod_bytes),('prepi','frcmod'),PINS[gas],strict=True):
        if type(raw) is not bytes or len(raw) > 4096 or sha256(raw).hexdigest() != digest:
            raise ValueError('gas parameter preparation requires its exact original source bytes')
        name = gas.lower()+'.'+suffix
        sources.append(SourceMember('source.gas-amber.'+name,_BASE+name,digest,raw.decode('ascii')))
    prepi,frcmod = _scope_text(sources[0].raw_utf8,sources[1].raw_utf8,ALIASES[gas])
    return GasAmberStock(gas,*sources,ALIASES[gas],prepi,frcmod)


def assess_gas_amber_stock(stock, *, existing_atom_types):
    """Compare complete native tokens independently of the aliasing producer."""
    if type(stock) is not GasAmberStock:
        raise TypeError('gas assessment requires its exact source stock record')
    stock._validate_sources()
    reverse = {new:old for old,new in stock.aliases}
    if set(reverse) & set(existing_atom_types):
        raise ValueError('gas alias collides with an existing host atom type')
    original = [[t.group() for t in tokens] for _,tokens in _prepi_rows(stock.original_prepi.raw_utf8)]
    derived = [[t.group() for t in tokens] for _,tokens in _prepi_rows(stock.scoped_prepi_utf8)]
    for row in derived:
        if row[2] != 'DU':
            row[2] = reverse.get(row[2])
    if original != derived:
        raise ValueError('gas aliasing changes a complete source atom or charge token')
    original_sections = _frcmod_sections(stock.original_frcmod.raw_utf8)
    derived_sections = _frcmod_sections(stock.scoped_frcmod_utf8)
    for section,lines in original_sections.items():
        count = _WIDTHS[section]
        def rows(values, transform):
            result = []
            for line in values:
                if count == 1:
                    typ,*rest = line.split()
                    result.append(((transform.get(typ,typ),),tuple(rest)))
                else:
                    types = tuple(t.strip() for t in line[:3*count-1].split('-'))
                    result.append((tuple(transform.get(t,t) for t in types),tuple(line[3*count-1:].split())))
            return result
        if rows(lines,{}) != rows(derived_sections[section],reverse):
            raise ValueError('gas aliasing changes a complete native parameter token')
    charge_tokens = tuple((row[1],row[10]) for row in original if row[2] != 'DU')
    with localcontext() as context:
        context.prec = 60
        charge = sum((Decimal(token) for _,token in charge_tokens),Decimal(0))
    return dict(status='ORIGINAL_GAS_PARAMETER_TOKENS_PRESERVED', gas=stock.gas,
        atom_charge_tokens=charge_tokens,partial_charge_sum_e=str(charge),
        parameter_section_counts={k:len(v) for k,v in original_sections.items()},
        original_bond_parameter_rows=tuple(line.strip() for line in original_sections['BOND']),
        new_native_calls=0,physical_or_chemical_admission=False,
        requirements=('COMPLETE_GAS_AUGMENTED_TOPOLOGY_AND_NATIVE_ASSIGNMENT',
            'EXPLICIT_QM_GAS_ATOMS_AND_CLASSICAL_TERM_EXCLUSIONS',
            'GAS_ENVIRONMENT_NONBONDED_MODEL_ASSESSMENT', 'SEPARATE_BULK_ACCESS_MODEL_IF_REQUIRED'))
