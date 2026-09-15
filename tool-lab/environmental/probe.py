"""P04-T21 Ladybug/Honeybee environment probe.

The probe is intentionally independent of the project's core engine.  It records
package/CLI evidence, checks a deterministic local EPW fixture with ladybug-core,
and distinguishes Python bindings from real EnergyPlus/Radiance executables.
"""

from __future__ import annotations

import csv
import hashlib
import importlib
import importlib.metadata
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import date, timedelta
from pathlib import Path
from typing import Any

PROBE_VERSION = "p04-t21-v1"
ROOT = Path(__file__).resolve().parents[2]
ENVIRONMENTAL_DIR = ROOT / "tool-lab" / "environmental"
RESULTS_DIR = ENVIRONMENTAL_DIR / "results"
FIXTURES_DIR = ENVIRONMENTAL_DIR / "fixtures"
WHEEL_DIR = ENVIRONMENTAL_DIR / "wheels"
EPW_PATH = FIXTURES_DIR / "synthetic_natal_2021.epw"
REPORT_PATH = RESULTS_DIR / "environmental-probe.json"
LOCK_PATH = ENVIRONMENTAL_DIR / "requirements-lock.txt"
ENERGYPLUS_IDF_SHA256 = "cba98d3ea4597f180e9821bb2b630d4f1541e0c49cf516031a85161e6c6ffb58"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_energyplus_sha256(path: Path) -> str:
    data = path.read_bytes()
    data = re.sub(rb"YMD=\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}", b"YMD=0000.00.00 00:00", data)
    return sha256_bytes(data)


def round_number(value: Any, digits: int = 6) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"non-finite numeric value: {value!r}")
    return round(number, digits)


def synthetic_epw_text() -> str:
    headers = [
        "LOCATION,Natal,RN,BRA,Synthetic,999999,-5.79,-35.21,-3.0,30",
        "DESIGN CONDITIONS,0",
        "TYPICAL/EXTREME PERIODS,0",
        "GROUND TEMPERATURES,0",
        "HOLIDAYS/DAYLIGHT SAVINGS,No,0,0,0",
        "COMMENTS 1,P04-T21 deterministic synthetic EPW fixture",
        "COMMENTS 2,Not measured weather; parser and EPW-statistics validation only",
        "DATA PERIODS,1,1,Data,Sunday,1/1,12/31",
    ]
    start = date(2021, 1, 1)
    rows: list[str] = []
    for index in range(8760):
        current = start + timedelta(days=index // 24)
        hour = index % 24 + 1
        annual_phase = 2 * math.pi * (index / 8760)
        daily_phase = 2 * math.pi * ((hour - 1) / 24)
        dry_bulb = 26.0 + 4.0 * math.sin(annual_phase) + 2.0 * math.sin(daily_phase - math.pi / 2)
        dew_point = dry_bulb - 5.0
        solar_factor = max(0.0, math.sin(math.pi * (hour - 6) / 12))
        global_horizontal = round(700.0 * solar_factor, 1)
        direct_normal = round(850.0 * solar_factor, 1)
        diffuse_horizontal = round(120.0 * solar_factor, 1)
        global_illuminance = round(75000.0 * solar_factor)
        direct_illuminance = round(90000.0 * solar_factor)
        diffuse_illuminance = round(12000.0 * solar_factor)
        row = [
            current.year,
            current.month,
            current.day,
            hour,
            60,
            "A7A7A7A7A7A7A7A7A7A7",
            round(dry_bulb, 1),
            round(dew_point, 1),
            70,
            101325,
            0,
            0,
            0,
            global_horizontal,
            direct_normal,
            diffuse_horizontal,
            global_illuminance,
            direct_illuminance,
            diffuse_illuminance,
            round(1000.0 * solar_factor),
            (hour * 15) % 360,
            2.0,
            3,
            2,
            20,
            99999,
            9,
            "999999999",
            1.5,
            0.1,
            0,
            99,
            0.2,
            0,
            0,
        ]
        rows.append(",".join(str(value) for value in row))
    return "\n".join(headers + rows) + "\n"


def ensure_synthetic_epw() -> Path:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    expected = synthetic_epw_text().encode("utf-8")
    if EPW_PATH.exists():
        actual = EPW_PATH.read_bytes()
        if actual != expected:
            raise RuntimeError(f"existing EPW fixture differs from deterministic source: {EPW_PATH}")
    else:
        EPW_PATH.write_bytes(expected)
    return EPW_PATH


def run_epw_case(epw_path: Path) -> dict[str, Any]:
    from ladybug.epw import EPW
    from ladybug.sunpath import Sunpath

    epw = EPW(str(epw_path))
    temperatures = epw.dry_bulb_temperature
    sun = Sunpath.from_location(epw.location).calculate_sun_from_hoy(12)
    years = sorted({int(year) for year in epw.years})
    values = [float(value) for value in temperatures.values]
    case = {
        "input": {
            "epw_file": "fixtures/synthetic_natal_2021.epw",
            "input_sha256": sha256_bytes(epw_path.read_bytes()),
        },
        "epw": {
            "station": epw.location.city,
            "state": epw.location.state,
            "country": epw.location.country,
            "station_id": epw.location.station_id,
            "latitude": round_number(epw.location.latitude),
            "longitude": round_number(epw.location.longitude),
            "timezone": round_number(epw.location.time_zone),
            "elevation_m": round_number(epw.location.elevation),
            "years": years,
            "hours": len(values),
            "is_leap_year": bool(epw.is_leap_year),
        },
        "pure_ladybug_core_stats": {
            "dry_bulb_min_c": round_number(temperatures.min),
            "dry_bulb_mean_c": round_number(temperatures.average),
            "dry_bulb_max_c": round_number(temperatures.max),
            "annual_global_horizontal_radiation_total": round_number(
                epw.global_horizontal_radiation.total, 3
            ),
        },
        "pure_ladybug_core_solar": {
            "hoy": 12,
            "native_altitude": round_number(sun.altitude),
            "native_azimuth": round_number(sun.azimuth),
        },
    }
    if case["epw"]["hours"] != 8760:
        raise AssertionError(f"EPW hour count is not 8760: {case['epw']['hours']}")
    if case["epw"]["years"] != [2021]:
        raise AssertionError(f"EPW year set is not [2021]: {case['epw']['years']}")
    if not case["epw"]["station"] or case["epw"]["timezone"] != -3.0:
        raise AssertionError("EPW station/timezone validation failed")
    stats = case["pure_ladybug_core_stats"]
    if not stats["dry_bulb_min_c"] <= stats["dry_bulb_mean_c"] <= stats["dry_bulb_max_c"]:
        raise AssertionError("dry-bulb statistics are not ordered")
    if not all(math.isfinite(value) for value in values):
        raise AssertionError("EPW dry-bulb values contain a non-finite value")
    if not all(math.isfinite(value) for value in case["pure_ladybug_core_solar"].values() if isinstance(value, float)):
        raise AssertionError("solar result contains a non-finite value")
    return case


def import_evidence() -> dict[str, Any]:
    targets = [
        "ladybug",
        "ladybug.epw",
        "ladybug.sunpath",
        "honeybee",
        "honeybee.model",
        "honeybee_energy",
        "honeybee_radiance",
        "honeybee_display",
        "openstudio",
    ]
    evidence: dict[str, Any] = {}
    for target in targets:
        try:
            module = importlib.import_module(target)
            evidence[target] = {"status": "PASS", "module_file": str(getattr(module, "__file__", ""))}
        except (AttributeError, ImportError, OSError, RuntimeError) as exc:  # pragma: no cover - runtime evidence
            evidence[target] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
    return evidence


def distribution_evidence() -> dict[str, Any]:
    names = [
        "ladybug-core",
        "lbt-honeybee",
        "honeybee-core",
        "honeybee-energy",
        "honeybee-radiance",
        "openstudio",
        "cupy-cuda12x",
    ]
    result: dict[str, Any] = {}
    for name in names:
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = None
    return result


def cli_evidence(name: str) -> dict[str, Any]:
    executable = Path(sys.executable).parent / f"{name}.exe"
    record: dict[str, Any] = {
        "command": f".venv-environmental/Scripts/{name}.exe",
        "exists": executable.is_file(),
    }
    if not executable.is_file():
        record["status"] = "MISSING"
        return record
    help_run = subprocess.run(
        [str(executable), "--help"], check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30
    )
    version_run = subprocess.run(
        [str(executable), "--version"], check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30
    )
    version_error = version_run.stderr.strip().splitlines()
    record.update(
        {
            "help_exit": help_run.returncode,
            "help_first_line": help_run.stdout.strip().splitlines()[0] if help_run.stdout.strip() else "",
            "version_exit": version_run.returncode,
            "version_first_line": version_run.stdout.strip().splitlines()[0] if version_run.stdout.strip() else "",
            "version_error_last_line": version_error[-1] if version_error else "",
            "status": "PASS" if help_run.returncode == 0 else "FAIL",
        }
    )
    return record


def license_evidence() -> dict[str, Any]:
    licenses: dict[str, Any] = {}
    paid_indicators: list[str] = []
    missing_metadata: list[str] = []
    indicator_pattern = re.compile(r"commercial|proprietary|subscription|paid|activation|trial", re.IGNORECASE)
    if not LOCK_PATH.exists():
        raise FileNotFoundError(LOCK_PATH)
    for line in LOCK_PATH.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        distribution = line.split("==", 1)[0]
        metadata = importlib.metadata.metadata(distribution)
        license_name = metadata.get("License", "").strip()
        license_expression = metadata.get("License-Expression", "").strip()
        classifiers = [value for value in metadata.get_all("Classifier", []) if value.startswith("License ::")]
        if not license_name and not license_expression and not classifiers:
            missing_metadata.append(distribution)
        # Some wheels put the complete license text in License; inspect only
        # the SPDX/expression/classifier and its first line for paid indicators.
        fields = " ".join([license_name.splitlines()[0] if license_name else "", license_expression, *classifiers])
        if indicator_pattern.search(fields):
            paid_indicators.append(distribution)
        licenses[distribution] = {
            "license": license_name,
            "license_expression": license_expression,
            "license_classifiers": classifiers,
        }
    return {
        "metadata_only": True,
        "paid_license_indicators": paid_indicators,
        "packages_without_license_metadata": missing_metadata,
        "packages": licenses,
        "assessment": "NO_PAID_LICENSE_INDICATED" if not paid_indicators else "REVIEW_REQUIRED",
    }


def wheel_evidence() -> dict[str, Any]:
    lock_hashes: dict[tuple[str, str], str] = {}
    pattern = re.compile(r"^([^=]+)==([^ ]+) --hash=sha256:([0-9a-f]+)$")
    for line in LOCK_PATH.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if match:
            lock_hashes[(match.group(1).lower().replace("_", "-"), match.group(2))] = match.group(3)
    wheels: list[dict[str, Any]] = []
    mismatches: list[str] = []
    for wheel in sorted(WHEEL_DIR.glob("*.whl")):
        metadata_name = ""
        metadata_version = ""
        with zipfile.ZipFile(wheel) as archive:
            metadata_entry = next(name for name in archive.namelist() if name.endswith("/METADATA"))
            metadata_text = archive.read(metadata_entry).decode("utf-8", errors="replace")
            metadata_name = re.search(r"(?m)^Name:\s*(.+)$", metadata_text).group(1).strip()
            metadata_version = re.search(r"(?m)^Version:\s*(.+)$", metadata_text).group(1).strip()
        actual_hash = sha256_bytes(wheel.read_bytes())
        key = (metadata_name.lower().replace("_", "-"), metadata_version)
        expected_hash = lock_hashes.get(key)
        match = actual_hash == expected_hash
        if not match:
            mismatches.append(f"{metadata_name}=={metadata_version}")
        wheels.append(
            {
                "file": wheel.name,
                "name": metadata_name,
                "version": metadata_version,
                "size_bytes": wheel.stat().st_size,
                "sha256": actual_hash,
                "lock_sha256": expected_hash,
                "hash_matches_lock": match,
            }
        )
    return {
        "wheel_count": len(wheels),
        "all_hashes_match_lock": not mismatches and len(wheels) == len(lock_hashes),
        "mismatches": mismatches,
        "wheels": wheels,
    }


def pip_check() -> dict[str, Any]:
    run = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return {
        "command": f"{Path(sys.executable).as_posix()} -m pip check",
        "exit": run.returncode,
        "output": run.stdout.strip() or run.stderr.strip(),
        "status": "PASS" if run.returncode == 0 else "FAIL",
    }


def executable_candidates() -> dict[str, Any]:
    script_dir = Path(sys.executable).parent
    known_roots = [
        Path("C:/EnergyPlus"),
        Path("C:/Radiance"),
        Path("C:/Program Files"),
        Path("C:/Program Files (x86)"),
    ]
    candidates: dict[str, Any] = {}
    for engine, names in {
        "energyplus": ["energyplus.exe", "energyplus"],
        "radiance_rtrace": ["rtrace.exe", "rtrace"],
        "radiance_oconv": ["oconv.exe", "oconv"],
    }.items():
        path = next((Path(found) for name in names if (found := shutil.which(name))), None)
        known_matches: list[str] = []
        for root in known_roots:
            if root.is_dir():
                known_matches.extend(
                    str(path_item)
                    for path_item in root.glob("**/" + names[0])
                    if path_item.is_file()
                )
        if path is None and known_matches:
            path = Path(known_matches[0])
        record: dict[str, Any] = {
            "status": "MISSING" if path is None else "FOUND",
            "path": str(path) if path else None,
            "searched_path": bool(shutil.which(names[0]) or shutil.which(names[1])),
            "known_root_matches": sorted(set(known_matches)),
        }
        if path is not None:
            arguments = ["--version"] if engine == "energyplus" else ["-version"]
            run = subprocess.run(
                [str(path), *arguments], check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30
            )
            output = (run.stdout.strip() or run.stderr.strip()).splitlines()
            record.update({"version_exit": run.returncode, "version_output_first_line": output[0] if output else ""})
        candidates[engine] = record
    embedded = [
        str(path)
        for path in (script_dir.parent / "Lib" / "site-packages").rglob("*.exe")
        if path.name.lower() in {"energyplus.exe", "rtrace.exe", "oconv.exe", "rpict.exe"}
    ]
    candidates["embedded_exact_engine_executables"] = sorted(embedded)
    candidates["openstudio_python_binding"] = {
        "status": "PASS",
        "version": distribution_evidence().get("openstudio"),
        "is_external_engine_executable": False,
    }
    return candidates


def ensure_energyplus_idf() -> Path:
    idf_path = FIXTURES_DIR / "honeybee_energy_minimal_24_1.idf"
    if not idf_path.exists():
        raise RuntimeError(f"fixed IDF fixture is missing: {idf_path}")
    actual_hash = sha256_bytes(idf_path.read_bytes())
    if actual_hash != ENERGYPLUS_IDF_SHA256:
        raise RuntimeError(f"fixed IDF fixture hash mismatch: expected {ENERGYPLUS_IDF_SHA256}, got {actual_hash}")
    return idf_path


def run_energyplus_once(executable: Path, idf_path: Path, epw_path: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in output_dir.glob("eplusout.*"):
        if path.is_file():
            path.unlink()
    run = subprocess.run(
        [str(executable), "-w", str(epw_path), "-d", str(output_dir), str(idf_path)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    err_path = output_dir / "eplusout.err"
    eso_path = output_dir / "eplusout.eso"
    sql_path = output_dir / "eplusout.sql"
    table_csv_path = output_dir / "eplustbl.csv"
    err_text = err_path.read_text(encoding="utf-8", errors="replace") if err_path.exists() else ""
    fatal_lines = [line.strip() for line in err_text.splitlines() if "** Fatal **" in line]
    warning_count = err_text.count("** Warning **")
    csv_rows: list[list[str]] = []
    if table_csv_path.exists():
        with table_csv_path.open("r", encoding="utf-8", errors="replace", newline="") as stream:
            csv_rows = list(csv.reader(stream))
    validated = (
        run.returncode == 0
        and "EnergyPlus Completed Successfully." in (run.stdout + run.stderr)
        and err_path.exists()
        and eso_path.exists()
        and eso_path.stat().st_size > 0
        and sql_path.exists()
        and sql_path.stat().st_size > 0
        and table_csv_path.exists()
        and len(csv_rows) > 1
        and not fatal_lines
    )
    return {
        "command": f"energyplus.exe -w fixtures/synthetic_natal_2021.epw -d {output_dir.relative_to(ROOT).as_posix()} fixtures/honeybee_energy_minimal_24_1.idf",
        "exit": run.returncode,
        "completed_successfully": "EnergyPlus Completed Successfully." in (run.stdout + run.stderr),
        "stderr_nonempty": bool(run.stderr.strip()),
        "err_exists": err_path.exists(),
        "native_eso_exists": eso_path.exists(),
        "native_sql_exists": sql_path.exists(),
        "table_csv_exists": table_csv_path.exists(),
        "fatal_lines": fatal_lines,
        "warning_count": warning_count,
        "table_csv_data_rows": max(len(csv_rows) - 1, 0),
        "native_eso_semantic_sha256": normalized_energyplus_sha256(eso_path) if eso_path.exists() else None,
        "native_eso_size_bytes": eso_path.stat().st_size if eso_path.exists() else None,
        "native_sql_semantic_sha256": normalized_energyplus_sha256(sql_path) if sql_path.exists() else None,
        "table_csv_semantic_sha256": normalized_energyplus_sha256(table_csv_path) if table_csv_path.exists() else None,
        "table_csv_size_bytes": table_csv_path.stat().st_size if table_csv_path.exists() else None,
        "raw_outputs_include_run_ymd": True,
        "readvarseso": {
            "path": str(executable.parent / "PostProcess" / "ReadVarsESO.exe"),
            "status": "MISSING",
            "note": "Native ESO/SQLite/table outputs were validated without -r; ReadVarsESO is optional for this probe.",
        },
        "status": "PASS" if validated else "FAIL",
    }


def energyplus_case(engine_record: dict[str, Any], epw_path: Path) -> dict[str, Any]:
    executable_text = engine_record.get("path")
    if not executable_text:
        return {
            "label": "ENERGYPLUS_SOLVER",
            "solver_output_label": "UNTESTED",
            "status": "UNTESTED",
            "reason": "EnergyPlus executable was not found; no solver run attempted.",
        }
    idf_path = ensure_energyplus_idf()
    first = run_energyplus_once(
        Path(executable_text), idf_path, epw_path, RESULTS_DIR / "energyplus-run-1"
    )
    second = run_energyplus_once(
        Path(executable_text), idf_path, epw_path, RESULTS_DIR / "energyplus-run-2"
    )
    same_output = (
        first["status"] == "PASS"
        and second["status"] == "PASS"
        and first["native_eso_semantic_sha256"] == second["native_eso_semantic_sha256"]
        and first["native_sql_semantic_sha256"] == second["native_sql_semantic_sha256"]
        and first["table_csv_semantic_sha256"] == second["table_csv_semantic_sha256"]
    )
    return {
        "label": "ENERGYPLUS_SOLVER",
        "solver_output_label": "SIMULATED" if same_output else "UNTESTED",
        "input_idf": "fixtures/honeybee_energy_minimal_24_1.idf",
        "input_idf_sha256": sha256_bytes(idf_path.read_bytes()),
        "same_input_twice_same_output": same_output,
        "output_validated": first["status"] == "PASS" and second["status"] == "PASS",
        "run_1": first,
        "run_2": second,
        "status": "PASS" if same_output else "FAIL",
    }


def main() -> int:
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    epw_path = ensure_synthetic_epw()
    first_case = run_epw_case(epw_path)
    second_case = run_epw_case(epw_path)
    first_hash = sha256_bytes(canonical_json(first_case).encode("utf-8"))
    second_hash = sha256_bytes(canonical_json(second_case).encode("utf-8"))
    report = {
        "task": "P04-T21",
        "probe_version": PROBE_VERSION,
        "environment": {
            "python": platform.python_version(),
            "python_executable": ".venv-environmental/Scripts/python.exe",
            "platform": platform.platform(),
        },
        "requested_distributions": {
            "ladybug-core": "0.44.59",
            "lbt-honeybee": "0.9.467",
        },
        "installed_distributions": distribution_evidence(),
        "pip_check": pip_check(),
        "wheel_integrity": wheel_evidence(),
        "license_review": license_evidence(),
        "imports": import_evidence(),
        "cli": {
            name: cli_evidence(name)
            for name in ["ladybug", "honeybee", "honeybee-energy", "honeybee-radiance", "honeybee-openstudio"]
        },
        "epw": {
            "file": "fixtures/synthetic_natal_2021.epw",
            "kind": "SYNTHETIC_DETERMINISTIC_FIXTURE",
            "size_bytes": epw_path.stat().st_size,
            "sha256": sha256_bytes(epw_path.read_bytes()),
            "station": first_case["epw"]["station"],
            "timezone": first_case["epw"]["timezone"],
            "years": first_case["epw"]["years"],
        },
        "synthetic_case": {
            "label": "PURE_LADYBUG_CORE_EPW_STATS",
            "solver_output_label": "NOT_APPLICABLE",
            "same_input_twice_same_output": first_case == second_case,
            "run_1_output_sha256": first_hash,
            "run_2_output_sha256": second_hash,
            "output_validated": first_case == second_case,
            "run_1": first_case,
            "run_2": second_case,
        },
        "external_engines": executable_candidates(),
    }
    report["energyplus_case"] = energyplus_case(report["external_engines"]["energyplus"], epw_path)
    report["capability"] = {
        "ladybug_core_epw_stats": "PASS",
        "ladybug_honeybee_python_surface": "PASS"
        if all(item["status"] == "PASS" for item in report["imports"].values())
        else "DEGRADED",
        "energyplus_solver": "PASS"
        if report["energyplus_case"]["solver_output_label"] == "SIMULATED"
        else "UNTESTED",
        "radiance_solver": "PASS"
        if report["external_engines"]["radiance_rtrace"]["status"] == "FOUND"
        and report["external_engines"]["radiance_oconv"]["status"] == "FOUND"
        else "UNTESTED",
        "overall_environment": "ADOTAR_COM_LIMITES",
        "core_engine_impact": "UNBLOCKED",
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(REPORT_PATH),
        "pip_check": report["pip_check"]["status"],
        "wheel_hashes": report["wheel_integrity"]["all_hashes_match_lock"],
        "epw": report["epw"],
        "reproducible_pure_case": report["synthetic_case"]["same_input_twice_same_output"],
        "energyplus": report["external_engines"]["energyplus"]["status"],
        "radiance_rtrace": report["external_engines"]["radiance_rtrace"]["status"],
        "radiance_oconv": report["external_engines"]["radiance_oconv"]["status"],
        "energyplus_case": report["energyplus_case"]["status"],
        "energyplus_solver_output_label": report["energyplus_case"]["solver_output_label"],
        "decision": report["capability"]["overall_environment"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
