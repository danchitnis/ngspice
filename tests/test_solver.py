r"""Check default, SPARSE, and KLU solver selection in local ngspice binaries.

From the repository root on Linux, with binaries matching your architecture:
    python3 tests/test_solver.py linux/ngspice linux/build/osdi/ngspice

Through Docker, using the image created by the standard build:
    docker run --rm -v "$(pwd):/repo:ro" -w /repo ngspice-build \
      python3 tests/test_solver.py linux/ngspice linux/build/osdi/ngspice

Pass one or more executable paths. Each case checks the reported solver and a
0.5 V divider output within 1e-9 V. No OSDI model libraries are required.
"""

import argparse
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile


CASES = (
    ("default", "", "SPARSE 1.3"),
    ("sparse", ".option sparse", "SPARSE 1.3"),
    ("klu", ".option klu", "KLU"),
)
SOLVER = re.compile(r"^Using (.+?) as Direct Linear Solver\s*$", re.MULTILINE)
VOLTAGE = re.compile(r"^v\(out\)\s*=\s*(\S+)\s*$", re.MULTILINE | re.IGNORECASE)


def run_case(executable: Path, name: str, option: str, expected_solver: str) -> bool:
    with tempfile.TemporaryDirectory(prefix="ngspice-solver-") as directory:
        deck = Path(directory) / "divider.cir"
        deck.write_text(
            "Solver selection smoke test\n"
            f"{option}\n"
            "V1 in 0 1\n"
            "R1 in out 1k\n"
            "R2 out 0 1k\n"
            ".control\n"
            "op\n"
            "print v(out)\n"
            "quit\n"
            ".endc\n"
            ".end\n"
        )
        try:
            result = subprocess.run(
                [str(executable), "-n", "-b", str(deck)],
                cwd=directory,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            print(f"FAIL {executable} [{name}]: {error}")
            if isinstance(error, subprocess.TimeoutExpired) and error.stdout:
                output = error.stdout
                print(output.decode(errors="replace") if isinstance(output, bytes) else output)
            return False

    errors = []
    if result.returncode != 0:
        errors.append(f"ngspice exited with status {result.returncode}")
    solvers = SOLVER.findall(result.stdout)
    if not solvers:
        errors.append(f"missing solver report (expected {expected_solver})")
    elif any(solver != expected_solver for solver in solvers):
        errors.append(f"expected solver {expected_solver}, reported {solvers}")
    voltage = VOLTAGE.search(result.stdout)
    if voltage is None:
        errors.append("missing v(out) result")
    else:
        try:
            value = float(voltage[1])
        except ValueError:
            errors.append(f"invalid v(out): {voltage[1]}")
        else:
            if not math.isfinite(value) or abs(value - 0.5) > 1e-9:
                errors.append(f"expected v(out) = 0.5 V within 1e-9 V, got {value}")
    if errors:
        print(f"FAIL {executable} [{name}]: {'; '.join(errors)}")
        print(result.stdout.strip() or "(no simulator output)")
        return False
    print(f"PASS {executable} [{name}]: {expected_solver}, v(out) = {value:g} V")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("executables", nargs="+", type=Path, help="ngspice executable paths")
    args = parser.parse_args()
    passed = True
    for path in args.executables:
        executable = path.resolve()
        if not executable.is_file() or not os.access(executable, os.X_OK):
            print(f"FAIL {executable}: executable is missing or not executable")
            passed = False
            continue
        for name, option, expected_solver in CASES:
            if not run_case(executable, name, option, expected_solver):
                passed = False
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
