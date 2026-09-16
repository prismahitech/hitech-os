#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

M="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
C="http://schemas.openxmlformats.org/drawingml/2006/chart"
A="http://schemas.openxmlformats.org/drawingml/2006/main"
NS={"m":M,"c":C,"a":A}
EXPECTED_SIZE=225600
EXPECTED_SHA256="ca2eeb60abe76f80d809728e1655f11d21b3a649d0b44a76b6ee4a5cd87a22f1"
SECTIONS={
    "EMPIEZA AQUÍ · FLUJO DE TRABAJO","DÓNDE CAPTURAR CADA COSA","RUTINA DIARIA · 3 MINUTOS",
    "QUÉ SE CALCULA SOLO","REGLAS DE ORO · EVITA ESTOS ERRORES","CÓMO LEER “MI DÍA”",
    "CIERRES, PÉRDIDAS Y OPORTUNIDADES"
}
BAD=("#REF!","#VALUE!","#NAME?","#DIV/0!")

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument("xlsx",type=Path);a=ap.parse_args()
    p=a.xlsx;checks={};errors=[]
    checks["identity"]=p.exists() and p.stat().st_size==EXPECTED_SIZE and sha256(p)==EXPECTED_SHA256
    with zipfile.ZipFile(p) as z:
        checks["zipOk"]=z.testzip() is None
        xmlok=True
        for n in z.namelist():
            if n.endswith(".xml"):
                try:ET.fromstring(z.read(n))
                except Exception as e:xmlok=False;errors.append(f"XML:{n}:{e}")
        checks["xmlOk"]=xmlok
        wb=ET.fromstring(z.read("xl/workbook.xml"))
        checks["sixSheets"]=len(wb.findall(".//m:sheet",NS))==6
        formulas=[]
        for n in z.namelist():
            if re.fullmatch(r"xl/worksheets/sheet\d+\.xml",n):
                root=ET.fromstring(z.read(n))
                formulas += [f.text or "" for f in root.findall(".//m:f",NS)]
        checks["noBrokenFormulaTokens"]=not any(any(b in f for b in BAD) for f in formulas)

        inst=ET.fromstring(z.read("xl/worksheets/sheet6.xml"))
        texts=set()
        for c in inst.findall(".//m:c",NS):
            if c.attrib.get("t")=="inlineStr":
                txt="".join(t.text or "" for t in c.findall(".//m:t",NS))
                if txt:texts.add(txt)
        checks["guideSections"]=SECTIONS.issubset(texts)
        checks["guideExpanded"]=inst.find("m:dimension",NS).attrib.get("ref")=="A1:H56"

        charts=[]
        for i in range(1,6):
            root=ET.fromstring(z.read(f"xl/charts/chart{i}.xml"))
            charts.append({
                "rounded":root.find("c:roundedCorners",NS) is not None and root.find("c:roundedCorners",NS).attrib.get("val")=="1",
                "gradient":len(root.findall(".//a:gradFill",NS))>=1,
                "shadow":len(root.findall(".//a:outerShdw",NS))>=1,
                "bevel":len(root.findall(".//a:bevelT",NS))>=1,
                "style":root.find("c:style",NS) is not None and root.find("c:style",NS).attrib.get("val")=="13",
            })
        checks["premiumCharts"]=all(all(x.values()) for x in charts)
        checks["chartCount"]=sum(1 for n in z.namelist() if re.fullmatch(r"xl/charts/chart\d+\.xml",n))==5
    passed=all(checks.values()) and not errors
    print(json.dumps({"pass":passed,"checks":checks,"errors":errors,"size":p.stat().st_size,"sha256":sha256(p)},ensure_ascii=False,indent=2))
    return 0 if passed else 1
if __name__=="__main__":raise SystemExit(main())