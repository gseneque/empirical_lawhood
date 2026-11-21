"""Enforce v1 scientific, authoring, method, execution and custody ownership.

These checks inspect source imports, including imports nested in functions,
relative imports and literal dynamic imports. A package rename cannot silently
weaken the boundary. Nonliteral declared plugin loaders retain their registry owner.
SPDX-License-Identifier: MPL-2.0
"""

import ast
from importlib.util import resolve_name
from pathlib import Path

SOURCE = Path(__file__).parents[1] / "src" / "empirical_lawhood"
OWNERS = frozenset({
    "science", "design", "methods", "domains", "adapters", "execution",
    "storage", "api", "cli", "workbench", "package_data", "examples",
})
ALLOWED = {
    "science": {"science"},
    "design": {"science", "design"},
    "methods": {"science", "design", "methods", "execution", "storage"},
    "execution": {"science", "design", "execution", "storage"},
    "storage": {"science", "design", "execution", "storage"},
    "domains": {"science", "design", "methods", "domains", "adapters", "execution", "storage"},
    "adapters": {"science", "design", "methods", "domains", "adapters", "execution", "storage"},
    "api": OWNERS - {"cli", "workbench", "examples"},
    "cli": OWNERS - {"workbench"},
    "workbench": OWNERS - {"cli", "examples"},
    "examples": OWNERS - {"cli", "workbench"},
    "package_data": {"package_data"},
}
REMOVED = frozenset({"kernel", "planning", "runtime", "resources", "infrastructure"})
NATIVE_ENGINES = frozenset({"pybamm", "openmm", "pyscf", "gpu4pyscf", "cantera", "fipy", "brian2", "torax", "gymtorax", "ash", "xtb", "parmed", "MDAnalysis", "sky"})
NUMERICAL_ENGINES = frozenset({"numpy", "scipy", "pybamm", "openmm", "pyscf", "gpu4pyscf", "cantera", "fipy", "brian2", "torax", "gymtorax"})


def imports(path):
    relative = path.relative_to(SOURCE)
    package = ("empirical_lawhood", *relative.parts[:-1])
    yield from imports_from_source(path.read_text(encoding="utf-8"), package=package)


def imports_from_source(source, *, package):
    tree = ast.parse(source)
    importlib_aliases = {"importlib"}
    import_module_aliases = set()
    builtin_import_aliases = {"__import__"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            importlib_aliases.update(alias.asname or alias.name for alias in node.names
                if alias.name == "importlib")
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            if node.module == "importlib":
                import_module_aliases.update(alias.asname or alias.name for alias in node.names
                    if alias.name == "import_module")
            elif node.module == "builtins":
                builtin_import_aliases.update(alias.asname or alias.name for alias in node.names
                    if alias.name == "__import__")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                base = ".".join(package[:len(package) - node.level + 1]) + ("." + base if base else "")
            yield node.lineno, base
            for alias in node.names:
                yield node.lineno, base + "." + alias.name
        elif isinstance(node, ast.Call):
            is_import_module = (
                isinstance(node.func, ast.Name) and node.func.id in import_module_aliases
                or isinstance(node.func, ast.Attribute) and node.func.attr == "import_module"
                and isinstance(node.func.value, ast.Name) and node.func.value.id in importlib_aliases)
            is_builtin_import = isinstance(node.func, ast.Name) and node.func.id in builtin_import_aliases
            if not (is_import_module or is_builtin_import):
                continue
            keywords = {keyword.arg: keyword.value for keyword in node.keywords}
            name_node = node.args[0] if node.args else keywords.get("name")
            if not isinstance(name_node, ast.Constant) or type(name_node.value) is not str:
                continue
            module = name_node.value
            if is_import_module and module.startswith("."):
                package_node = node.args[1] if len(node.args) > 1 else keywords.get("package")
                if not isinstance(package_node, ast.Constant) or type(package_node.value) is not str:
                    continue
                module = resolve_name(module, package_node.value)
            elif is_builtin_import:
                level_node = node.args[4] if len(node.args) > 4 else keywords.get("level")
                if isinstance(level_node, ast.Constant) and type(level_node.value) is int and level_node.value:
                    module = resolve_name("." * level_node.value + module, ".".join(package))
            yield node.lineno, module


def test_source_imports_follow_documented_layers():
    violations = []
    for path in sorted(SOURCE.rglob("*.py")):
        relative = path.relative_to(SOURCE)
        owner = relative.parts[0]
        if owner not in OWNERS:
            continue
        for line, module in imports(path):
            parts = module.split(".")
            if len(parts) < 2 or parts[0] != "empirical_lawhood":
                if owner != "adapters" and parts[0] in NATIVE_ENGINES:
                    violations.append(f"{relative}:{line}: native engine bridge belongs in adapters: {module}")
                if owner in {"cli", "workbench"} and parts[0] in NUMERICAL_ENGINES:
                    violations.append(f"{relative}:{line}: presentation imports numerical engine {module}")
                continue
            target = parts[1]
            if target in REMOVED:
                violations.append(f"{relative}:{line}: removed package {module}")
            elif target in OWNERS and target not in ALLOWED[owner]:
                violations.append(f"{relative}:{line}: {owner} cannot import {module}")
            elif target == "examples" and relative.as_posix() != "cli/app.py" and owner != "examples":
                violations.append(f"{relative}:{line}: examples cannot supply production implementations")
    assert not violations, "Invalid ownership dependencies:\n" + "\n".join(sorted(set(violations)))


def test_literal_dynamic_imports_cannot_hide_wrong_layer_or_native_contact():
    source = '''
import importlib as loader
from importlib import import_module as select
from builtins import __import__ as builtin_load
def operation():
    loader.import_module("sky")
    select("empirical_lawhood.api.application_context")
    select(".sources", package="empirical_lawhood.api")
    __import__("pyscf")
    builtin_load("api", level=1)
    select(code_owned_registry_key)
    unrelated = "empirical_lawhood.runtime.old"
'''
    modules = {module for _, module in imports_from_source(source, package=("empirical_lawhood",))}
    assert {"sky", "pyscf", "empirical_lawhood.api", "empirical_lawhood.api.sources",
        "empirical_lawhood.api.application_context"} <= modules
    assert "code_owned_registry_key" not in modules
    assert "empirical_lawhood.runtime.old" not in modules


def test_removed_packages_have_no_import_shims():
    assert not [name for name in REMOVED if (SOURCE / name).exists()]
    assert not (SOURCE / "adapters" / "methods").exists()


def test_scientific_schema_identifiers_remain_independent_of_package_paths():
    # Namespaced v0 schema identifiers are retained bytes, not import wrappers.
    from empirical_lawhood.science.records.serialization import CanonicalRecord
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    assert issubclass(ObjectIdentity, CanonicalRecord)
    assert ObjectIdentity.SCHEMA == "empirical-lawhood/kernel/object-identity"


def test_every_source_package_has_a_declared_owner():
    allowed = OWNERS | {"_vendor", "__pycache__"}
    unknown = [path.name for path in SOURCE.iterdir() if path.is_dir() and path.name not in allowed]
    assert not unknown, f"Unclassified source owners: {unknown}"
