"""Check an exported OSDI bundle and optionally run its Linux simulator."""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path


NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
DATA_ROW = re.compile(rf"^\s*\d+\s+({NUMBER})\s+({NUMBER})(?:\s|$)", re.M)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_deck(bundle: Path, deck: Path) -> list[float]:
    result = subprocess.run([str(bundle / "ngspice"), "-b", str(deck)], cwd=bundle,
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if result.returncode or re.search(r"\b(error|unknown model|unrecognized)\b", result.stdout, re.I):
        raise RuntimeError(f"{deck.name} failed:\n{result.stdout[-5000:]}")
    values = [float(match[2]) for match in DATA_ROW.finditer(result.stdout)]
    if len(values) < 2 or not all(math.isfinite(value) for value in values):
        raise RuntimeError(f"{deck.name} produced no finite DC sweep:\n{result.stdout[-5000:]}")
    return values


def verify(bundle: Path, smoke: bool) -> dict[str, object]:
    manifest = json.loads((bundle / "manifest.json").read_text())
    if manifest.get("policy") != "fresh default-branch HEAD on every build; no pinned source revisions":
        raise RuntimeError("Unexpected source-selection policy")
    if set(manifest["sources"]) != {"ngspice", "openvaf", "va_models", "asap7", "pkp3"}:
        raise RuntimeError("Missing upstream source record")
    for name, source in manifest["sources"].items():
        if not re.fullmatch(r"[0-9a-f]{40}", source["commit"]) or not source["branch"]:
            raise RuntimeError(f"Invalid resolved source revision for {name}")
    expected = manifest["artifactsSha256"]
    actual = {str(path.relative_to(bundle)): sha(path) for path in bundle.rglob("*") if path.is_file() and path.name != "manifest.json"}
    if actual != expected:
        raise RuntimeError(f"Bundle artifact mismatch: missing={sorted(set(expected)-set(actual))}, extra={sorted(set(actual)-set(expected))}, changed={sorted(k for k in set(actual)&set(expected) if actual[k] != expected[k])}")
    if any(Path(name).suffix.lower() in {".va", ".pm"} for name in actual):
        raise RuntimeError("Raw Verilog-A or PDK model sources leaked into the output bundle")
    cards = manifest["models"]
    if not cards or len({(card["family"], card["flavor"], card["corner"]) for card in cards}) != len(cards):
        raise RuntimeError("Missing or duplicate model cards")
    if {card["file"] for card in cards} != {name for name in expected if name.startswith("models/")}:
        raise RuntimeError("Model card inventory does not match the manifest")
    for card in cards:
        text = (bundle / card["file"]).read_text()
        for polarity in ("N", "P"):
            model_name = f"{card['family']}_{card['flavor']}_{card['corner']}_{polarity}"
            if not re.search(rf"(?mi)^\.model\s+{re.escape(model_name)}\s+", text):
                raise RuntimeError(f"Missing {model_name} in {card['file']}")
    family_corners = {family: {card["corner"] for card in cards if card["family"] == family} for family in ("ASAP7", "PKP3")}
    for family, corners in family_corners.items():
        folder = bundle / "examples" / family.lower()
        if {path.stem.upper() for path in folder.glob("*.cir")} != corners:
            raise RuntimeError(f"{family} examples do not cover every corner")
    if not smoke:
        return {"cards": len(cards), "examples": sum(map(len, family_corners.values()))}

    for family in ("ASAP7", "PKP3"):
        for deck in sorted((bundle / "examples" / family.lower()).glob("*.cir")):
            run_deck(bundle, deck)

    currents: dict[tuple[str, str, str, str], float] = {}
    with tempfile.TemporaryDirectory(prefix="ngspice-osdi-smoke-") as directory:
        temporary = Path(directory)
        for card in cards:
            for polarity in ("N", "P"):
                family, flavor, corner = card["family"], card["flavor"], card["corner"]
                voltage = "0.7" if polarity == "N" else "-0.7"
                end = "0.7 0.35" if polarity == "N" else "-0.7 -0.35"
                geometry = "L=21n NFIN=1" if family == "ASAP7" else "L=16n W=35n NF=1"
                deck = temporary / f"{family}_{flavor}_{corner}_{polarity}.cir"
                deck.write_text(
                    f"{family} {flavor} {corner} {polarity} smoke\n"
                    f".include {bundle / card['file']}\n"
                    f"VDS d 0 {voltage}\nVG g 0 0\n"
                    f"N1 d g 0 0 {family}_{flavor}_{corner}_{polarity} {geometry}\n"
                    f".control\npre_osdi {bundle / 'catalog.osdi'}\n.endc\n"
                    f".dc VG 0 {end}\n.print dc i(VDS)\n.end\n"
                )
                values = run_deck(bundle, deck)
                currents[(family, flavor, corner, polarity)] = abs(values[-1])
    for family, flavor in (("ASAP7", "RVT"), ("PKP3", "LVT")):
        if {"FF", "SS"} <= family_corners[family]:
            for polarity in ("N", "P"):
                fast = currents[(family, flavor, "FF", polarity)]
                slow = currents[(family, flavor, "SS", polarity)]
                if not fast > slow:
                    raise RuntimeError(f"{family} {flavor} {polarity}: FF current {fast} is not above SS {slow}")
    return {"cards": len(cards), "devices": len(currents), "examples": sum(map(len, family_corners.values()))}


if __name__ == "__main__":
    result = verify(Path(sys.argv[1]).resolve(), "--smoke" in sys.argv[2:])
    print(json.dumps(result, sort_keys=True))
