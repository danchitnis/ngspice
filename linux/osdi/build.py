"""Build a fresh native ngspice/OSDI bundle inside the Docker builder."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

from pkp_adapter import adapt as adapt_pkp_module


SOURCES = {
    "ngspice": "https://github.com/danchitnis/ngspice-sf-mirror.git",
    "openvaf": "https://github.com/OpenVAF/OpenVAF-Reloaded.git",
    "va_models": "https://github.com/dwarning/VA-Models.git",
    "asap7": "https://github.com/The-OpenROAD-Project/asap7_pdk_r1p7.git",
    "pkp3": "https://github.com/PHIMO-Group/PKP3.git",
}
LEGACY_ASAP7 = {"version", "coremod", "capmod", "nseg", "etaqm"}
PKP_PARAMETERS = ("DVTSHIFT", "U0", "XL", "DeltaWGAA", "DeltaTGAA", "EOT_0")


def run(*args: str, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=cwd, env=env, check=True)


def output(*args: str, cwd: Path | None = None) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clone_sources(work: Path) -> dict[str, Path]:
    result = {}
    for name, url in SOURCES.items():
        path = work / "sources" / name
        run("git", "clone", "--depth", "1", url, str(path))
        result[name] = path
    return result


def build_openvaf(source: Path) -> tuple[Path, dict[str, str | int]]:
    manifest = source / "openvaf/openvaf-driver/Cargo.toml"
    features = tomllib.loads(manifest.read_text()).get("features", {})
    majors = sorted(int(match[1]) for key in features if (match := re.fullmatch(r"llvm(\d+)", key)))
    if not majors:
        raise RuntimeError("The current OpenVAF source advertises no LLVM build feature")
    major = majors[-1]
    installer = Path("/tmp/ngspice-llvm.sh")
    run("curl", "-fsSL", "https://apt.llvm.org/llvm.sh", "-o", str(installer))
    run("bash", str(installer), str(major))
    run("apt-get", "install", "-y", "--no-install-recommends", f"llvm-{major}-dev", f"lld-{major}", f"libpolly-{major}-dev")
    env = os.environ.copy()
    env["PATH"] = f"/usr/lib/llvm-{major}/bin:" + env["PATH"]
    env[f"LLVM_SYS_{major}1_PREFIX"] = f"/usr/lib/llvm-{major}"
    run("cargo", "update", cwd=source, env=env)
    run("cargo", "build", "--release", "--locked", "-p", "openvaf-driver", "--features", f"llvm{major}", cwd=source, env=env)
    compiler = source / "target/release/openvaf-r"
    if not compiler.is_file():
        raise RuntimeError(f"OpenVAF did not produce {compiler}")
    return compiler, {
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "gccVersion": output("gcc", "-dumpfullversion"),
        "llvmMajor": major,
        "llvmVersion": output("/usr/lib/llvm-%d/bin/llvm-config" % major, "--version"),
        "rustVersion": output("rustc", "--version"),
        "cargoVersion": output("cargo", "--version"),
        "cargoLockSha256": sha(source / "Cargo.lock"),
        "llvmInstallerSha256": sha(installer),
        "openvafCompilerSha256": sha(compiler),
    }


def adapt_asap7(source: Path, cmg: Path, bundle: Path) -> tuple[list[dict[str, str]], dict[str, str]]:
    available = {key.lower() for key in re.findall(r"`\w+\((\w+),", (cmg / "bsimcmg_parameters.include").read_text())}
    if not available:
        raise RuntimeError("Cannot discover BSIM-CMG parameters in current VA-Models source")
    raw_dir = source / "models/hspice"
    candidates: dict[str, list[tuple[Path, list[str]]]] = {}
    for path in sorted(raw_dir.glob("7nm_*.pm")):
        match = re.fullmatch(r"7nm_([A-Z]+)(?:_\d+)?\.pm", path.name)
        if not match:
            raise RuntimeError(f"Unrecognized ASAP7 model card: {path.name}")
        blocks = re.split(r"(?im)^\.model\s+", path.read_text())[1:]
        if blocks:
            candidates.setdefault(match[1], []).append((path, blocks))
    if not candidates:
        raise RuntimeError("No ASAP7 transistor corner cards found")
    cards: list[dict[str, str]] = []
    inputs: dict[str, str] = {}
    all_flavors: set[str] | None = None
    destination = bundle / "models/asap7"
    destination.mkdir(parents=True, exist_ok=True)
    for corner, versions in sorted(candidates.items()):
        versions.sort(key=lambda item: len(item[1]), reverse=True)
        if len(versions) > 1:
            for duplicate, duplicate_blocks in versions[1:]:
                if duplicate_blocks != versions[0][1]:
                    raise RuntimeError(f"Conflicting ASAP7 {corner} source cards: {[str(v[0]) for v in versions]}")
                inputs[str(duplicate.relative_to(source))] = sha(duplicate)
        path, blocks = versions[0]
        inputs[str(path.relative_to(source))] = sha(path)
        parsed: dict[tuple[str, str], dict[str, str]] = {}
        for block in blocks:
            name = block.split()[0].lower()
            match = re.fullmatch(r"(nmos|pmos)_([a-z0-9]+)", name)
            if not match:
                raise RuntimeError(f"Unexpected ASAP7 model {name} in {path}")
            polarity = "N" if match[1] == "nmos" else "P"
            flavor = match[2].upper()
            values = {key.lower(): value for line in block.splitlines() if line.lstrip().startswith("+")
                      for key, value in re.findall(r"(\w+)\s*=\s*([^\s]+)", line)}
            unknown = set(values) - available - LEGACY_ASAP7
            if unknown or values.get("version") != "107" or not values:
                raise RuntimeError(f"ASAP7 {name}/{corner} needs review: unknown={sorted(unknown)}, version={values.get('version')}")
            if (flavor, polarity) in parsed:
                raise RuntimeError(f"Duplicate ASAP7 model {name}/{corner}")
            parsed[(flavor, polarity)] = values
        flavors = {flavor for flavor, _ in parsed}
        if all_flavors is not None and flavors != all_flavors:
            raise RuntimeError(f"ASAP7 flavor mismatch in {corner}: {sorted(flavors)}")
        all_flavors = flavors
        for flavor in sorted(flavors):
            if (flavor, "N") not in parsed or (flavor, "P") not in parsed:
                raise RuntimeError(f"Incomplete ASAP7 {flavor}/{corner} NMOS/PMOS pair")
            name = f"modelcard.ASAP7_{flavor}_{corner}"
            lines = [f"* ASAP7 {flavor} {corner}; adapted from BSIM-CMG 107 to current VA-Models BSIM-CMG", f"* Source: {path.name}; see licenses/ASAP7-LICENSE"]
            for polarity, sign in (("N", 1), ("P", -1)):
                values = parsed[(flavor, polarity)]
                lines.append(f".model ASAP7_{flavor}_{corner}_{polarity} bsimcmg_va type={sign}")
                lines.extend(f"+ {key}={value}" for key, value in values.items() if key in available)
            card = destination / name
            card.write_text("\n".join(lines) + "\n")
            cards.append({"family": "ASAP7", "flavor": flavor, "corner": corner, "file": str(card.relative_to(bundle))})
    if "RVT" not in (all_flavors or set()):
        raise RuntimeError("ASAP7 RVT flavor is required by the corner example template")
    return cards, inputs


def adapt_pkp3(source: Path, prepared: Path, bundle: Path) -> tuple[list[dict[str, str]], dict[str, str]]:
    va_dir = source / "models/PHIMO/VERILOG-A"
    va_files = sorted(va_dir.rglob("*.va"))
    if not va_files:
        raise RuntimeError("No PKP3 PHIMO-NN Verilog-A modules found")
    prepared.mkdir(parents=True)
    modules: set[tuple[str, str]] = set()
    inputs: dict[str, str] = {}
    for path in va_files:
        adapted, report = adapt_pkp_module(path.name, path.read_text())
        polarity, flavor = str(report["module"]).split("_", 1)
        key = (flavor.upper(), polarity.upper()[0])
        if key in modules:
            raise RuntimeError(f"Duplicate PKP3 module {key}")
        modules.add(key)
        (prepared / path.name).write_text(adapted)
        inputs[str(path.relative_to(source))] = sha(path)
    flavors = {flavor for flavor, _ in modules}
    if any((flavor, polarity) not in modules for flavor in flavors for polarity in ("N", "P")):
        raise RuntimeError("Incomplete PKP3 PHIMO-NN NMOS/PMOS module pair")
    (prepared / "pkp3.va").write_text("".join(f'`include "{path.name}"\n' for path in sorted(prepared.glob("*.va"))))

    card_dir = source / "models/PHIMO/MODELCARD"
    source_cards = sorted(card_dir.glob("*_modelcard.pm"))
    if not source_cards:
        raise RuntimeError("No PKP3 process-corner cards found")
    destination = bundle / "models/pkp3"
    destination.mkdir(parents=True, exist_ok=True)
    cards: list[dict[str, str]] = []
    for path in source_cards:
        match = re.fullmatch(r"([A-Z]+)_modelcard\.pm", path.name)
        if not match:
            raise RuntimeError(f"Unrecognized PKP3 model card: {path.name}")
        corner = match[1]
        inputs[str(path.relative_to(source))] = sha(path)
        lines = path.read_text().splitlines()
        entries: dict[tuple[str, str], dict[str, str]] = {}
        for index, line in enumerate(lines):
            model = re.fullmatch(r"\s*\*?\.model\s+((?:nmos|pmos)_[a-z0-9]+)\s+\1\s*", line, re.I)
            if not model:
                continue
            if index + 1 >= len(lines):
                raise RuntimeError(f"Missing PKP3 parameter line after {path}:{index + 1}")
            continuation = re.fullmatch(r"\s*\*?\+\s*(.*)", lines[index + 1])
            if not continuation:
                raise RuntimeError(f"Invalid PKP3 parameter line after {path}:{index + 1}")
            values = {key.lower(): (key, value) for key, value in re.findall(r"([A-Za-z0-9_]+)=([^\s]+)", continuation[1])}
            if set(values) != {key.lower() for key in PKP_PARAMETERS}:
                raise RuntimeError(f"PKP3 parameter change in {path}:{index + 1}: {sorted(values)}")
            polarity, flavor = model[1].lower().split("_", 1)
            key = (flavor.upper(), polarity.upper()[0])
            if key in entries:
                raise RuntimeError(f"Duplicate PKP3 model {key}/{corner}")
            entries[key] = {key: values[key.lower()][1] for key in PKP_PARAMETERS}
        if set(entries) != modules:
            raise RuntimeError(f"PKP3 {corner} card/module mismatch: missing={sorted(modules-set(entries))}, extra={sorted(set(entries)-modules)}")
        for flavor in sorted(flavors):
            name = f"modelcard.PKP3_{flavor}_{corner}"
            card = destination / name
            text = [f"* PKP3 PHIMO-NN {flavor} {corner}; adapted from {path.name}", "* Predictive research model; see licenses/PKP3-LICENSE"]
            for polarity in ("N", "P"):
                values = entries[(flavor, polarity)]
                params = " ".join(f"{key}={values[key]}" for key in PKP_PARAMETERS)
                source_name = f"{'nmos' if polarity == 'N' else 'pmos'}_{flavor.lower()}"
                text.append(f".model PKP3_{flavor}_{corner}_{polarity} {source_name} {params}")
            card.write_text("\n".join(text) + "\n")
            cards.append({"family": "PKP3", "flavor": flavor, "corner": corner, "file": str(card.relative_to(bundle))})
    if "LVT" not in flavors:
        raise RuntimeError("PKP3 LVT flavor is required by the corner example template")
    return cards, inputs


def build_catalog(compiler: Path, cmg: Path, prepared: Path, bundle: Path, work: Path) -> None:
    catalog = work / "catalog.va"
    catalog.write_text(f'`include "{cmg / "bsimcmg.va"}"\n`include "{prepared / "pkp3.va"}"\n')
    run(str(compiler), "-I", str(cmg), "-I", str(prepared), str(catalog), "-o", str(bundle / "catalog.osdi"))


def build_ngspice(source: Path, bundle: Path) -> None:
    run("./autogen.sh", cwd=source)
    release = source / "release"
    release.mkdir()
    run("../configure", "--disable-debug", "--enable-openmp", "--with-readline=no", "--enable-osdi", cwd=release)
    run("make", f"-j{min(os.cpu_count() or 2, 8)}", cwd=release)
    shutil.copy2(release / "src/ngspice", bundle / "ngspice")


def add_examples(bundle: Path, cards: list[dict[str, str]]) -> None:
    for family, template_name, flavor in (("ASAP7", "asap7", "RVT"), ("PKP3", "pkp3", "LVT")):
        template = (Path("/opt/ngspice-osdi/examples") / template_name / "inverter.cir.in").read_text()
        folder = bundle / "examples" / template_name
        folder.mkdir(parents=True)
        for corner in sorted({card["corner"] for card in cards if card["family"] == family}):
            if not any(card["family"] == family and card["flavor"] == flavor and card["corner"] == corner for card in cards):
                raise RuntimeError(f"Missing {family} {flavor}/{corner} example model")
            (folder / f"{corner.lower()}.cir").write_text(template.replace("@CORNER@", corner))


def add_licenses(sources: dict[str, Path], bundle: Path) -> None:
    folder = bundle / "licenses"
    folder.mkdir()
    for name, source, candidates in (
        ("ASAP7-LICENSE", sources["asap7"], ("LICENSE", "LICENSE.txt")),
        ("PKP3-LICENSE", sources["pkp3"], ("LICENSE", "LICENSE.txt")),
        ("ngspice-LICENSE", sources["ngspice"], ("COPYING", "LICENSE", "COPYRIGHT")),
    ):
        found = next((source / candidate for candidate in candidates if (source / candidate).is_file()), None)
        if found is None:
            raise RuntimeError(f"Cannot find upstream {name} in {source}")
        shutil.copy2(found, folder / name)
    cmg_license = sources["va_models"] / "code/bsimcmg/vacode/LICENSE.txt"
    if not cmg_license.is_file() or "Educational Community License" not in cmg_license.read_text():
        raise RuntimeError("BSIM-CMG license file changed; review before distributing")
    shutil.copy2(cmg_license, folder / "BSIM-CMG-LICENSE")
    shutil.copy2(Path("/opt/ngspice-osdi/EEcircuit-engine-LICENSE.txt"), folder / "EEcircuit-engine-LICENSE")


def main(bundle: Path) -> None:
    work = Path("/work/ngspice-osdi")
    work.mkdir(parents=True, exist_ok=True)
    sources = clone_sources(work)
    compiler, toolchain = build_openvaf(sources["openvaf"])
    cmg = sources["va_models"] / "code/bsimcmg/vacode"
    if not (cmg / "bsimcmg.va").is_file():
        raise RuntimeError("Current VA-Models source does not contain BSIM-CMG")
    asap_cards, asap_inputs = adapt_asap7(sources["asap7"], cmg, bundle)
    prepared = work / "prepared/pkp3"
    pkp_cards, pkp_inputs = adapt_pkp3(sources["pkp3"], prepared, bundle)
    cards = asap_cards + pkp_cards
    build_catalog(compiler, cmg, prepared, bundle, work)
    build_ngspice(sources["ngspice"], bundle)
    add_examples(bundle, cards)
    add_licenses(sources, bundle)
    manifest = {
        "schemaVersion": 1,
        "policy": "fresh default-branch HEAD on every build; no pinned source revisions",
        "sources": {name: {"url": SOURCES[name], "commit": output("git", "rev-parse", "HEAD", cwd=path),
                           "branch": output("git", "branch", "--show-current", cwd=path)} for name, path in sources.items()},
        "toolchain": toolchain,
        "sourceInputsSha256": {"asap7": asap_inputs, "pkp3": pkp_inputs,
                               "bsimcmg.va": sha(cmg / "bsimcmg.va"), "bsimcmg_parameters.include": sha(cmg / "bsimcmg_parameters.include"),
                               "bsimcmg/LICENSE.txt": sha(cmg / "LICENSE.txt")},
        "models": cards,
        "artifactsSha256": {str(path.relative_to(bundle)): sha(path) for path in sorted(bundle.rglob("*")) if path.is_file()},
    }
    (bundle / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    run("python3", "/opt/ngspice-osdi/verify.py", str(bundle), "--smoke")


if __name__ == "__main__":
    target = Path(sys.argv[1]).resolve()
    try:
        main(target)
    finally:
        uid, gid = os.environ.get("HOST_UID"), os.environ.get("HOST_GID")
        if uid is not None and gid is not None:
            run("chown", "-R", f"{uid}:{gid}", str(target))
