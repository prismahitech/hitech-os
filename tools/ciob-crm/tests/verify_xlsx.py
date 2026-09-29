#!/usr/bin/env python3
"""Structural verifier for CIOB CRM XLSX.

Uses only Python stdlib. It does not calculate Excel formulas; it verifies
the OOXML package, required workbook structures and obvious broken refs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}

REQUIRED_SHEETS = {
    "Mi día",
    "Dashboard",
    "Base de contactos",
    "Seguimiento comercial",
    "Configuración",
    "Instrucciones",
}
ERROR_PATTERNS = ("#REF!", "#VALUE!", "#NAME?", "#DIV/0!")


def verify(path: Path) -> dict:
    result = {
        "file": str(path),
        "exists": path.exists(),
        "zipOk": False,
        "xmlOk": False,
        "requiredSheets": False,
        "sheetNames": [],
        "tables": 0,
        "charts": 0,
        "dataValidations": 0,
        "formulaCount": 0,
        "brokenRefFormulaCount": 0,
        "definedNames": 0,
        "errors": [],
    }
    if not path.exists():
        result["errors"].append("FILE_NOT_FOUND")
        return result

    try:
        with zipfile.ZipFile(path) as zf:
            result["zipOk"] = zf.testzip() is None
            names = set(zf.namelist())

            for name in names:
                if name.endswith(".xml"):
                    ET.fromstring(zf.read(name))
            result["xmlOk"] = True

            wb = ET.fromstring(zf.read("xl/workbook.xml"))
            result["sheetNames"] = [
                s.attrib.get("name", "")
                for s in wb.findall(".//m:sheet", NS)
            ]
            result["requiredSheets"] = REQUIRED_SHEETS.issubset(result["sheetNames"])
            result["definedNames"] = len(wb.findall(".//m:definedName", NS))

            result["tables"] = sum(
                1 for n in names if re.fullmatch(r"xl/tables/table\d+\.xml", n)
            )
            result["charts"] = sum(
                1 for n in names if re.fullmatch(r"xl/charts/chart\d+\.xml", n)
            )

            for name in names:
                if not re.fullmatch(r"xl/worksheets/sheet\d+\.xml", name):
                    continue
                root = ET.fromstring(zf.read(name))
                result["dataValidations"] += len(root.findall(".//m:dataValidation", NS))
                for f in root.findall(".//m:f", NS):
                    result["formulaCount"] += 1
                    formula = f.text or ""
                    if any(err in formula for err in ERROR_PATTERNS):
                        result["brokenRefFormulaCount"] += 1

    except Exception as exc:
        result["errors"].append(f"{type(exc).__name__}: {exc}")

    result["pass"] = all(
        [
            result["zipOk"],
            result["xmlOk"],
            result["requiredSheets"],
            result["tables"] >= 2,
            result["dataValidations"] >= 10,
            result["formulaCount"] > 0,
            result["brokenRefFormulaCount"] == 0,
            not result["errors"],
        ]
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("xlsx", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = verify(args.xlsx)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("PASS" if result.get("pass") else "FAIL")
        for key, value in result.items():
            if key not in {"pass", "errors"}:
                print(f"{key}: {value}")
        for err in result["errors"]:
            print(f"ERROR: {err}", file=sys.stderr)
    return 0 if result.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
