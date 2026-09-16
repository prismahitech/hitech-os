#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

EXPECTED_INPUT_SIZE = 221187
EXPECTED_INPUT_SHA256 = "054be2704261e44c93d548b84eaf56ca7a491a15591d527eb07c0d8577251b8e"
EXPECTED_OUTPUT_SIZE = 225600
EXPECTED_OUTPUT_SHA256 = "ca2eeb60abe76f80d809728e1655f11d21b3a649d0b44a76b6ee4a5cd87a22f1"

M="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
R="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR="http://schemas.openxmlformats.org/package/2006/relationships"
C="http://schemas.openxmlformats.org/drawingml/2006/chart"
A="http://schemas.openxmlformats.org/drawingml/2006/main"
XDR="http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"

for prefix,uri in [("",M),("r",R),("c",C),("a",A),("xdr",XDR)]:
    ET.register_namespace(prefix,uri)
NS={"m":M,"r":R,"c":C,"a":A,"xdr":XDR}
qn=lambda uri,tag:f"{{{uri}}}{tag}"

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def load_entries(path: Path) -> dict[str,bytes]:
    with zipfile.ZipFile(path,"r") as z:
        return {n:z.read(n) for n in z.namelist()}

def write_entries(entries: dict[str,bytes], path: Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(entries.items()):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=3
            info.external_attr=(0o600 & 0xFFFF)<<16
            z.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)

def sheet_paths(entries):
    wb=ET.fromstring(entries["xl/workbook.xml"])
    rel=ET.fromstring(entries["xl/_rels/workbook.xml.rels"])
    mp={x.attrib["Id"]:x.attrib["Target"] for x in rel.findall(qn(PR,"Relationship"))}
    return {s.attrib["name"]:"xl/"+mp[s.attrib[qn(R,"id")]] for s in wb.findall(".//m:sheet",NS)}

def col_num(col):
    n=0
    for ch in col:n=n*26+ord(ch)-64
    return n
def ref_col(ref):return re.match(r"([A-Z]+)",ref).group(1)
def ref_row(ref):return int(re.search(r"(\d+)",ref).group(1))

def find_row(root,r,create=True):
    sd=root.find("m:sheetData",NS)
    for row in sd.findall("m:row",NS):
        rr=int(row.attrib["r"])
        if rr==r:return row
        if rr>r and create:
            new=ET.Element(qn(M,"row"),{"r":str(r)})
            sd.insert(list(sd).index(row),new)
            return new
    return ET.SubElement(sd,qn(M,"row"),{"r":str(r)}) if create else None

def find_cell(root,ref,create=True,style=None):
    row=find_row(root,ref_row(ref),create)
    if row is None:return None
    target=col_num(ref_col(ref))
    for cell in row.findall("m:c",NS):
        n=col_num(ref_col(cell.attrib["r"]))
        if n==target:
            if style is not None:cell.set("s",str(style))
            return cell
        if n>target and create:
            attrs={"r":ref}
            if style is not None:attrs["s"]=str(style)
            new=ET.Element(qn(M,"c"),attrs)
            row.insert(list(row).index(cell),new)
            return new
    if create:
        attrs={"r":ref}
        if style is not None:attrs["s"]=str(style)
        return ET.SubElement(row,qn(M,"c"),attrs)

def clear_cell(c):
    for ch in list(c):
        if ch.tag in (qn(M,"v"),qn(M,"f"),qn(M,"is")):c.remove(ch)
    c.attrib.pop("t",None)

def set_inline(root,ref,text,style):
    c=find_cell(root,ref,True,style)
    clear_cell(c)
    c.set("t","inlineStr")
    isel=ET.SubElement(c,qn(M,"is"))
    ET.SubElement(isel,qn(M,"t")).text=text

def set_row_height(root,r,h):
    row=find_row(root,r,True)
    row.set("ht",str(h));row.set("customHeight","1")

def set_dimension(root,ref):
    d=root.find("m:dimension",NS)
    if d is None:
        d=ET.Element(qn(M,"dimension"),{"ref":ref})
        root.insert(0,d)
    else:d.set("ref",ref)

def add_wrap_style(entries):
    styles=ET.fromstring(entries["xl/styles.xml"])
    xfs=styles.find("m:cellXfs",NS)
    if len(xfs.findall("m:xf",NS))<=35:
        base=copy.deepcopy(xfs.findall("m:xf",NS)[16])
        base.set("applyAlignment","1")
        alg=base.find("m:alignment",NS)
        if alg is None:alg=ET.SubElement(base,qn(M,"alignment"))
        alg.set("wrapText","1");alg.set("vertical","center")
        xfs.append(base)
        xfs.set("count",str(len(xfs.findall("m:xf",NS))))
    entries["xl/styles.xml"]=ET.tostring(styles,encoding="utf-8",xml_declaration=True)

def rewrite_instructions(entries,paths):
    root=ET.fromstring(entries[paths["Instrucciones"]])
    sd=root.find("m:sheetData",NS)
    for row in list(sd.findall("m:row",NS)):
        if int(row.attrib["r"])>=3:sd.remove(row)
    merges=root.find("m:mergeCells",NS)
    if merges is None:
        merges=ET.Element(qn(M,"mergeCells"),{"count":"0"})
        root.append(merges)
    else:
        for mc in list(merges):merges.remove(mc)
    def merge(ref):ET.SubElement(merges,qn(M,"mergeCell"),{"ref":ref})
    def section(r,title):
        merge(f"A{r}:H{r}");set_inline(root,f"A{r}",title,13);set_row_height(root,r,24)
    def card(r,badge,head,body,warning=False):
        merge(f"C{r}:H{r}")
        set_inline(root,f"A{r}",badge,1);set_inline(root,f"B{r}",head,5)
        set_inline(root,f"C{r}",body,14 if warning else 35)
        set_row_height(root,r,38 if len(body)<105 else 50)

    merge("A3:H3");set_inline(root,"A3","GUÍA DE USO · CIOB CRM V3",3);set_row_height(root,3,34)
    merge("A4:H4");set_inline(root,"A4","Base guarda al prospecto. Seguimiento registra lo que pasó. Mi día te dice qué hacer. Dashboard te dice cómo va el negocio.",4);set_row_height(root,4,26)

    section(6,"EMPIEZA AQUÍ · FLUJO DE TRABAJO")
    card(7,"1","ALTA","En Base de contactos captura lo que sabes: Empresa, Nombre, Puesto, teléfono/correo/WhatsApp, Fuente, Prioridad y Responsable.")
    card(8,"2","CONTACTO","Cada llamada, correo, WhatsApp, visita o reunión se registra como una FILA NUEVA en Seguimiento comercial.")
    card(9,"3","RESULTADO","Completa Resultado, Próxima acción, Próximo seguimiento y Estatus posterior. Si cerró, agrega el motivo.")
    card(10,"4","OPERACIÓN","Vuelve a Mi día. La cola se reordena sola por vencimiento, HOT/WARM/COLD, score y valor potencial.")
    card(11,"5","LECTURA","Usa Dashboard para revisar pipeline, temperatura, salud del seguimiento, fuentes y cierres. Ahí no se captura nada.")

    section(13,"DÓNDE CAPTURAR CADA COSA")
    card(14,"B","BASE","Una fila = un prospecto/cliente. Datos relativamente estables: empresa, persona, contacto, perfil, valor potencial, preferencias y responsable.")
    card(15,"S","SEGUIMIENTO","Una fila = una interacción. Es la BITÁCORA y FUENTE DE VERDAD para estatus, último contacto, próxima fecha, próxima acción y cierres.")
    card(16,"M","MI DÍA","No es otra base. Es tu bandeja de trabajo: filtra por responsable y ejecuta la siguiente acción.")
    card(17,"D","DASHBOARD","Sólo lectura ejecutiva. Sirve para detectar embudos atorados, vencidos, concentración y calidad de la operación.")
    card(18,"C","CONFIG","Catálogos y reglas. Tócalos sólo si necesitas cambiar opciones válidas del CRM; no borres encabezados ni nombres de catálogo.",True)
    merge("A19:H19");set_inline(root,"A19","EJEMPLO: si hoy llamas a ACME, no cambies “Último contacto” en Base. Agrega la llamada en Seguimiento; Base se actualiza sola.",14);set_row_height(root,19,38)

    section(21,"RUTINA DIARIA · 3 MINUTOS")
    card(22,"1","ABRE MI DÍA","Elige Responsable. Atiende primero Vencido + HOT, luego Vencido, Hoy y Próximo.")
    card(23,"2","EJECUTA","Usa los accesos rápidos para WhatsApp, correo o web. Si hubo una interacción, regístrala en Seguimiento.")
    card(24,"3","CIERRA EL LOOP","Antes de salir deja Resultado + Próxima acción + Próxima fecha. Así ningún prospecto se cae del radar.")
    card(25,"4","REVISA ALERTAS","Si ves DATOS DE ETAPA, DUPLICADO, SIN FECHA o una alerta roja, corrige la causa, no la celda automática.")
    merge("A26:H26");set_inline(root,"A26","TIP: no inventes fechas para “quitar” alertas. La prioridad funciona mejor con compromisos reales y datos honestos.",14);set_row_height(root,26,34)

    section(28,"QUÉ SE CALCULA SOLO")
    card(29,"✓","AUTOMÁTICO","Estatus, Último contacto, Próximo seguimiento, Próxima acción, Probabilidad, Score, Temperatura y Alertas.")
    card(30,"✓","INTELIGENCIA","Días en etapa, intentos sin respuesta, completitud contextual, pipeline ponderado, sugerencias y controles de coherencia.")
    card(31,"✓","DUPLICADOS","El CRM normaliza correo, teléfono y WhatsApp para detectar coincidencias probables.")
    card(32,"✓","PRIORIDAD","Mi día combina urgencia, temperatura, score y valor. No necesitas ordenar manualmente la Base.")
    merge("A33:H33");set_inline(root,"A33","Las columnas automáticas pueden estar ocultas o agrupadas. Déjalas así: existen para calcular, no para capturar.",16);set_row_height(root,33,32)

    section(35,"REGLAS DE ORO · EVITA ESTOS ERRORES")
    card(36,"!","NO SOBRESCRIBAS","No escribas encima de Estatus, Último contacto, Próximo seguimiento, Próxima acción, Score, Temperatura, Alertas ni Control.",True)
    card(37,"!","NO “ARREGLES” FÓRMULAS","Si algo se ve raro, corrige la actividad o el dato de origen. Las columnas automáticas deben permanecer protegidas.",True)
    card(38,"!","NO DUPLIQUES","Antes de crear otra fila, busca empresa, correo, teléfono y WhatsApp. Si aparece Duplicado, revísalo.",True)
    card(39,"!","NO RECICLES ACTIVIDADES","Cada interacción nueva va en una fila nueva de Seguimiento. No sobrescribas una actividad anterior.",True)
    card(40,"!","CIERRES COHERENTES","Cliente debe terminar con Resultado Ganado. Perdido/No viable debe llevar Motivo de pérdida/cierre.",True)

    section(42,"CÓMO LEER “MI DÍA”")
    rows=[
        ("1","VENCIDO + HOT","Prioridad máxima: oportunidad fuerte y seguimiento atrasado."),
        ("2","VENCIDO","Recupera el compromiso pendiente."),
        ("3","HOY + HOT","Protege la oportunidad antes de que se enfríe."),
        ("4","HOY","Ejecuta el compromiso programado."),
        ("5","PRÓXIMO","Prepara lo que viene en los siguientes días."),
        ("6","SIN FECHA / DATOS","Completa el siguiente paso o la información faltante.")
    ]
    for r,(badge,head,body) in enumerate(rows,start=43):card(r,badge,head,body)

    section(50,"CIERRES, PÉRDIDAS Y OPORTUNIDADES")
    card(51,"G","GANADO","En Seguimiento usa Resultado = Ganado y Estatus posterior = Cliente. Registra valor final si aplica.")
    card(52,"P","PERDIDO","Usa Estatus posterior = Perdido y selecciona Motivo de pérdida/cierre. Eso alimenta el Dashboard.")
    card(53,"N","NO VIABLE","Úsalo cuando el prospecto realmente no encaja. Registra motivo para que el aprendizaje sea útil.")
    card(54,"⏸","EN PAUSA","No lo cierres si aún existe posibilidad. Define una próxima fecha realista para que vuelva a Mi día.")
    merge("A56:H56");set_inline(root,"A56","REGLA FINAL: si dudas dónde escribir algo, casi siempre es en Seguimiento. Base resume; Seguimiento cuenta la historia.",14);set_row_height(root,56,40)

    merges.set("count",str(len(merges.findall("m:mergeCell",NS))))
    old=root.find("m:cols",NS)
    if old is not None:root.remove(old)
    cols=ET.Element(qn(M,"cols"))
    for mn,mx,w in [(1,1,5.5),(2,2,20),(3,8,17.8)]:
        ET.SubElement(cols,qn(M,"col"),{"min":str(mn),"max":str(mx),"width":str(w),"customWidth":"1"})
    root.insert(list(root).index(sd),cols)
    set_dimension(root,"A1:H56")
    entries[paths["Instrucciones"]]=ET.tostring(root,encoding="utf-8",xml_declaration=True)

def remove_children(parent,tags):
    for ch in list(parent):
        if ch.tag in tags:parent.remove(ch)

def add_color(parent,hexv,alpha=None):
    c=ET.SubElement(parent,qn(A,"srgbClr"),{"val":hexv.upper().replace("#","")})
    if alpha is not None:ET.SubElement(c,qn(A,"alpha"),{"val":str(alpha)})

def lighten(hexv,f=.25):
    h=hexv.replace("#","")
    rgb=[int(h[i:i+2],16) for i in (0,2,4)]
    vals=[round(v+(255-v)*f) for v in rgb]
    return "".join(f"{v:02X}" for v in vals)

def set_shape(sppr,fill1,fill2=None,line="D8E2EA",shadow=True,bevel=False):
    remove_children(sppr,{qn(A,"solidFill"),qn(A,"gradFill"),qn(A,"noFill"),qn(A,"ln"),qn(A,"effectLst"),qn(A,"sp3d"),qn(A,"scene3d")})
    if fill2:
        gf=ET.SubElement(sppr,qn(A,"gradFill"),{"rotWithShape":"1"})
        gsl=ET.SubElement(gf,qn(A,"gsLst"))
        for pos,col in [("0",fill1),("100000",fill2)]:
            gs=ET.SubElement(gsl,qn(A,"gs"),{"pos":pos});add_color(gs,col)
        ET.SubElement(gf,qn(A,"lin"),{"ang":"5400000","scaled":"1"})
    else:
        sf=ET.SubElement(sppr,qn(A,"solidFill"));add_color(sf,fill1)
    ln=ET.SubElement(sppr,qn(A,"ln"),{"w":"12700"})
    if line:
        sf=ET.SubElement(ln,qn(A,"solidFill"));add_color(sf,line)
    else:ET.SubElement(ln,qn(A,"noFill"))
    if shadow:
        eff=ET.SubElement(sppr,qn(A,"effectLst"))
        sh=ET.SubElement(eff,qn(A,"outerShdw"),{"blurRad":"50800","dist":"19050","dir":"2700000","algn":"ctr","rotWithShape":"0"})
        add_color(sh,"0B1F33",22000)
    if bevel:
        sp3d=ET.SubElement(sppr,qn(A,"sp3d"),{"extrusionH":"9000","prstMaterial":"warmMatte"})
        ET.SubElement(sp3d,qn(A,"bevelT"),{"w":"42000","h":"22000","prst":"softRound"})

def rich_style(node,size,color,bold):
    for tag in ["a:rPr","a:defRPr","a:endParaRPr"]:
        for rp in node.findall(".//"+tag,NS):
            rp.set("sz",str(size))
            if bold:rp.set("b","1")
            else:rp.attrib.pop("b",None)
            remove_children(rp,{qn(A,"solidFill")})
            sf=ET.SubElement(rp,qn(A,"solidFill"));add_color(sf,color)
            latin=rp.find("a:latin",NS)
            if latin is None:latin=ET.SubElement(rp,qn(A,"latin"))
            latin.set("typeface","Aptos")

def axis_style(ax):
    tx=ax.find("c:txPr",NS)
    if tx is None:
        tx=ET.SubElement(ax,qn(C,"txPr"));ET.SubElement(tx,qn(A,"bodyPr"));ET.SubElement(tx,qn(A,"lstStyle"))
        p=ET.SubElement(tx,qn(A,"p"));ppr=ET.SubElement(p,qn(A,"pPr"));ET.SubElement(ppr,qn(A,"defRPr"));ET.SubElement(p,qn(A,"endParaRPr"),{"lang":"es-MX"})
    rich_style(tx,900,"60727E",False)
    sp=ax.find("c:spPr",NS)
    if sp is None:sp=ET.SubElement(ax,qn(C,"spPr"))
    remove_children(sp,{qn(A,"ln")})
    ln=ET.SubElement(sp,qn(A,"ln"),{"w":"6350"});sf=ET.SubElement(ln,qn(A,"solidFill"));add_color(sf,"C7D2DB")

def gridlines(ax):
    mg=ax.find("c:majorGridlines",NS)
    if mg is None:
        mg=ET.Element(qn(C,"majorGridlines"))
        ap=ax.find("c:axPos",NS)
        ax.insert(list(ax).index(ap)+1 if ap is not None else len(ax),mg)
    sp=mg.find("c:spPr",NS)
    if sp is None:sp=ET.SubElement(mg,qn(C,"spPr"))
    remove_children(sp,{qn(A,"ln")})
    ln=ET.SubElement(sp,qn(A,"ln"),{"w":"6350"});sf=ET.SubElement(ln,qn(A,"solidFill"));add_color(sf,"E8EEF3")

def points(ser,colors):
    for d in list(ser.findall("c:dPt",NS)):ser.remove(d)
    sp=ser.find("c:spPr",NS)
    idx=list(ser).index(sp)+1 if sp is not None else 3
    for i,col in enumerate(colors):
        d=ET.Element(qn(C,"dPt"));ET.SubElement(d,qn(C,"idx"),{"val":str(i)})
        dsp=ET.SubElement(d,qn(C,"spPr"));set_shape(dsp,col,lighten(col,.28),None,False,True)
        ser.insert(idx+i,d)

def style_chart(entries,name,kind):
    root=ET.fromstring(entries[name])
    rc=root.find("c:roundedCorners",NS)
    if rc is None:
        rc=ET.Element(qn(C,"roundedCorners"),{"val":"1"})
        lang=root.find("c:lang",NS);root.insert(list(root).index(lang)+1 if lang is not None else 0,rc)
    st=root.find("c:style",NS)
    if st is not None:st.set("val","13")
    chart=root.find("c:chart",NS);title=chart.find("c:title",NS)
    if title is not None:rich_style(title,1500,"0B1F33",True)
    csp=root.find("c:spPr",NS)
    if csp is None:
        csp=ET.Element(qn(C,"spPr"));ps=root.find("c:printSettings",NS);root.insert(list(root).index(ps) if ps is not None else len(root),csp)
    set_shape(csp,"FFFFFF",None,"D8E2EA",True,False)
    plot=chart.find("c:plotArea",NS);psp=plot.find("c:spPr",NS)
    if psp is None:psp=ET.SubElement(plot,qn(C,"spPr"))
    set_shape(psp,"FBFCFD",None,None,False,False)
    for ax in plot.findall("c:catAx",NS)+plot.findall("c:valAx",NS):axis_style(ax)
    for ax in plot.findall("c:valAx",NS):gridlines(ax)

    if kind=="doughnut":
        ch=plot.find("c:doughnutChart",NS);ser=ch.find("c:ser",NS)
        hs=ch.find("c:holeSize",NS)
        if hs is None:hs=ET.SubElement(ch,qn(C,"holeSize"))
        hs.set("val","64")
        fa=ch.find("c:firstSliceAng",NS)
        if fa is None:fa=ET.SubElement(ch,qn(C,"firstSliceAng"))
        fa.set("val","270")
        sp=ser.find("c:spPr",NS)
        if sp is None:sp=ET.SubElement(ser,qn(C,"spPr"))
        set_shape(sp,"173A5E","4E86B5",None,True,True)
        points(ser,["C44747","C8A24A","3C78A8"])
        leg=chart.find("c:legend",NS)
        if leg is not None and leg.find("c:txPr",NS) is not None:rich_style(leg.find("c:txPr",NS),950,"4E5D68",False)
    else:
        ch=plot.find("c:barChart",NS);ser=ch.find("c:ser",NS)
        gap=ch.find("c:gapWidth",NS)
        if gap is None:gap=ET.SubElement(ch,qn(C,"gapWidth"))
        gap.set("val","50" if kind=="funnel" else "58")
        sp=ser.find("c:spPr",NS)
        if sp is None:sp=ET.SubElement(ser,qn(C,"spPr"))
        pal={"funnel":("173A5E","4E86B5"),"health":("60727E","A4B0B8"),"sources":("173A5E","79A8CC"),"loss":("A75A50","E2A45B")}
        set_shape(sp,*pal[kind],None,True,True)
        if kind=="funnel":points(ser,["6F8FAF","4E86B5","3C78A8","2E7D7A","2E7D60","C8A24A","D39B3B","2E7D60","8897A5","9D6B53","C44747"])
        elif kind=="health":points(ser,["C44747","D38D3C","C8A24A","8897A5","2E7D60","2E7D60","173A5E"])
    entries[name]=ET.tostring(root,encoding="utf-8",xml_declaration=True)

def polish(inp: Path, out: Path):
    if inp.stat().st_size!=EXPECTED_INPUT_SIZE or sha256(inp)!=EXPECTED_INPUT_SHA256:
        raise SystemExit(f"INPUT_IDENTITY_MISMATCH size={inp.stat().st_size} sha256={sha256(inp)}")
    entries=load_entries(inp)
    paths=sheet_paths(entries)
    add_wrap_style(entries)
    rewrite_instructions(entries,paths)
    for name,kind in [
        ("xl/charts/chart1.xml","funnel"),
        ("xl/charts/chart2.xml","doughnut"),
        ("xl/charts/chart3.xml","health"),
        ("xl/charts/chart4.xml","sources"),
        ("xl/charts/chart5.xml","loss"),
    ]:
        style_chart(entries,name,kind)
    write_entries(entries,out)
    if out.stat().st_size!=EXPECTED_OUTPUT_SIZE or sha256(out)!=EXPECTED_OUTPUT_SHA256:
        raise SystemExit(f"OUTPUT_IDENTITY_MISMATCH size={out.stat().st_size} sha256={sha256(out)}")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input",type=Path)
    ap.add_argument("output",type=Path)
    args=ap.parse_args()
    polish(args.input,args.output)
    print(f"PASS {args.output} {args.output.stat().st_size} {sha256(args.output)}")
if __name__=="__main__":
    main()