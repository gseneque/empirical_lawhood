# SPDX-License-Identifier: MPL-2.0
"""Bound optional read metadata by its retained Python graph, not external files.

This is cache admission, not a scientific limit or a process RSS allowance.
Live custody readers/guards have their own finite owner. Unknown data shapes or
an exhausted counting allowance simply keep the ordinary uncached read route.
"""

from collections import deque
from dataclasses import is_dataclass
from decimal import Decimal
from enum import Enum
from functools import partial
import gc
from itertools import chain
from pathlib import PurePath
import sys
from types import BuiltinFunctionType, CellType, FunctionType, MappingProxyType, MemberDescriptorType, MethodType, SimpleNamespace

from empirical_lawhood.science.records.serialization import CanonicalRecord, _CanonicalRope
from empirical_lawhood.science.records.decoding import _RecordValidationLifetime

MAX_METADATA_OBJECTS = 1_000_000


def _immutable_definition_capture(value, maximum_objects):
    """Generated frozen constructors capture object, never a mutable verdict."""
    pending, seen = [iter((value,))], set()
    while pending:
        try:
            current = next(pending[-1])
        except StopIteration:
            pending.pop()
            continue
        if id(current) in seen:
            continue
        if len(seen) >= maximum_objects:
            return False
        seen.add(id(current))
        if (current is None or type(current) in (bool, int, float, complex, str, bytes, Decimal)
                or isinstance(current, (type, Enum))):
            continue
        if isinstance(current, CanonicalRecord) and current._is_cacheable():
            continue
        if type(current) not in (tuple, frozenset):
            return False
        pending.append(iter(current))
    return True


def _slots(value):
    for kind in type(value).__mro__:
        for descriptor in kind.__dict__.values():
            if type(descriptor) is MemberDescriptorType:
                try:
                    yield descriptor, descriptor.__get__(value, type(value))
                except AttributeError:
                    pass


def _attributes(value):
    """Visit instance storage, including canonical caches in inherited slots."""
    namespace = getattr(value, '__dict__', None)
    if namespace is not None:
        yield namespace
    for _, item in _slots(value):
        yield item


def retained_metadata_bytes(value, *, maximum_bytes, maximum_objects=MAX_METADATA_OBJECTS,
                            owner_objects=()):
    """Count shared data once per entry; return None when safe admission fails.

Owner objects are explicitly identified live read capabilities, never data
records. Their lifetimes and final guards are retained independently of this
optional cache. Module/class/function graphs are likewise not cache-owned.
The walk is iterative and bounded in both bytes and object visits. It does not
encode records, read files, invoke properties or flatten canonical ropes.
"""
    if (type(maximum_bytes) is not int or maximum_bytes <= 0
            or type(maximum_objects) is not int or maximum_objects <= 0):
        raise ValueError('retained metadata requires positive finite counting bounds')
    excluded = {id(owner) for owner in owner_objects}
    pending, seen, size = [iter((value,))], set(), 0
    while pending:
        try:
            current = next(pending[-1])
        except StopIteration:
            pending.pop()
            continue
        identity = id(current)
        if identity in seen or identity in excluded:
            continue
        if len(seen) >= maximum_objects:
            return None
        seen.add(identity)
        kind = type(current)
        if current is None or kind in (bool, int, float, complex, str, bytes, bytearray, Decimal):
            children = ()
        elif isinstance(current, Enum) or isinstance(current, type) or kind is BuiltinFunctionType:
            # These immutable shared definitions are owned by the installed
            # implementation, not by one cached result. Do not follow globals.
            children = ()
        elif kind is FunctionType:
            # Installed function definitions do not own their module globals.
            # Count captures too: frozen dataclass constructors capture object.
            # Only the exact bounded immutable cell contents below are admitted.
            children = (current.__defaults__, current.__kwdefaults__, current.__dict__, current.__closure__)
        elif kind is CellType:
            try:
                captured = current.cell_contents
            except ValueError:
                children = ()
            else:
                if not _immutable_definition_capture(captured, maximum_objects - len(seen)):
                    return None
                children = (captured,)
        elif kind is MethodType:
            children = (current.__self__, current.__func__)
        elif kind is partial:
            children = (current.func, current.args, current.keywords, current.__dict__)
        elif kind is dict:
            children = chain.from_iterable(current.items())
        elif kind in (tuple, list, set, frozenset, deque):
            children = iter(current)
        elif kind is MappingProxyType:
            # Include the actual backing dictionary and its capacity, not just
            # the small proxy header; no copied dictionary is allocated.
            children = iter(gc.get_referents(current))
        elif kind is memoryview:
            children = (current.obj,)
        elif (isinstance(current, (CanonicalRecord, PurePath))
                or kind in (_CanonicalRope, _RecordValidationLifetime, SimpleNamespace) or is_dataclass(current)):
            children = _attributes(current)
        else:
            # Binary scientific data must expose a known owned buffer before
            # it can take this optional route; undercounting is not admission.
            return None
        size += sys.getsizeof(current)
        if size > maximum_bytes:
            return None
        pending.append(iter(children))
    return size


def copy_metadata_containers(value, *, owner_objects=()):
    """Isolate caller-owned projections while sharing immutable typed records.

The admitted graph was already bounded by retained_metadata_bytes. This copy
does not copy scientific record bodies or acquire authority for any owner.
"""
    owned = {id(owner): owner for owner in owner_objects}
    memo = dict(owned)

    def copy(current):
        identity = id(current)
        if identity in memo:
            return memo[identity]
        kind = type(current)
        if isinstance(current, CanonicalRecord):
            if not current._is_cacheable():
                raise TypeError('mutable scientific records cannot enter the metadata cache')
            return current
        if kind is dict:
            result = {}
            memo[identity] = result
            result.update((copy(key), copy(item)) for key, item in current.items())
            return result
        if kind is list:
            result = []
            memo[identity] = result
            result.extend(copy(item) for item in current)
            return result
        if kind is deque:
            result = deque(maxlen=current.maxlen)
            memo[identity] = result
            result.extend(copy(item) for item in current)
            return result
        if kind is tuple:
            result = tuple(copy(item) for item in current)
        elif kind is set:
            result = {copy(item) for item in current}
        elif kind is frozenset:
            result = frozenset(copy(item) for item in current)
        elif kind is MappingProxyType:
            result = MappingProxyType({copy(key): copy(item) for key, item in current.items()})
        elif kind is SimpleNamespace:
            result = SimpleNamespace()
            memo[identity] = result
            vars(result).update((name, copy(item)) for name, item in vars(current).items())
        elif kind is bytearray:
            result = bytearray(current)
        elif kind is partial:
            result = partial(current.func, *copy(current.args), **copy(current.keywords))
            memo[identity] = result
            vars(result).update(copy(vars(current)))
        elif kind is memoryview:
            raise TypeError('live buffer views require the ordinary uncached reader')
        elif is_dataclass(current):
            parameters = getattr(kind, '__dataclass_params__', None)
            if parameters is None or not parameters.frozen:
                raise TypeError('mutable metadata records cannot enter the cache')
            # Noncanonical frozen records are uncommon, but their mutable
            # containers still need an independent snapshot.
            result = object.__new__(kind)
            memo[identity] = result
            for name, item in getattr(current, '__dict__', {}).items():
                object.__setattr__(result, name, copy(item))
            for descriptor, item in _slots(current):
                descriptor.__set__(result, copy(item))
        else:
            return current
        memo[identity] = result
        return result

    return copy(value)
