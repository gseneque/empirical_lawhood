# SPDX-License-Identifier: MPL-2.0
"""Independent interpretation of retained LEaP diagnostics, without native work.

Exit status and emitted topology files are not a construction-quality verdict.
Warnings remain unresolved until an explicitly authored scientific assessment
explains them; no warning category is silently waived by this default policy.
"""

from hashlib import sha256
import re


def assess_leap_diagnostics(stdout, stderr, *, complete_endpoint_satisfied=False, final_charge_balanced=False,
                            selected_integral_dry_charge=False):
    if type(stdout) is not bytes or type(stderr) is not bytes:
        raise TypeError("LEaP assessment requires the original stdout and stderr bytes")
    text = stdout.decode("utf-8", errors="replace") + "\n" + stderr.decode("utf-8", errors="replace")
    summary = re.findall(r"Errors\s*=\s*(\d+)\s*;\s*Warnings\s*=\s*(\d+)", text, flags=re.IGNORECASE)
    diagnostic_lines = tuple((number, line) for number, line in enumerate(text.splitlines(), 1)
        if re.search(r"\b(?:warning|fatal|error)\b|close contact|unusually short|could not find", line, re.IGNORECASE)
        and not re.search(r"Errors\s*=\s*\d+\s*;\s*Warnings\s*=\s*\d+", line, re.IGNORECASE))
    findings = set()
    if len(summary) != 1:
        findings.add("leap-completion-summary-missing-or-ambiguous")
    if any(int(errors) for errors, _ in summary):
        findings.add("leap-errors")
    resolved, unresolved = [], []
    for item in diagnostic_lines:
        line = item[1]
        geometric = bool(re.search(r"close contact|unusually short|bond of\s+[0-9.]+\s+angstrom", line, re.IGNORECASE))
        charge = bool(re.search(r"(?:unperturbed|total|net) charge.*(?:not zero|non.?integral|not integral)", line, re.IGNORECASE))
        fatal = bool(re.search(r"fatal|could not find|missing parameter|unknown residue|\berror\b", line, re.IGNORECASE))
        if not fatal and (geometric and complete_endpoint_satisfied
                or charge and (final_charge_balanced or selected_integral_dry_charge)):
            resolved.append(item)
        else:
            unresolved.append(item)
    # A missing printed diagnostic cannot be explained by a later minimizer.
    warned = max((int(warnings) for _, warnings in summary), default=0)
    if unresolved or warned > len(resolved) or diagnostic_lines and not resolved:
        findings.add("leap-unresolved-diagnostics")
    return {"disposition": "REJECTED" if findings else "SCREEN_PASSED",
        "findings": sorted(findings), "diagnostic_lines": diagnostic_lines,
        "resolved_by_complete_endpoint": tuple(resolved), "unresolved_diagnostics": tuple(unresolved),
        "selected_integral_nonperiodic_charge": selected_integral_dry_charge,
        "reported_summaries": tuple((int(errors), int(warnings)) for errors, warnings in summary),
        "stdout_sha256": sha256(stdout).hexdigest(), "stderr_sha256": sha256(stderr).hexdigest(),
        "scope": "LEAP_DIAGNOSTICS_ONLY_NOT_ALL_ATOM_GEOMETRY_OR_FORCE_ACCURACY"}
