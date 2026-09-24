"""Apply reviewed PKP3/OpenVAF compatibility edits.

Adapted from EEcircuit-engine's MIT-licensed PKP3 adapter; its license is
included alongside the generated bundle.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

INITIALIZERS = {
    "  real mx = 0.916 * MEL;": "  real mx = 0.916 * 9.11e-31;",
    "  real mxprime = 0.190 * MEL;": "  real mxprime = 0.190 * 9.11e-31;",
    "  real md = 0.190 * MEL;": "  real md = 0.190 * 9.11e-31;",
    "  real mdprime = 0.417 * MEL;": "  real mdprime = 0.417 * 9.11e-31;",
    "  real epsratio = EPSRSUB / EPSROX;": "  real epsratio = 11.9 / 3.9;",
}
MACROS = (
    "EXPL_THRESHOLD", "MAX_EXPL", "MIN_EXPL", "N_MINLOG", "LN_N_MINLOG",
    "lexp", "lln", "hypsmooth", "smoothminx", "smoothmaxx", "smoothmaxx2",
    "gammafunc", "binning",
)
PMOS_INCLUDE = '`include "discipline.h"'
INSTANCE_PARAMETERS = ("L", "W", "NF")


def adapt(name: str, text: str) -> tuple[str, dict[str, object]]:
    """Adapt one pristine source, rejecting any source shape we did not review."""
    module_match = re.findall(r"^module\s+(nmos|pmos)_(lvt|slvt|svt|sramvt)\(", text, re.M)
    if len(module_match) != 1:
        raise RuntimeError(f"PKP3 module declaration drift in {name}")
    polarity, flavor = module_match[0]
    expected_name = f"fusion_ic_{polarity}_{flavor}.va"
    if name != expected_name:
        raise RuntimeError(f"PKP3 module/file mismatch: expected {expected_name}, got {name}")

    result = text
    for parameter in INSTANCE_PARAMETERS:
        original = f"parameter real {parameter}="
        replacement = f'(* type="instance" *) parameter real {parameter}='
        if result.count(original) != 1 or replacement in result:
            raise RuntimeError(f"PKP3 instance-parameter metadata drift in {name}: {parameter}")
        result = result.replace(original, replacement, 1)
    for original, replacement in INITIALIZERS.items():
        if result.count(original) != 1 or replacement in result:
            raise RuntimeError(f"PKP3 initializer source drift in {name}: {original.strip()}")
        result = result.replace(original, replacement, 1)

    include_pattern = re.compile(r'^`include "discipline\.h"\s*\n', re.M)
    include_count = len(include_pattern.findall(result))
    if polarity == "pmos":
        if include_count != 1:
            raise RuntimeError(f"PKP3 PMOS discipline include source drift in {name}")
        result = include_pattern.sub("", result, count=1)
    elif include_count:
        raise RuntimeError(f"Unexpected PMOS-only discipline include in {name}")

    defined = re.findall(r"^\s*`define\s+(\w+)", result, re.M)
    if sorted(defined) != sorted(MACROS):
        raise RuntimeError(f"PKP3 macro set source drift in {name}: {defined}")
    prefix = f"PKP3_{polarity.upper()}_{flavor.upper()}_"
    definition_pattern = re.compile(r"(`define\s+)(" + "|".join(map(re.escape, MACROS)) + r")\b")
    result, definition_substitutions = definition_pattern.subn(lambda match: match.group(1) + prefix + match.group(2), result)
    if definition_substitutions != len(MACROS):
        raise RuntimeError(f"PKP3 macro definition source drift in {name}")
    macro_pattern = re.compile(r"`(" + "|".join(map(re.escape, MACROS)) + r")\b")
    result, reference_substitutions = macro_pattern.subn(lambda match: "`" + prefix + match.group(1), result)
    substitutions = definition_substitutions + reference_substitutions
    if reference_substitutions < len(MACROS):
        raise RuntimeError(f"PKP3 macro reference source drift in {name}")
    if re.search(r"`(" + "|".join(map(re.escape, MACROS)) + r")\b", result):
        raise RuntimeError(f"PKP3 unprefixed macro remains in {name}")

    return result, {
        "source": name,
        "module": f"{polarity}_{flavor}",
        "initializerDeclarationsChanged": len(INITIALIZERS),
        "variableReferencesReplaced": 6,
        "instanceParametersAnnotated": list(INSTANCE_PARAMETERS),
        "removedPmosDisciplineInclude": polarity == "pmos",
        "macroPrefix": prefix,
        "macroTokenSubstitutions": substitutions,
    }


if __name__ == "__main__":
    source, output = map(Path, sys.argv[1:])
    prepared, _ = adapt(source.name, source.read_text())
    output.write_text(prepared)
