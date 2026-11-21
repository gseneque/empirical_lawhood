# SPDX-License-Identifier: MPL-2.0
"""Exact finite weighted-ensemble resampling, without a dynamical time step.

Each occupied bin is sampled independently within one original run. A chosen
child inherits its parent's entire path and phase. Other parent histories and
every random word remain in the evidence, including zero-offspring parents.
"""

from dataclasses import dataclass, replace
from fractions import Fraction
from hashlib import sha256
from math import gcd, lcm
from typing import ClassVar

from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_records import PathWeight, WeightedPathState, WeightedResamplingSelection, roster


@dataclass(frozen=True, slots=True)
class ResampledPath(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/resampled-path'
    VERSION: ClassVar[str] = '1.0.0'
    parent_path_id: str
    path: WeightedPathState
    random_words: tuple[int, ...]
    accepted_integer: int
    selection_denominator: int

    def __post_init__(self):
        validate_stable_id(self.parent_path_id)
        exact(self.path, WeightedPathState)
        if (type(self.random_words) is not tuple or not self.random_words
                or any(type(n) is not int or not 0 <= n < 2**64 for n in self.random_words)
                or type(self.accepted_integer) is not int or type(self.selection_denominator) is not int
                or not 0 <= self.accepted_integer < self.selection_denominator):
            raise ValueError('resampling evidence needs every exact draw and its finite categorical extent')


@dataclass(frozen=True, slots=True)
class WeightedResamplingEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/weighted-resampling-evidence'
    VERSION: ClassVar[str] = '1.0.0'
    evidence_id: str
    selection: WeightedResamplingSelection
    original_paths: tuple[WeightedPathState, ...]
    offspring: tuple[ResampledPath, ...]
    retained_terminal_paths: tuple[WeightedPathState, ...]
    scope: str = 'PATH_RESAMPLING_WITHOUT_NEW_DYNAMICS_OR_INDEPENDENT_UNITS'

    def __post_init__(self):
        validate_stable_id(self.evidence_id)
        exact(self.selection, WeightedResamplingSelection)
        roster(self.original_paths, WeightedPathState, 'path_id')
        roster(self.retained_terminal_paths, WeightedPathState, 'path_id', allow_empty=True)
        if type(self.offspring) is not tuple or any(type(row) is not ResampledPath for row in self.offspring):
            raise ValueError('resampling evidence requires its complete ordered offspring census')
        if self.scope != 'PATH_RESAMPLING_WITHOUT_NEW_DYNAMICS_OR_INDEPENDENT_UNITS':
            raise ValueError('resampling cannot create a physical clock or independent experiment')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.evidence_id, self)

    @property
    def resulting_paths(self):
        return tuple(sorted((*self.retained_terminal_paths, *(row.path for row in self.offspring)), key=lambda p:p.path_id))


def _draw_integer(generator, denominator):
    """Rejection sampling avoids binary64 rounding or modulo selection bias."""
    bits = denominator.bit_length()
    words, per_draw = [], (bits+63)//64
    while True:
        number = 0
        for _ in range(per_draw):
            word = int(generator.random_raw())
            words.append(word)
            number = (number << 64) | word
        number &= (1 << bits)-1
        if number < denominator:
            return number, tuple(words)


def resample_weighted_paths(*, selection, paths):
    """Retain all originals and exact probability while resampling active paths.

    A deterministic NVE clone has the same future until its physical dynamics
    differs. This method does not randomize its velocity, add a bath, promise
    independent trajectories or supply acceleration from identical clones.
    """
    import numpy as np
    exact(selection, WeightedResamplingSelection)
    roster(paths, WeightedPathState, 'path_id')
    if any(p.bin_id not in selection.bin_ids for p in paths):
        raise ValueError('weighted resampling omits a selected original bin')
    groups = sorted({(p.ensemble_id, p.run_id) for p in paths})
    for key in groups:
        group = tuple(p for p in paths if (p.ensemble_id, p.run_id) == key)
        if sum((p.weight.fraction for p in group), Fraction()) != 1:
            raise ValueError('weighted resampling loses the complete unit-probability run census')
        active_steps = {p.physical_step for p in group if p.disposition == 'ACTIVE'}
        if len(active_steps) > 1:
            raise ValueError('weighted resampling cannot combine paths at different physical times')
    if any(max(p.weight.numerator.bit_length(), p.weight.denominator.bit_length()) > selection.maximum_integer_bits for p in paths):
        raise ValueError('complete exact weights exceed the selected integer allocation')
    digest = sha256(selection.canonical_bytes()+b''.join(p.canonical_bytes() for p in paths)).hexdigest()
    generator = np.random.PCG64DXSM(selection.seed)
    offspring = []
    for ensemble, run in groups:
        for bin_id, count in zip(selection.bin_ids, selection.offspring_per_occupied_bin, strict=True):
            parents = tuple(p for p in paths if (p.ensemble_id, p.run_id, p.bin_id, p.disposition) == (ensemble, run, bin_id, 'ACTIVE'))
            if not parents:
                continue
            common = 1
            for parent in parents:
                common = lcm(common, parent.weight.denominator)
                if common.bit_length() > selection.maximum_integer_bits:
                    raise ValueError('complete weight denominator exceeds the selected integer allocation')
            integers = tuple(p.weight.numerator*(common//p.weight.denominator) for p in parents)
            divisor = gcd(*integers)
            integers = tuple(v//divisor for v in integers)
            denominator = sum(integers)
            if denominator.bit_length() > selection.maximum_integer_bits:
                raise ValueError('categorical probability exceeds the selected integer allocation')
            weight = PathWeight.from_fraction(sum((p.weight.fraction for p in parents), Fraction())/count)
            if max(weight.numerator.bit_length(), weight.denominator.bit_length()) > selection.maximum_integer_bits:
                raise ValueError('offspring weight exceeds the selected exact integer allocation')
            for _ in range(count):
                selected, words = _draw_integer(generator, denominator)
                cumulative = 0
                for parent, integer in zip(parents, integers, strict=True):
                    cumulative += integer
                    if selected < cumulative:
                        break
                child = replace(parent, path_id='path.weighted.'+digest+'.'+str(len(offspring)), weight=weight)
                offspring.append(ResampledPath(parent.path_id, child, words, selected, denominator))
    result = WeightedResamplingEvidence('evidence.weighted-resampling.'+digest, selection, paths, tuple(offspring),
        tuple(p for p in paths if p.disposition != 'ACTIVE'))
    for ensemble, run in groups:
        if sum((p.weight.fraction for p in result.resulting_paths if (p.ensemble_id, p.run_id) == (ensemble, run)), Fraction()) != 1:
            raise AssertionError('exact weighted resampling failed probability conservation')
    return result


def assess_weighted_resampling(evidence):
    """Check exact categorical decisions, ancestry, clocks and all random words."""
    exact(evidence, WeightedResamplingEvidence)
    import numpy as np
    generator = np.random.PCG64DXSM(evidence.selection.seed)
    seen = set()
    if evidence.retained_terminal_paths != tuple(p for p in evidence.original_paths if p.disposition != 'ACTIVE'):
        raise ValueError('resampling dropped or changed a terminal path')
    parents = {p.path_id:p for p in evidence.original_paths}
    for row in evidence.offspring:
        parent = parents.get(row.parent_path_id)
        if parent is None or parent.disposition != 'ACTIVE' or row.path.path_id in seen:
            raise ValueError('resampling changes original ancestry or repeats an offspring')
        seen.add(row.path.path_id)
        group = tuple(p for p in evidence.original_paths if (p.ensemble_id,p.run_id,p.bin_id,p.disposition) ==
            (parent.ensemble_id,parent.run_id,parent.bin_id,'ACTIVE'))
        total = sum((p.weight.fraction for p in group), Fraction())
        count = evidence.selection.offspring_per_occupied_bin[evidence.selection.bin_ids.index(parent.bin_id)]
        if replace(row.path, path_id=parent.path_id, weight=parent.weight) != parent or row.path.weight.fraction != total/count:
            raise ValueError('resampling changes a phase, history, physical clock or compensating probability')
        for word in row.random_words:
            if int(generator.random_raw()) != word:
                raise ValueError('resampling substitutes the original random-word sequence')
        bits, width = row.selection_denominator.bit_length(), (row.selection_denominator.bit_length()+63)//64
        if len(row.random_words) % width:
            raise ValueError('resampling truncates a categorical draw')
        draws = []
        for start in range(0, len(row.random_words), width):
            value = 0
            for word in row.random_words[start:start+width]:
                value = value*(2**64)+word
            draws.append(value % (2**bits))
        if (any(v < row.selection_denominator for v in draws[:-1]) or draws[-1] != row.accepted_integer):
            raise ValueError('resampling discards an accepted draw or changes the chosen integer')
        position = Fraction(row.accepted_integer, row.selection_denominator)
        low = Fraction()
        for candidate in group:
            high = low+candidate.weight.fraction/total
            if low <= position < high:
                if candidate.path_id != parent.path_id:
                    raise ValueError('resampling changes the weight-proportional chosen parent')
                break
            low = high
    expected = resample_weighted_paths(selection=evidence.selection, paths=evidence.original_paths)
    if expected != evidence:
        raise ValueError('resampling changes the complete original bin, offspring or draw census')
    return dict(original_paths=len(evidence.original_paths), offspring=len(evidence.offspring),
        terminal_paths=len(evidence.retained_terminal_paths), probability_conservation='EXACT',
        physical_steps_added=0, independent_units_added=0, verification='RANDOM_WORDS_CATEGORICAL_INTERVALS_AND_COMPLETE_GENEALOGY')
