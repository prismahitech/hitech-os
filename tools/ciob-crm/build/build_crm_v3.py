#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import shutil
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET

EXPECTED_SIZE = 159678
EXPECTED_SHA = 'e8eb06bcf05b88500c4733a9b54b11f355ce3a7c51773b062fefafab86b27bf9'

M = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG_R = 'http://schemas.openxmlformats.org/package/2006/relationships'
C = 'http://schemas.openxmlformats.org/drawingml/2006/chart'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
XDR = 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'

for prefix, uri in [('', M), ('r', R), ('c', C), ('a', A), ('xdr', XDR)]:
    ET.register_namespace(prefix, uri)

NS = {'m': M, 'r': R, 'c': C, 'a': A, 'xdr': XDR}
qn = lambda uri, tag: f'{{{uri}}}{tag}'


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def col_num(col: str) -> int:
    n = 0
    for c in col:
        n = n * 26 + ord(c.upper()) - 64
    return n


def num_col(n: int) -> str:
    out = ''
    while n:
        n, rem = divmod(n - 1, 26)
        out = chr(65 + rem) + out
    return out


def ref_col(ref: str) -> str:
    return re.match(r'([A-Z]+)', ref).group(1)


def ref_row(ref: str) -> int:
    return int(re.search(r'(\d+)', ref).group(1))


def excel_serial(d: date) -> int:
    return (d - date(1899, 12, 30)).days


def xml_bytes(root: ET.Element) -> bytes:
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def find_row(root: ET.Element, r: int, create=True) -> ET.Element | None:
    sheet_data = root.find('m:sheetData', NS)
    for row in sheet_data.findall('m:row', NS):
        rr = int(row.attrib['r'])
        if rr == r:
            return row
        if rr > r and create:
            new = ET.Element(qn(M, 'row'), {'r': str(r)})
            idx = list(sheet_data).index(row)
            sheet_data.insert(idx, new)
            return new
    if create:
        new = ET.SubElement(sheet_data, qn(M, 'row'), {'r': str(r)})
        return new
    return None


def find_cell(root: ET.Element, ref: str, create=True, style: int | None = None) -> ET.Element | None:
    r = ref_row(ref)
    row = find_row(root, r, create=create)
    if row is None:
        return None
    target_n = col_num(ref_col(ref))
    for c in row.findall('m:c', NS):
        n = col_num(ref_col(c.attrib['r']))
        if n == target_n:
            if style is not None:
                c.set('s', str(style))
            return c
        if n > target_n and create:
            attrs = {'r': ref}
            if style is not None:
                attrs['s'] = str(style)
            new = ET.Element(qn(M, 'c'), attrs)
            row.insert(list(row).index(c), new)
            return new
    if create:
        attrs = {'r': ref}
        if style is not None:
            attrs['s'] = str(style)
        return ET.SubElement(row, qn(M, 'c'), attrs)
    return None


def clear_cell_contents(c: ET.Element):
    for child in list(c):
        if child.tag in (qn(M, 'v'), qn(M, 'f'), qn(M, 'is')):
            c.remove(child)
    c.attrib.pop('t', None)


def set_inline(root: ET.Element, ref: str, text: str, style: int | None = None):
    c = find_cell(root, ref, True, style)
    clear_cell_contents(c)
    c.set('t', 'inlineStr')
    isel = ET.SubElement(c, qn(M, 'is'))
    t = ET.SubElement(isel, qn(M, 't'))
    if text.startswith(' ') or text.endswith(' '):
        t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    t.text = text


def set_number(root: ET.Element, ref: str, value: float | int | None, style: int | None = None):
    c = find_cell(root, ref, True, style)
    clear_cell_contents(c)
    if value is not None:
        v = ET.SubElement(c, qn(M, 'v'))
        v.text = str(value)


def set_formula(root: ET.Element, ref: str, formula: str, style: int | None = None, cached=None):
    c = find_cell(root, ref, True, style)
    clear_cell_contents(c)
    f = ET.SubElement(c, qn(M, 'f'))
    f.text = formula
    if cached is not None:
        if isinstance(cached, str):
            c.set('t', 'str')
        v = ET.SubElement(c, qn(M, 'v'))
        v.text = str(cached)


def clear_formula_cache(c: ET.Element):
    """Keep the formula but remove stale cached display values."""
    v = c.find('m:v', NS)
    if v is not None:
        c.remove(v)
    if c.attrib.get('t') == 'str':
        c.attrib.pop('t', None)


def set_row_height(root: ET.Element, start: int, end: int, height: float):
    for r in range(start, end + 1):
        row = find_row(root, r, True)
        row.set('ht', str(height))
        row.set('customHeight', '1')


def set_dimension(root: ET.Element, ref: str):
    dim = root.find('m:dimension', NS)
    if dim is None:
        dim = ET.Element(qn(M, 'dimension'), {'ref': ref})
        root.insert(0, dim)
    else:
        dim.set('ref', ref)


def merge_expand(root: ET.Element, old: str, new: str):
    for mc in root.findall('.//m:mergeCells/m:mergeCell', NS):
        if mc.attrib.get('ref') == old:
            mc.set('ref', new)


def get_shared_strings(entries: dict[str, bytes]) -> list[str]:
    out = []
    root = ET.fromstring(entries['xl/sharedStrings.xml'])
    for si in root.findall('m:si', NS):
        out.append(''.join((t.text or '') for t in si.findall('.//m:t', NS)))
    return out


def cell_text(root: ET.Element, ref: str, sst: list[str]):
    c = root.find(f".//m:c[@r='{ref}']", NS)
    if c is None:
        return ''
    t = c.attrib.get('t')
    v = c.find('m:v', NS)
    if t == 'inlineStr':
        return ''.join((x.text or '') for x in c.findall('.//m:t', NS))
    if v is None or v.text is None:
        return ''
    if t == 's':
        return sst[int(v.text)]
    return v.text


def workbook_sheet_paths(entries: dict[str, bytes]) -> dict[str, str]:
    wb = ET.fromstring(entries['xl/workbook.xml'])
    rels = ET.fromstring(entries['xl/_rels/workbook.xml.rels'])
    id_target = {r.attrib['Id']: r.attrib['Target'] for r in rels.findall(qn(PKG_R, 'Relationship'))}
    out = {}
    for s in wb.findall('.//m:sheet', NS):
        out[s.attrib['name']] = 'xl/' + id_target[s.attrib[qn(R, 'id')]]
    return out


def load_entries(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path, 'r') as z:
        return {n: z.read(n) for n in z.namelist()}


def write_entries(entries: dict[str, bytes], path: Path):
    """Write a byte-deterministic OOXML ZIP.

    XLSX identity should reflect workbook content, not wall-clock ZIP metadata.
    Sorting parts and pinning ZipInfo timestamps makes repeated V3 builds stable.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (0o600 & 0xFFFF) << 16
            z.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def insert_before_first(root: ET.Element, elem: ET.Element, candidate_tags: list[str]):
    tags = [qn(M, x) for x in candidate_tags]
    for idx, child in enumerate(list(root)):
        if child.tag in tags:
            root.insert(idx, elem)
            return
    root.append(elem)


def ensure_data_validations(root: ET.Element) -> ET.Element:
    dvs = root.find('m:dataValidations', NS)
    if dvs is None:
        dvs = ET.Element(qn(M, 'dataValidations'), {'count': '0'})
        insert_before_first(root, dvs, ['hyperlinks', 'printOptions', 'pageMargins', 'pageSetup', 'headerFooter', 'drawing'])
    return dvs


def add_dv(root: ET.Element, sqref: str, dv_type: str, formula1: str, *, operator=None,
           formula2=None, allow_blank=True, error_style='warning', title='CIOB CRM V3',
           error='Revisa este dato. La regla es preventiva y no reemplaza el criterio comercial.'):
    dvs = ensure_data_validations(root)
    attrs = {
        'type': dv_type,
        'sqref': sqref,
        'allowBlank': '1' if allow_blank else '0',
        'showErrorMessage': '1',
        'showInputMessage': '1',
        'errorStyle': error_style,
        'errorTitle': title,
        'error': error,
    }
    if operator:
        attrs['operator'] = operator
    dv = ET.SubElement(dvs, qn(M, 'dataValidation'), attrs)
    f1 = ET.SubElement(dv, qn(M, 'formula1')); f1.text = formula1
    if formula2 is not None:
        f2 = ET.SubElement(dv, qn(M, 'formula2')); f2.text = formula2
    dvs.set('count', str(len(dvs.findall('m:dataValidation', NS))))


def ensure_sheet_protection(root: ET.Element):
    old = root.find('m:sheetProtection', NS)
    if old is not None:
        root.remove(old)
    prot = ET.Element(qn(M, 'sheetProtection'), {
        'sheet': '1', 'objects': '1', 'scenarios': '1',
        'sort': '0', 'autoFilter': '0',
        'selectLockedCells': '0', 'selectUnlockedCells': '0'
    })
    insert_before_first(root, prot, ['protectedRanges', 'scenarios', 'autoFilter', 'sortState', 'mergeCells', 'conditionalFormatting', 'dataValidations', 'hyperlinks', 'printOptions', 'pageMargins', 'drawing'])


def add_conditional_contains(root: ET.Element, sqref: str, text: str, dxf_id: int, priority: int):
    cf = ET.SubElement(root, qn(M, 'conditionalFormatting'), {'sqref': sqref})
    rule = ET.SubElement(cf, qn(M, 'cfRule'), {
        'type': 'containsText', 'dxfId': str(dxf_id), 'priority': str(priority),
        'operator': 'containsText', 'text': text
    })
    f = ET.SubElement(rule, qn(M, 'formula'))
    first = sqref.split(':')[0]
    f.text = f'NOT(ISERROR(SEARCH("{text}",{first})))'
    # move before dataValidations/hyperlinks/etc
    root.remove(cf)
    insert_before_first(root, cf, ['dataValidations', 'hyperlinks', 'printOptions', 'pageMargins', 'drawing'])


def add_or_replace_defined_name(wb: ET.Element, name: str, formula: str):
    dns = wb.find('m:definedNames', NS)
    if dns is None:
        dns = ET.SubElement(wb, qn(M, 'definedNames'))
    for d in dns.findall('m:definedName', NS):
        if d.attrib.get('name') == name:
            d.text = formula
            return
    d = ET.SubElement(dns, qn(M, 'definedName'), {'name': name}); d.text = formula


def add_unlocked_style_variants(styles_root: ET.Element, base_ids: list[int]) -> dict[int, int]:
    cellxfs = styles_root.find('m:cellXfs', NS)
    xfs = cellxfs.findall('m:xf', NS)
    result = {}
    for base in base_ids:
        xf = copy.deepcopy(xfs[base])
        xf.set('applyProtection', '1')
        prot = xf.find('m:protection', NS)
        if prot is None:
            prot = ET.SubElement(xf, qn(M, 'protection'))
        prot.set('locked', '0')
        cellxfs.append(xf)
        result[base] = len(cellxfs.findall('m:xf', NS)) - 1
    cellxfs.set('count', str(len(cellxfs.findall('m:xf', NS))))
    return result


def set_style_range(root: ET.Element, col: str, r1: int, r2: int, style: int):
    for r in range(r1, r2 + 1):
        c = find_cell(root, f'{col}{r}', True)
        c.set('s', str(style))


def rebuild_cols(root: ET.Element, specs: list[dict]):
    old = root.find('m:cols', NS)
    if old is not None:
        root.remove(old)
    cols = ET.Element(qn(M, 'cols'))
    for spec in specs:
        attrs = {k: str(v) for k, v in spec.items() if v is not None}
        ET.SubElement(cols, qn(M, 'col'), attrs)
    # cols should be before sheetData
    sd = root.find('m:sheetData', NS)
    root.insert(list(root).index(sd), cols)


def base_col_specs():
    # visible nucleus: ID, Empresa, Contacto, Cargo, Tel, Correo, Temp, Prioridad, Estatus,
    # Próx fecha, Acción V3, Score, Valor, Responsable, Alerta. Others remain grouped/collapsed.
    widths = {
        'A':13,'B':25,'C':23,'D':24,'E':16,'F':17,'G':17,'H':28,'I':22,'J':20,'K':16,'L':18,'M':19,'N':22,
        'O':16,'P':22,'Q':23,'R':25,'S':13,'T':17,'U':18,'V':15,'W':16,'X':25,'Y':17,'Z':13,'AA':10,'AB':14,
        'AC':13,'AD':15,'AE':28,'AF':11,'AG':13,'AH':15,'AI':18,'AJ':28,'AK':16,'AL':16,'AM':24,'AN':13,'AO':14,
        'AP':18,'AQ':17,'AR':16,'AS':30,'AT':26,'AU':18,'AV':18,'AW':18,'AX':14,
    }
    visible = set('A B C D F H S T U W Y AA AC AF AS'.split())
    specs=[]
    for n in range(1,col_num('AX')+1):
        c=num_col(n)
        hidden = c not in visible
        attrs={'min':n,'max':n,'width':widths.get(c,14),'customWidth':1}
        if hidden:
            attrs['hidden']=1
            attrs['outlineLevel']=1
        specs.append(attrs)
    return specs


def add_table_columns(table_root: ET.Element, cols: list[tuple[str, int, str | None]]):
    tcols = table_root.find('m:tableColumns', NS)
    maxid = max(int(x.attrib['id']) for x in tcols.findall('m:tableColumn', NS))
    for name, dxf, formula in cols:
        maxid += 1
        tc = ET.SubElement(tcols, qn(M, 'tableColumn'), {'id': str(maxid), 'name': name, 'dataDxfId': str(dxf)})
        if formula:
            f = ET.SubElement(tc, qn(M, 'calculatedColumnFormula')); f.text = formula
    tcols.set('count', str(len(tcols.findall('m:tableColumn', NS))))


def set_table_formula(table_root: ET.Element, col_name: str, formula: str):
    for tc in table_root.findall('.//m:tableColumn', NS):
        if tc.attrib.get('name') == col_name:
            f = tc.find('m:calculatedColumnFormula', NS)
            if f is None:
                f = ET.SubElement(tc, qn(M, 'calculatedColumnFormula'))
            f.text = formula
            return
    raise KeyError(col_name)


def add_hyperlink_location(root: ET.Element, ref: str, location: str, display: str):
    hs = root.find('m:hyperlinks', NS)
    if hs is None:
        hs = ET.Element(qn(M, 'hyperlinks'))
        insert_before_first(root, hs, ['printOptions','pageMargins','pageSetup','headerFooter','drawing'])
    # replace if exists
    for h in hs.findall('m:hyperlink', NS):
        if h.attrib.get('ref') == ref:
            h.set('location', location); h.set('display', display); return
    ET.SubElement(hs, qn(M, 'hyperlink'), {'ref':ref,'location':location,'display':display})


def baseline_rows(entries: dict[str, bytes]):
    sst = get_shared_strings(entries)
    paths = workbook_sheet_paths(entries)
    root = ET.fromstring(entries[paths['Base de contactos']])
    rows=[]
    headers=[cell_text(root,f'{num_col(i)}6',sst) for i in range(1,col_num('AJ')+1)]
    for r in range(7,507):
        empresa=cell_text(root,f'B{r}',sst)
        if empresa:
            rec={headers[i-1]:cell_text(root,f'{num_col(i)}{r}',sst) for i in range(1,len(headers)+1)}
            rec['_row']=r
            rows.append(rec)
    return rows


def normal_email(s: str) -> str:
    return re.sub(r'\s+','',s or '').lower()


def normal_phone(s: str) -> str:
    return re.sub(r'[\s\-\(\)\+\./]','', (s or '').lower())


def stage_completeness(rec: dict) -> float:
    def yes(x): return bool(str(x or '').strip())
    contact=yes(rec.get('Teléfono')) or yes(rec.get('WhatsApp')) or yes(rec.get('Correo'))
    need=yes(rec.get('Necesidad principal')) and rec.get('Necesidad principal')!='Por definir'
    service=yes(rec.get('Servicio CIOB potencial')) and rec.get('Servicio CIOB potencial')!='Por definir'
    base=[yes(rec.get('Empresa')), yes(rec.get('Nombre')), contact, yes(rec.get('Responsable'))]
    st=rec.get('Estatus') or ('Por contactar' if contact else 'Por investigar')
    if st=='Por investigar': vals=base
    elif st=='Por contactar': vals=base+[yes(rec.get('Fuente'))]
    elif st=='Contactado': vals=base+[yes(rec.get('Fuente')),need]
    elif st in ('Reunión agendada','Diagnóstico'): vals=base+[need,service, bool(rec.get('Próximo seguimiento') or rec.get('Próxima acción'))]
    elif st in ('Propuesta enviada','Negociación'): vals=base+[need,service, float(rec.get('Valor potencial MXN') or 0)>0, bool(rec.get('Próximo seguimiento') or rec.get('Próxima acción'))]
    elif st=='En pausa': vals=base+[bool(rec.get('Próximo seguimiento') or rec.get('Próxima acción'))]
    else: vals=base+[service]
    return sum(vals)/len(vals) if vals else 0.0


def control_v3(rec: dict, motive='', ctxt=0.0) -> str:
    email=rec.get('Correo') or ''; tel=rec.get('Teléfono') or ''; wa=rec.get('WhatsApp') or ''; web=rec.get('Página web') or ''
    if email and (('@' not in email) or ('.' not in email.split('@')[-1])): return 'REVISAR CORREO'
    if tel and len(normal_phone(tel)) < 8: return 'REVISAR TELÉFONO'
    if wa and len(normal_phone(wa)) < 8: return 'REVISAR WHATSAPP'
    if web and '.' not in web: return 'REVISAR WEB'
    st=rec.get('Estatus') or ''
    if st=='Negociación' and not float(rec.get('Valor potencial MXN') or 0): return 'VALOR EN NEGOCIACIÓN'
    if st=='Propuesta enviada' and (not rec.get('Servicio CIOB potencial') or rec.get('Servicio CIOB potencial')=='Por definir'): return 'SERVICIO EN PROPUESTA'
    if st not in ('Cliente','Perdido','No viable') and not (rec.get('Próximo seguimiento') or rec.get('Próxima acción')): return 'SIGUIENTE PASO'
    if st in ('Perdido','No viable') and not motive: return 'MOTIVO DE CIERRE'
    if ctxt < 0.7: return 'DATOS DE ETAPA'
    return 'OK'


def bucket(alert,temp,control,dup):
    if alert=='VENCIDO' and temp=='HOT': return 1
    if alert=='VENCIDO': return 2
    if alert=='HOY' and temp=='HOT': return 3
    if alert=='HOY': return 4
    if alert=='PRÓXIMO': return 5
    if alert=='SIN FECHA' and temp=='HOT': return 6
    if alert=='SIN FECHA' and temp=='WARM': return 7
    if control!='OK': return 8
    if dup=='REVISAR': return 9
    return 10


def formula_base():
    # worksheet structured-ref formulas
    norm_email='IF([@Empresa]="","",LOWER(TRIM(SUBSTITUTE([@Correo]," ",""))))'
    norm_tel='IF([@Empresa]="","",LOWER(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(TRIM([@Teléfono])," ",""),"-",""),"(",""),")",""),"+",""),".",""),"/","")))'
    norm_wa='IF([@Empresa]="","",LOWER(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(TRIM([@WhatsApp])," ",""),"-",""),"(",""),")",""),"+",""),".",""),"/","")))'
    motive='IF([@Empresa]="","",IFERROR(LOOKUP(2,1/((tblSeguimiento[ID prospecto]=[@ID])*(tblSeguimiento[Motivo de pérdida/cierre]<>"")),tblSeguimiento[Motivo de pérdida/cierre]),""))'
    days_stage='IF([@Empresa]="","",IFERROR(TODAY()-LOOKUP(2,1/((tblSeguimiento[ID prospecto]=[@ID])*(tblSeguimiento[Cambio etapa?]=1)*(tblSeguimiento[Estatus posterior]=[@Estatus])*(tblSeguimiento[Fecha]<>"")),tblSeguimiento[Fecha]),IF([@[Último contacto]]="","",TODAY()-[@[Último contacto]])))'
    attempts='IF([@Empresa]="","",SUMPRODUCT((tblSeguimiento[ID prospecto]=[@ID])*(tblSeguimiento[Resultado]="Sin respuesta")*(ROW(tblSeguimiento[Resultado])>IFERROR(LOOKUP(2,1/((tblSeguimiento[ID prospecto]=[@ID])*(tblSeguimiento[Resultado]<>"")*(tblSeguimiento[Resultado]<>"Sin respuesta")),ROW(tblSeguimiento[Resultado])),0))))'
    ctxt='IF([@Empresa]="","",IF([@Estatus]="Por investigar",(--([@Empresa]<>"")+--([@Nombre]<>"")+--(OR([@Teléfono]<>"",[@WhatsApp]<>"",[@Correo]<>""))+--([@Responsable]<>""))/4,IF([@Estatus]="Por contactar",(--([@Empresa]<>"")+--([@Nombre]<>"")+--(OR([@Teléfono]<>"",[@WhatsApp]<>"",[@Correo]<>""))+--([@Responsable]<>"")+--([@Fuente]<>""))/5,IF([@Estatus]="Contactado",(--([@Empresa]<>"")+--([@Nombre]<>"")+--(OR([@Teléfono]<>"",[@WhatsApp]<>"",[@Correo]<>""))+--([@Responsable]<>"")+--([@Fuente]<>"")+--(AND([@[Necesidad principal]]<>"",[@[Necesidad principal]]<>"Por definir")))/6,IF(OR([@Estatus]="Reunión agendada",[@Estatus]="Diagnóstico"),(--([@Empresa]<>"")+--([@Nombre]<>"")+--(OR([@Teléfono]<>"",[@WhatsApp]<>"",[@Correo]<>""))+--([@Responsable]<>"")+--(AND([@[Necesidad principal]]<>"",[@[Necesidad principal]]<>"Por definir"))+--(AND([@[Servicio CIOB potencial]]<>"",[@[Servicio CIOB potencial]]<>"Por definir"))+--(OR([@[Próximo seguimiento]]<>"",[@[Próxima acción]]<>"")))/7,IF(OR([@Estatus]="Propuesta enviada",[@Estatus]="Negociación"),(--([@Empresa]<>"")+--([@Nombre]<>"")+--(OR([@Teléfono]<>"",[@WhatsApp]<>"",[@Correo]<>""))+--([@Responsable]<>"")+--(AND([@[Necesidad principal]]<>"",[@[Necesidad principal]]<>"Por definir"))+--(AND([@[Servicio CIOB potencial]]<>"",[@[Servicio CIOB potencial]]<>"Por definir"))+--([@[Valor potencial MXN]]>0)+--(OR([@[Próximo seguimiento]]<>"",[@[Próxima acción]]<>"")))/8,IF([@Estatus]="En pausa",(--([@Empresa]<>"")+--([@Nombre]<>"")+--(OR([@Teléfono]<>"",[@WhatsApp]<>"",[@Correo]<>""))+--([@Responsable]<>"")+--(OR([@[Próximo seguimiento]]<>"",[@[Próxima acción]]<>"")))/5,(--([@Empresa]<>"")+--([@Nombre]<>"")+--(OR([@Teléfono]<>"",[@WhatsApp]<>"",[@Correo]<>""))+--([@Responsable]<>"")+--(AND([@[Servicio CIOB potencial]]<>"",[@[Servicio CIOB potencial]]<>"Por definir")))/5)))))))'
    suggested_date='IF([@Empresa]="","",IF(OR([@Estatus]="Cliente",[@Estatus]="Perdido",[@Estatus]="No viable"),"",IF([@[Próximo seguimiento]]<>"",[@[Próximo seguimiento]],IF([@[Último contacto]]="",TODAY(),[@[Último contacto]])+IFERROR(VLOOKUP(IFERROR(LOOKUP(2,1/((tblSeguimiento[ID prospecto]=[@ID])*(tblSeguimiento[Resultado]<>"")),tblSeguimiento[Resultado]),"Sin respuesta"),ResultadoDias,2,FALSE),3))))'
    suggested_channel='IF([@Empresa]="","",IF([@[Canal preferido]]<>"",[@[Canal preferido]],IFERROR(LOOKUP(2,1/((tblSeguimiento[ID prospecto]=[@ID])*(tblSeguimiento[Canal]<>"")),tblSeguimiento[Canal]),IF([@WhatsApp]<>"","WhatsApp",IF([@Correo]<>"","Correo",IF([@Teléfono]<>"","Llamada","Por definir"))))))'
    control='IF([@Empresa]="","",IF(AND([@Correo]<>"",NOT(IFERROR(AND(ISNUMBER(SEARCH("@",[@Correo])),ISNUMBER(SEARCH(".",[@Correo])),SEARCH("@",[@Correo])>1,SEARCH(".",[@Correo])>SEARCH("@",[@Correo])+1),FALSE))),"REVISAR CORREO",IF(AND([@Teléfono]<>"",LEN([@[Tel normalizado]])<8),"REVISAR TELÉFONO",IF(AND([@WhatsApp]<>"",LEN([@[WA normalizado]])<8),"REVISAR WHATSAPP",IF(AND([@[Página web]]<>"",ISERROR(SEARCH(".",[@[Página web]]))),"REVISAR WEB",IF(AND([@Estatus]="Negociación",N([@[Valor potencial MXN]])<=0),"VALOR EN NEGOCIACIÓN",IF(AND([@Estatus]="Propuesta enviada",OR([@[Servicio CIOB potencial]]="",[@[Servicio CIOB potencial]]="Por definir")),"SERVICIO EN PROPUESTA",IF(AND([@Estatus]<>"Cliente",[@Estatus]<>"Perdido",[@Estatus]<>"No viable",[@[Próximo seguimiento]]="",[@[Próxima acción]]=""),"SIGUIENTE PASO",IF(AND(OR([@Estatus]="Perdido",[@Estatus]="No viable"),[@[Motivo de pérdida/cierre]]=""),"MOTIVO DE CIERRE",IF([@[Completitud contextual %]]<CompletitudOK,"DATOS DE ETAPA","OK"))))))))))'
    action='IF([@Empresa]="","",IF([@Duplicado]="REVISAR","Revisar posible duplicado",IF(AND([@[Control V3]]<>"OK",[@[Control V3]]<>"SIGUIENTE PASO"),"Corregir: "&[@[Control V3]],IF([@[Intentos sin respuesta]]>=3,"Cambiar canal y reactivar",IF([@Estatus]="Cliente","Programar postventa",IF(OR([@Estatus]="Perdido",[@Estatus]="No viable"),"Sin acción",IF([@[Próxima acción]]<>"",[@[Próxima acción]],IF([@Alerta]="VENCIDO","Dar seguimiento hoy por "&[@[Canal sugerido]],IF([@Alerta]="HOY","Ejecutar seguimiento por "&[@[Canal sugerido]],IF([@Estatus]="Por investigar","Investigar empresa/contacto",IF([@Estatus]="Por contactar","Contactar por "&[@[Canal sugerido]],IF([@Estatus]="Contactado","Agendar siguiente contacto",IF([@Estatus]="Reunión agendada","Preparar diagnóstico",IF([@Estatus]="Diagnóstico","Preparar propuesta",IF([@Estatus]="Propuesta enviada","Dar seguimiento a propuesta",IF([@Estatus]="Negociación","Cerrar próximos pasos",IF([@Estatus]="En pausa","Definir reactivación","Definir siguiente paso")))))))))))))))))'
    order='IF([@Empresa]="","",IF(OR([@Estatus]="Cliente",[@Estatus]="Perdido",[@Estatus]="No viable"),99000000000000,(IF(AND([@Alerta]="VENCIDO",[@Temperatura]="HOT"),1,IF([@Alerta]="VENCIDO",2,IF(AND([@Alerta]="HOY",[@Temperatura]="HOT"),3,IF([@Alerta]="HOY",4,IF([@Alerta]="PRÓXIMO",5,IF(AND([@Alerta]="SIN FECHA",[@Temperatura]="HOT"),6,IF(AND([@Alerta]="SIN FECHA",[@Temperatura]="WARM"),7,IF([@[Control V3]]<>"OK",8,IF([@Duplicado]="REVISAR",9,10))))))))))*1000000000000+(100-[@Score])*100000000+(100000000-MIN(100000000,N([@[Valor potencial MXN]])))+ROW()/1000000))'
    return {
        'AM':motive,'AN':days_stage,'AO':attempts,'AP':ctxt,'AQ':suggested_date,'AR':suggested_channel,
        'AS':action,'AT':control,'AU':norm_email,'AV':norm_tel,'AW':norm_wa,'AX':order
    }


def apply_guardrails(entries: dict[str, bytes], checkpoints: Path):
    paths=workbook_sheet_paths(entries)
    wb=ET.fromstring(entries['xl/workbook.xml'])
    styles=ET.fromstring(entries['xl/styles.xml'])
    unlocked=add_unlocked_style_variants(styles,[9,10,17,18,21,26,27])
    entries['xl/styles.xml']=xml_bytes(styles)

    # dynamic defined names
    dyn={
        'ListaEstatus':"OFFSET('Configuración'!$A$6,0,0,MAX(1,COUNTA('Configuración'!$A$6:$A$100)),1)",
        'EstatusProb':"OFFSET('Configuración'!$A$6,0,0,MAX(1,COUNTA('Configuración'!$A$6:$A$100)),2)",
        'ListaPrioridad':"OFFSET('Configuración'!$D$6,0,0,MAX(1,COUNTA('Configuración'!$D$6:$D$100)),1)",
        'PrioridadPesos':"OFFSET('Configuración'!$D$6,0,0,MAX(1,COUNTA('Configuración'!$D$6:$D$100)),2)",
        'ListaTipoContacto':"OFFSET('Configuración'!$G$6,0,0,MAX(1,COUNTA('Configuración'!$G$6:$G$100)),1)",
        'TipoPesos':"OFFSET('Configuración'!$G$6,0,0,MAX(1,COUNTA('Configuración'!$G$6:$G$100)),2)",
        'ListaExtranjera':"OFFSET('Configuración'!$J$6,0,0,MAX(1,COUNTA('Configuración'!$J$6:$J$100)),1)",
        'ExtranjeraPesos':"OFFSET('Configuración'!$J$6,0,0,MAX(1,COUNTA('Configuración'!$J$6:$J$100)),2)",
        'ListaFuente':"OFFSET('Configuración'!$M$6,0,0,MAX(1,COUNTA('Configuración'!$M$6:$M$100)),1)",
        'ListaPresencia':"OFFSET('Configuración'!$O$6,0,0,MAX(1,COUNTA('Configuración'!$O$6:$O$100)),1)",
        'ListaNecesidad':"OFFSET('Configuración'!$Q$6,0,0,MAX(1,COUNTA('Configuración'!$Q$6:$Q$100)),1)",
        'ListaServicio':"OFFSET('Configuración'!$S$6,0,0,MAX(1,COUNTA('Configuración'!$S$6:$S$100)),1)",
        'ListaResponsable':"OFFSET('Configuración'!$U$6,0,0,MAX(1,COUNTA('Configuración'!$U$6:$U$100)),1)",
        'ListaCanal':"OFFSET('Configuración'!$W$6,0,0,MAX(1,COUNTA('Configuración'!$W$6:$W$100)),1)",
        'ListaActividad':"OFFSET('Configuración'!$Y$6,0,0,MAX(1,COUNTA('Configuración'!$Y$6:$Y$100)),1)",
        'ListaResultado':"OFFSET('Configuración'!$AA$6,0,0,MAX(1,COUNTA('Configuración'!$AA$6:$AA$100)),1)",
        'ListaIdioma':"OFFSET('Configuración'!$AF$6,0,0,MAX(1,COUNTA('Configuración'!$AF$6:$AF$100)),1)",
        'ListaMotivoCierre':"OFFSET('Configuración'!$AH$6,0,0,MAX(1,COUNTA('Configuración'!$AH$6:$AH$100)),1)",
        'ResultadoDias':"OFFSET('Configuración'!$AJ$6,0,0,MAX(1,COUNTA('Configuración'!$AJ$6:$AJ$100)),2)",
    }
    for n,f in dyn.items(): add_or_replace_defined_name(wb,n,f)
    entries['xl/workbook.xml']=xml_bytes(wb)

    # Config additions + validations
    cfg=ET.fromstring(entries[paths['Configuración']])
    set_dimension(cfg,'A1:AK100')
    merge_expand(cfg,'A3:AE3','A3:AK3')
    set_inline(cfg,'A3','CONFIGURACIÓN · CATÁLOGOS Y REGLAS V3',3)
    set_inline(cfg,'A4','Agrega opciones al final de cada catálogo: dropdowns y reglas se expanden automáticamente.',4)
    for ref,text in [('AF5','Idioma preferido'),('AH5','Motivo pérdida/cierre'),('AJ5','Resultado'),('AK5','Días sugeridos')]: set_inline(cfg,ref,text,25)
    langs=['Español','Inglés','Portugués','Alemán','Francés','Otro']
    for i,x in enumerate(langs,6): set_inline(cfg,f'AF{i}',x,unlocked[9])
    motives=['Ganado','Precio','Sin presupuesto','Sin respuesta','Timing','Competencia','No fit / fuera de alcance','Decisión interna','Duplicado','Otro']
    for i,x in enumerate(motives,6): set_inline(cfg,f'AH{i}',x,unlocked[9])
    results=['Sin respuesta','Respondió','Interesado','No interesado','Reagendar','Requiere información','Reunión realizada','Propuesta solicitada','Propuesta enviada','Ganado','Perdido']
    days=[2,3,2,None,2,2,1,1,3,7,None]
    for i,(res,dd) in enumerate(zip(results,days),6):
        set_inline(cfg,f'AJ{i}',res,unlocked[9])
        set_number(cfg,f'AK{i}',dd,unlocked[27])
    # unlock existing config catalog/input cells
    for col in ['A','D','G','J','M','O','Q','S','U','W','Y','AA','AC','AE']:
        set_style_range(cfg,col,6,100,unlocked.get(9,9))
    for col in ['B']:
        set_style_range(cfg,col,6,100,unlocked[26])
    for col in ['E','H','K']:
        set_style_range(cfg,col,6,100,unlocked[27])
    set_style_range(cfg,'AD',6,18,unlocked[9])
    # restore number styles for numeric rule cells using unlocked variants
    for rr in [6,7,8,10,11,12,13,14]: find_cell(cfg,f'AD{rr}',True).set('s',str(unlocked[9]))
    find_cell(cfg,'AD9',True).set('s',str(unlocked[26]))
    # config validations
    add_dv(cfg,'B6:B100','decimal','0',operator='between',formula2='1',error_style='stop',error='Probabilidad: usa un valor entre 0% y 100%.')
    for rg in ['E6:E100','H6:H100','K6:K100']:
        add_dv(cfg,rg,'whole','0',operator='greaterThanOrEqual',error_style='stop',error='Los pesos deben ser enteros no negativos.')
    add_dv(cfg,'AD6','whole','0',operator='greaterThan',error_style='stop',error='Los días deben ser enteros positivos.')
    add_dv(cfg,'AD12','whole','0',operator='greaterThan',error_style='stop',error='Los días deben ser enteros positivos.')
    add_dv(cfg,'AD7','custom','$AD$7>$AD$8',error_style='stop',error='Score HOT debe ser mayor que Score WARM.')
    add_dv(cfg,'AD8','custom','$AD$8<$AD$7',error_style='stop',error='Score WARM debe ser menor que Score HOT.')
    add_dv(cfg,'AD9','decimal','0',operator='between',formula2='1',error_style='stop',error='Completitud mínima: valor entre 0% y 100%.')
    add_dv(cfg,'AK6:AK100','custom','=OR(AK6="",AND(ISNUMBER(AK6),AK6=INT(AK6),AK6>0))',error_style='stop',error='Los días sugeridos deben ser enteros positivos o quedar vacíos.')
    ensure_sheet_protection(cfg)
    entries[paths['Configuración']]=xml_bytes(cfg)

    # Base: unlock input cells + stronger validations. Full V3 columns are added in intelligence phase.
    base=ET.fromstring(entries[paths['Base de contactos']])
    input_cols={'B':17,'C':17,'D':18,'E':17,'F':17,'G':17,'H':17,'I':17,'J':17,'K':17,'L':17,'M':17,'N':18,'O':17,'P':18,'Q':17,'R':17,'S':17,'U':17,'Y':21,'AE':18}
    for col,style in input_cols.items(): set_style_range(base,col,7,506,unlocked[style])
    # list validations already exist; add soft format + cross-field warnings
    phone_norm='SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(F7," ",""),"-",""),"(",""),")",""),"+",""),".",""),"/","")'
    wa_norm=phone_norm.replace('F7','G7')
    add_dv(base,'H7:H506','custom','=OR(H7="",IFERROR(AND(ISNUMBER(SEARCH("@",H7)),ISNUMBER(SEARCH(".",H7)),SEARCH("@",H7)>1,SEARCH(".",H7)>SEARCH("@",H7)+1),FALSE))',error_style='warning',error='Correo con formato inusual. Puedes continuar, pero conviene revisarlo.')
    add_dv(base,'F7:F506','custom',f'=OR(F7="",LEN({phone_norm})>=8)',error_style='warning',error='Teléfono muy corto o con formato inusual.')
    add_dv(base,'G7:G506','custom',f'=OR(G7="",LEN({wa_norm})>=8)',error_style='warning',error='WhatsApp muy corto o con formato inusual.')
    add_dv(base,'I7:I506','custom','=OR(I7="",ISNUMBER(SEARCH(".",I7)))',error_style='warning',error='Web con formato inusual. Ejemplo: empresa.com')
    add_dv(base,'Y7:Y506','custom','=OR($T7<>"Negociación",N($Y7)>0)',error_style='warning',error='En Negociación conviene registrar Valor potencial MXN.')
    add_dv(base,'R7:R506','custom','=OR($T7<>"Propuesta enviada",AND($R7<>"",$R7<>"Por definir"))',error_style='warning',error='En Propuesta enviada conviene definir el servicio CIOB potencial.')
    ensure_sheet_protection(base)
    entries[paths['Base de contactos']]=xml_bytes(base)

    # Tracking: extend with motive + change-stage helper; unlock capture fields; validations
    seg=ET.fromstring(entries[paths['Seguimiento comercial']])
    set_dimension(seg,'A1:P1006')
    for old,new in [('A3:N3','A3:P3'),('A4:N4','A4:P4'),('A5:N5','A5:P5')]: merge_expand(seg,old,new)
    set_inline(seg,'A3','CIOB · HISTORIAL DE SEGUIMIENTO V3 (FUENTE DE VERDAD)',3)
    set_inline(seg,'O6','Motivo de pérdida/cierre',15)
    set_inline(seg,'P6','Cambio etapa?',15)
    # styles / values / formula
    for r in range(7,1007):
        set_style_range(seg,'O',r,r,unlocked[18])
        formula='IF(OR([@[ID prospecto]]="",[@[Estatus posterior]]=""),"",IFERROR(--(LOOKUP(2,1/((tblSeguimiento[ID prospecto]=[@[ID prospecto]])*(tblSeguimiento[Estatus posterior]<>"")*(ROW(tblSeguimiento[ID prospecto])<ROW())),tblSeguimiento[Estatus posterior])<>[@[Estatus posterior]]),1))'
        set_formula(seg,f'P{r}',formula,16)
    # unlock tracking input cells
    for col,style in {'B':10,'C':18,'F':18,'G':18,'H':18,'I':18,'J':18,'K':10,'M':18,'N':18,'O':18}.items():
        set_style_range(seg,col,7,1006,unlocked[style])
    # header and col widths
    seg_cols=[]
    widths=[11,12,14,22,20,14,20,22,18,22,15,18,18,24,22,10]
    for i,w in enumerate(widths,1):
        spec={'min':i,'max':i,'width':w,'customWidth':1}
        if i in (1,16):
            spec['hidden']=1
            spec['outlineLevel']=1
        seg_cols.append(spec)
    rebuild_cols(seg,seg_cols)
    add_dv(seg,'O7:O1006','list','ListaMotivoCierre',error_style='warning',error='Usa un motivo del catálogo para cierres Perdido/No viable y, si aplica, Ganado.')
    add_dv(seg,'G7:G1006','custom','=OR($G7="",AND($B7<>"",$C7<>""))',error_style='warning',error='Si registras una actividad, completa Fecha e ID prospecto.')
    add_dv(seg,'K7:K1006','custom','=OR($K7="",$B7="",$K7>=$B7)',error_style='warning',error='El próximo seguimiento no debería ser anterior a la actividad.')
    add_dv(seg,'M7:M1006','custom','=OR(NOT(OR($M7="Cliente",$M7="Perdido",$M7="No viable")),AND($I7<>"",IF(OR($M7="Perdido",$M7="No viable"),$O7<>"",TRUE)))',error_style='warning',error='Para cierre, registra Resultado y motivo cuando corresponda.')
    ensure_sheet_protection(seg)
    entries[paths['Seguimiento comercial']]=xml_bytes(seg)

    # Table2 extension
    t2=ET.fromstring(entries['xl/tables/table2.xml']); t2.set('ref','A6:P1006')
    change_formula='IF(OR([[#This Row],[ID prospecto]]="",[[#This Row],[Estatus posterior]]=""),"",IFERROR(--(LOOKUP(2,1/((tblSeguimiento[ID prospecto]=[[#This Row],[ID prospecto]])*(tblSeguimiento[Estatus posterior]<>"")*(ROW(tblSeguimiento[ID prospecto])<ROW())),tblSeguimiento[Estatus posterior])<>[[#This Row],[Estatus posterior]]),1))'
    add_table_columns(t2,[('Motivo de pérdida/cierre',2,None),('Cambio etapa?',0,change_formula)])
    entries['xl/tables/table2.xml']=xml_bytes(t2)

    cp=checkpoints/'01_guardrails.xlsx'; write_entries(entries,cp); return cp,unlocked


def apply_intelligence(entries: dict[str, bytes], checkpoints: Path, unlocked: dict[int,int]):
    paths=workbook_sheet_paths(entries)
    base=ET.fromstring(entries[paths['Base de contactos']])
    t1=ET.fromstring(entries['xl/tables/table1.xml']); t1.set('ref','A6:AX506')
    # headers
    headers=['Idioma preferido','Canal preferido','Motivo de pérdida/cierre','Días en etapa','Intentos sin respuesta','Completitud contextual %','Seguimiento sugerido','Canal sugerido','Acción sugerida V3','Control V3','Email normalizado','Tel normalizado','WA normalizado','Orden Mi día']
    for idx,name in enumerate(headers,col_num('AK')): set_inline(base,f'{num_col(idx)}6',name,15)
    # input styles + formulas
    set_style_range(base,'AK',7,506,unlocked[17]); set_style_range(base,'AL',7,506,unlocked[17])
    formulas=formula_base()
    style_map={'AM':16,'AN':16,'AO':16,'AP':22,'AQ':19,'AR':20,'AS':20,'AT':16,'AU':16,'AV':16,'AW':16,'AX':16}
    for col,formula in formulas.items():
        for r in range(7,507): set_formula(base,f'{col}{r}',formula,style_map[col])
    # update existing formulas to contextual / normalized V3 intelligence
    score='IF([@Empresa]="","",MIN(100,IFERROR(VLOOKUP([@Prioridad],PrioridadPesos,2,FALSE),0)+IFERROR(VLOOKUP([@[Tipo contacto]],TipoPesos,2,FALSE),0)+IFERROR(VLOOKUP([@[Empresa extranjera?]],ExtranjeraPesos,2,FALSE),0)+([@[Probabilidad %]]*PesoEtapa)+([@[Completitud contextual %]]*PesoCompletitud)))'
    quality='IF([@Empresa]="","",IF([@[Completitud contextual %]]>=CompletitudOK,"OK","INCOMPLETO"))'
    dup='IF([@Empresa]="","",IF(OR(AND([@[Email normalizado]]<>"",COUNTIF(tblProspectos[Email normalizado],[@[Email normalizado]])>1),AND([@[Tel normalizado]]<>"",COUNTIF(tblProspectos[Tel normalizado],[@[Tel normalizado]])>1),AND([@[WA normalizado]]<>"",COUNTIF(tblProspectos[WA normalizado],[@[WA normalizado]])>1),AND([@Empresa]<>"",[@Nombre]<>"",COUNTIFS(tblProspectos[Empresa],[@Empresa],tblProspectos[Nombre],[@Nombre])>1)),"REVISAR","OK"))'
    action_alias='IF([@Empresa]="","",[@[Acción sugerida V3]])'
    for col,formula,style in [('AA',score,23),('AD',quality,16),('AG',dup,16),('AJ',action_alias,20)]:
        for r in range(7,507): set_formula(base,f'{col}{r}',formula,style)
    set_table_formula(t1,'Score',score.replace('[@','[[#This Row],').replace(']]]',']]')) if False else None
    # Set table formulas with table syntax explicitly
    set_table_formula(t1,'Score','IF([[#This Row],Empresa]="","",MIN(100,IFERROR(VLOOKUP([[#This Row],Prioridad],PrioridadPesos,2,FALSE),0)+IFERROR(VLOOKUP([[#This Row],[Tipo contacto]],TipoPesos,2,FALSE),0)+IFERROR(VLOOKUP([[#This Row],[Empresa extranjera?]],ExtranjeraPesos,2,FALSE),0)+([[#This Row],[Probabilidad %]]*PesoEtapa)+([[#This Row],[Completitud contextual %]]*PesoCompletitud)))')
    set_table_formula(t1,'Calidad de datos','IF([[#This Row],Empresa]="","",IF([[#This Row],[Completitud contextual %]]>=CompletitudOK,"OK","INCOMPLETO"))')
    set_table_formula(t1,'Duplicado','IF([[#This Row],Empresa]="","",IF(OR(AND([[#This Row],[Email normalizado]]<>"",COUNTIF(tblProspectos[Email normalizado],[[#This Row],[Email normalizado]])>1),AND([[#This Row],[Tel normalizado]]<>"",COUNTIF(tblProspectos[Tel normalizado],[[#This Row],[Tel normalizado]])>1),AND([[#This Row],[WA normalizado]]<>"",COUNTIF(tblProspectos[WA normalizado],[[#This Row],[WA normalizado]])>1),AND([[#This Row],Empresa]<>"",[[#This Row],Nombre]<>"",COUNTIFS(tblProspectos[Empresa],[[#This Row],Empresa],tblProspectos[Nombre],[[#This Row],Nombre])>1)),"REVISAR","OK"))')
    set_table_formula(t1,'Siguiente acción sugerida','IF([[#This Row],Empresa]="","",[[#This Row],[Acción sugerida V3]])')
    # new table cols; Dxf 1=input white, 0 auto, 3 date auto,4 action auto,6 pct auto
    table_formulas={
        'Motivo de pérdida/cierre':'IF([[#This Row],Empresa]="","",IFERROR(LOOKUP(2,1/((tblSeguimiento[ID prospecto]=[[#This Row],ID])*(tblSeguimiento[Motivo de pérdida/cierre]<>"")),tblSeguimiento[Motivo de pérdida/cierre]),""))',
        'Días en etapa':'IF([[#This Row],Empresa]="","",IFERROR(TODAY()-LOOKUP(2,1/((tblSeguimiento[ID prospecto]=[[#This Row],ID])*(tblSeguimiento[Cambio etapa?]=1)*(tblSeguimiento[Estatus posterior]=[[#This Row],Estatus])*(tblSeguimiento[Fecha]<>"")),tblSeguimiento[Fecha]),IF([[#This Row],[Último contacto]]="","",TODAY()-[[#This Row],[Último contacto]])))',
        'Intentos sin respuesta':'IF([[#This Row],Empresa]="","",SUMPRODUCT((tblSeguimiento[ID prospecto]=[[#This Row],ID])*(tblSeguimiento[Resultado]="Sin respuesta")*(ROW(tblSeguimiento[Resultado])>IFERROR(LOOKUP(2,1/((tblSeguimiento[ID prospecto]=[[#This Row],ID])*(tblSeguimiento[Resultado]<>"")*(tblSeguimiento[Resultado]<>"Sin respuesta")),ROW(tblSeguimiento[Resultado])),0))))',
        'Completitud contextual %':formulas['AP'].replace('[@','[[#This Row],').replace(']]]',']]'),
        'Seguimiento sugerido':formulas['AQ'].replace('[@','[[#This Row],').replace(']]]',']]'),
        'Canal sugerido':formulas['AR'].replace('[@','[[#This Row],').replace(']]]',']]'),
        'Acción sugerida V3':formulas['AS'].replace('[@','[[#This Row],').replace(']]]',']]'),
        'Control V3':formulas['AT'].replace('[@','[[#This Row],').replace(']]]',']]'),
        'Email normalizado':formulas['AU'].replace('[@','[[#This Row],').replace(']]]',']]'),
        'Tel normalizado':formulas['AV'].replace('[@','[[#This Row],').replace(']]]',']]'),
        'WA normalizado':formulas['AW'].replace('[@','[[#This Row],').replace(']]]',']]'),
        'Orden Mi día':formulas['AX'].replace('[@','[[#This Row],').replace(']]]',']]'),
    }
    # Some naive conversion above can be ugly; use worksheet formulas as calculated formula text is advisory, Excel still sees cell formulas.
    add_table_columns(t1,[
        ('Idioma preferido',1,None),('Canal preferido',1,None),
        ('Motivo de pérdida/cierre',0,table_formulas['Motivo de pérdida/cierre']),('Días en etapa',0,table_formulas['Días en etapa']),
        ('Intentos sin respuesta',0,table_formulas['Intentos sin respuesta']),('Completitud contextual %',6,table_formulas['Completitud contextual %']),
        ('Seguimiento sugerido',3,table_formulas['Seguimiento sugerido']),('Canal sugerido',4,table_formulas['Canal sugerido']),
        ('Acción sugerida V3',4,table_formulas['Acción sugerida V3']),('Control V3',0,table_formulas['Control V3']),
        ('Email normalizado',0,table_formulas['Email normalizado']),('Tel normalizado',0,table_formulas['Tel normalizado']),
        ('WA normalizado',0,table_formulas['WA normalizado']),('Orden Mi día',0,table_formulas['Orden Mi día']),
    ])
    entries['xl/tables/table1.xml']=xml_bytes(t1)
    set_dimension(base,'A1:AX506')
    for old,new in [('A3:AJ3','A3:AX3'),('A4:AJ4','A4:AX4'),('A5:AJ5','A5:AX5')]: merge_expand(base,old,new)
    set_inline(base,'A3','CIOB · BASE DE CONTACTOS V3',3)
    set_inline(base,'A4','Núcleo visible, inteligencia debajo: expande grupos sólo cuando necesites el detalle.',4)
    set_inline(base,'A5','Seguimiento gobierna estatus, fechas, próxima acción, motivo de cierre y días en etapa.',14)
    rebuild_cols(base,base_col_specs())
    # validations for new input columns
    add_dv(base,'AK7:AK506','list','ListaIdioma',error_style='warning',error='Selecciona un idioma del catálogo o déjalo vacío.')
    add_dv(base,'AL7:AL506','list','ListaCanal',error_style='warning',error='Selecciona un canal del catálogo o déjalo vacío.')
    # control conditional formatting
    add_conditional_contains(base,'AT7:AT506','REVISAR',10,50)
    add_conditional_contains(base,'AT7:AT506','SIGUIENTE',11,51)
    add_conditional_contains(base,'AT7:AT506','DATOS',11,52)
    entries[paths['Base de contactos']]=xml_bytes(base)

    cp=checkpoints/'02_intelligence.xlsx'; write_entries(entries,cp); return cp


def apply_productivity(entries: dict[str, bytes], checkpoints: Path):
    paths=workbook_sheet_paths(entries)
    mid=ET.fromstring(entries[paths['Mi día']])
    set_dimension(mid,'A1:N59')
    merge_expand(mid,'A3:I3','A3:M3'); merge_expand(mid,'A4:I4','A4:M4')
    set_inline(mid,'A3','MI DÍA V3 · COLA COMERCIAL PRIORIZADA',3)
    set_inline(mid,'A4','Urgencia primero; después temperatura, score y valor. Filtra por responsable sin duplicar hojas.',4)
    set_inline(mid,'A5','Responsable (vacío = todos)',13)
    set_inline(mid,'C5','',17)
    add_dv(mid,'C5','list','ListaResponsable',error_style='warning',error='Selecciona un responsable del catálogo o deja vacío para ver a todos.')
    # KPI cards
    cards=[('A6','VENCIDOS'),('C6','HOY'),('E6','PRÓXIMOS'),('G6','SIN FECHA'),('I6','HOT'),('K6','SIN RESP. 3+')]
    for ref,text in cards: set_inline(mid,ref,text,5)
    metrics={
        'A7':'IF($C$5="",COUNTIF(tblProspectos[Alerta],"VENCIDO"),COUNTIFS(tblProspectos[Alerta],"VENCIDO",tblProspectos[Responsable],$C$5))',
        'C7':'IF($C$5="",COUNTIF(tblProspectos[Alerta],"HOY"),COUNTIFS(tblProspectos[Alerta],"HOY",tblProspectos[Responsable],$C$5))',
        'E7':'IF($C$5="",COUNTIF(tblProspectos[Alerta],"PRÓXIMO"),COUNTIFS(tblProspectos[Alerta],"PRÓXIMO",tblProspectos[Responsable],$C$5))',
        'G7':'IF($C$5="",COUNTIF(tblProspectos[Alerta],"SIN FECHA"),COUNTIFS(tblProspectos[Alerta],"SIN FECHA",tblProspectos[Responsable],$C$5))',
        'I7':'IF($C$5="",COUNTIF(tblProspectos[Temperatura],"HOT"),COUNTIFS(tblProspectos[Temperatura],"HOT",tblProspectos[Responsable],$C$5))',
        'K7':'IF($C$5="",COUNTIFS(tblProspectos[Intentos sin respuesta],">=3"),COUNTIFS(tblProspectos[Intentos sin respuesta],">=3",tblProspectos[Responsable],$C$5))',
    }
    for ref,form in metrics.items(): set_formula(mid,ref,form,7)
    # quick activity top-right
    set_inline(mid,'M6','＋ ACTIVIDAD',5); add_hyperlink_location(mid,'M6',"'Seguimiento comercial'!B7",'＋ ACTIVIDAD')
    # table headers
    headers=['ID','Empresa','Contacto','Temp.','Prioridad','Alerta','Próx. fecha','Acción sugerida','Responsable','WA','Correo','Web','＋ Act.','_idx']
    for i,h in enumerate(headers,1): set_inline(mid,f'{num_col(i)}9',h,15)
    # rows 10:59, helper N = row index by sorted Orden Mi día + owner filter
    for r in range(10,60):
        nform=f'IFERROR(MATCH(AGGREGATE(15,6,tblProspectos[Orden Mi día]/((tblProspectos[Empresa]<>"")*(tblProspectos[Orden Mi día]<99000000000000)*(($C$5="")+(tblProspectos[Responsable]=$C$5)>0)),ROWS($N$10:N{r})),tblProspectos[Orden Mi día],0),"")'
        set_formula(mid,f'N{r}',nform,9)
        idx=f'$N{r}'
        mapping={'A':'ID','B':'Empresa','C':'Nombre','D':'Temperatura','E':'Prioridad','F':'Alerta','G':'Seguimiento sugerido','H':'Acción sugerida V3','I':'Responsable'}
        for col,name in mapping.items():
            style=10 if col=='G' else 9
            set_formula(mid,f'{col}{r}',f'IF({idx}="","",INDEX(tblProspectos[{name}],{idx}))',style)
        # quick links
        set_formula(mid,f'J{r}',f'IF({idx}="","",IF(INDEX(tblProspectos[WA normalizado],{idx})="","",HYPERLINK("https://wa.me/"&INDEX(tblProspectos[WA normalizado],{idx}),"WA")))',9)
        set_formula(mid,f'K{r}',f'IF({idx}="","",IF(INDEX(tblProspectos[Correo],{idx})="","",HYPERLINK("mailto:"&INDEX(tblProspectos[Correo],{idx}),"Correo")))',9)
        set_formula(mid,f'L{r}',f'IF({idx}="","",IF(INDEX(tblProspectos[Página web],{idx})="","",HYPERLINK(IF(LEFT(INDEX(tblProspectos[Página web],{idx}),4)="http",INDEX(tblProspectos[Página web],{idx}),"https://"&INDEX(tblProspectos[Página web],{idx})),"Web")))',9)
        set_formula(mid,f'M{r}',f'IF({idx}="","",HYPERLINK("#\'Seguimiento comercial\'!B7","＋"))',9)
    # widths / hidden helper
    specs=[]
    widths=[13,24,21,10,12,13,15,30,17,8,10,8,8,4]
    for i,w in enumerate(widths,1):
        a={'min':i,'max':i,'width':w,'customWidth':1}
        if i==14: a['hidden']=1
        specs.append(a)
    rebuild_cols(mid,specs)
    # protection: owner selector unlocked. Sheet cells otherwise formula/static locked.
    # C5 currently style 17 locked; protection is optional on Mi día since only selector editable. Use unlocked style id already present in workbook by matching last variants is hard.
    # Instead leave Mi día unprotected; the main automatic tables Base/Seguimiento are protected.
    # conditional formatting extend existing D/F plus Control implicit in action
    entries[paths['Mi día']]=xml_bytes(mid)
    cp=checkpoints/'03_productivity.xlsx'; write_entries(entries,cp); return cp


def chart_bar(title, cat_ref, val_ref, color='173A5E', horizontal=True):
    bar_dir='bar' if horizontal else 'col'
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<c:chartSpace xmlns:c="{C}" xmlns:a="{A}" xmlns:r="{R}"><c:lang val="es-MX"/><c:style val="10"/><c:chart><c:title><c:tx><c:rich><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="es-MX"/><a:t>{title}</a:t></a:r></a:p></c:rich></c:tx><c:layout/></c:title><c:plotArea><c:layout/><c:barChart><c:barDir val="{bar_dir}"/><c:grouping val="clustered"/><c:ser><c:idx val="0"/><c:order val="0"/><c:spPr><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:ln><a:noFill/></a:ln></c:spPr><c:cat><c:strRef><c:f>{cat_ref}</c:f></c:strRef></c:cat><c:val><c:numRef><c:f>{val_ref}</c:f></c:numRef></c:val></c:ser><c:axId val="51010001"/><c:axId val="51010002"/></c:barChart><c:catAx><c:axId val="51010001"/><c:scaling><c:orientation val="minMax"/></c:scaling><c:axPos val="l"/><c:tickLblPos val="nextTo"/><c:crossAx val="51010002"/><c:crosses val="autoZero"/></c:catAx><c:valAx><c:axId val="51010002"/><c:scaling><c:orientation val="minMax"/></c:scaling><c:axPos val="b"/><c:tickLblPos val="nextTo"/><c:crossAx val="51010001"/><c:crosses val="autoZero"/></c:valAx></c:plotArea><c:plotVisOnly val="1"/></c:chart><c:spPr><a:ln><a:noFill/></a:ln></c:spPr></c:chartSpace>'''.encode('utf-8')


def add_chart_anchor(drawing: ET.Element, rel_id: str, chart_num: int, c1: int,r1: int,c2: int,r2: int):
    a=ET.SubElement(drawing,qn(XDR,'twoCellAnchor'))
    fr=ET.SubElement(a,qn(XDR,'from'))
    for tag,val in [('col',c1),('colOff',0),('row',r1),('rowOff',0)]: ET.SubElement(fr,qn(XDR,tag)).text=str(val)
    to=ET.SubElement(a,qn(XDR,'to'))
    for tag,val in [('col',c2),('colOff',0),('row',r2),('rowOff',0)]: ET.SubElement(to,qn(XDR,tag)).text=str(val)
    gf=ET.SubElement(a,qn(XDR,'graphicFrame'),{'macro':''})
    nv=ET.SubElement(gf,qn(XDR,'nvGraphicFramePr')); ET.SubElement(nv,qn(XDR,'cNvPr'),{'id':str(chart_num+1),'name':f'Chart {chart_num}'}); ET.SubElement(nv,qn(XDR,'cNvGraphicFramePr'))
    xfrm=ET.SubElement(gf,qn(XDR,'xfrm')); ET.SubElement(xfrm,qn(A,'off'),{'x':'0','y':'0'}); ET.SubElement(xfrm,qn(A,'ext'),{'cx':'0','cy':'0'})
    gr=ET.SubElement(gf,qn(A,'graphic')); gd=ET.SubElement(gr,qn(A,'graphicData'),{'uri':C}); ET.SubElement(gd,qn(C,'chart'),{qn(R,'id'):rel_id})
    ET.SubElement(a,qn(XDR,'clientData'))


def apply_visual(entries: dict[str, bytes], checkpoints: Path):
    paths=workbook_sheet_paths(entries)
    sst=get_shared_strings(entries)
    # Base premium compact already grouped; add badge CF for new control and titles. Update row heights and outlinePr.
    base=ET.fromstring(entries[paths['Base de contactos']])
    sp=base.find('m:sheetPr',NS)
    if sp is None:
        sp=ET.Element(qn(M,'sheetPr')); base.insert(0,sp)
    op=sp.find('m:outlinePr',NS)
    if op is None: op=ET.SubElement(sp,qn(M,'outlinePr'))
    op.set('summaryRight','1'); op.set('showOutlineSymbols','1')
    # discreet badges already present; ensure temp/alerts/control conditional formatting
    add_conditional_contains(base,'AF7:AF506','HOT',13,60); add_conditional_contains(base,'AF7:AF506','WARM',11,61); add_conditional_contains(base,'AF7:AF506','COLD',14,62)
    add_conditional_contains(base,'AC7:AC506','VENCIDO',10,63); add_conditional_contains(base,'AC7:AC506','HOY',11,64); add_conditional_contains(base,'AC7:AC506','PRÓXIMO',11,65)

    # Final visual hygiene: an unused row must look genuinely empty.
    # Prospect IDs remain deterministic, but only appear once Empresa exists.
    t1=ET.fromstring(entries['xl/tables/table1.xml'])
    set_table_formula(t1,'ID','IF([[#This Row],Empresa]="","","CIOB-"&TEXT(ROW()-6,"000"))')
    for r in range(7,507):
        empresa=cell_text(base,f'B{r}',sst)
        old_id=cell_text(base,f'A{r}',sst)
        set_formula(base,f'A{r}',f'IF(B{r}="","","CIOB-"&TEXT(ROW()-6,"000"))',16,old_id if empresa else None)
        row=find_row(base,r,True)
        if not empresa:
            for c in row.findall('m:c',NS):
                if c.find('m:f',NS) is not None:
                    clear_formula_cache(c)
    # V2 had no Seguimiento history. Remove stale 0 caches that QuickLook renders as 31-dic-1899 / 0.
    for r in range(7,507):
        if cell_text(base,f'B{r}',sst):
            for col in ('V','W','X','AB','AI'):
                c=find_cell(base,f'{col}{r}')
                if c is not None and c.find('m:f',NS) is not None:
                    clear_formula_cache(c)
    set_row_height(base,7,506,20)
    find_row(base,6,True).set('ht','27'); find_row(base,6,True).set('customHeight','1')
    entries['xl/tables/table1.xml']=xml_bytes(t1)
    entries[paths['Base de contactos']]=xml_bytes(base)

    # Seguimiento hygiene: internal activity IDs/helpers hidden; blank rows stay blank.
    seg=ET.fromstring(entries[paths['Seguimiento comercial']])
    t2=ET.fromstring(entries['xl/tables/table2.xml'])
    set_table_formula(t2,'Actividad ID','IF([[#This Row],[ID prospecto]]="","","ACT-"&TEXT(ROW()-6,"0000"))')
    for r in range(7,1007):
        prospect=cell_text(seg,f'C{r}',sst)
        old_act=cell_text(seg,f'A{r}',sst)
        set_formula(seg,f'A{r}',f'IF(C{r}="","","ACT-"&TEXT(ROW()-6,"0000"))',16,old_act if prospect else None)
        if not prospect:
            for col in ('D','E','L','P'):
                c=find_cell(seg,f'{col}{r}')
                if c is not None and c.find('m:f',NS) is not None:
                    clear_formula_cache(c)
    set_row_height(seg,7,1006,20)
    find_row(seg,6,True).set('ht','27'); find_row(seg,6,True).set('customHeight','1')
    entries['xl/tables/table2.xml']=xml_bytes(t2)
    entries[paths['Seguimiento comercial']]=xml_bytes(seg)

    # Mi día is also a table-like working surface: keep rows rhythmically uniform.
    mid=ET.fromstring(entries[paths['Mi día']])
    set_row_height(mid,10,59,21)
    find_row(mid,9,True).set('ht','26'); find_row(mid,9,True).set('customHeight','1')
    entries[paths['Mi día']]=xml_bytes(mid)

    # Dashboard executive redesign/data tables
    dash=ET.fromstring(entries[paths['Dashboard']])
    set_dimension(dash,'A1:U63')
    merge_expand(dash,'A3:N3','A3:Q3'); merge_expand(dash,'A4:N4','A4:Q4')
    set_inline(dash,'A3','CIOB · DASHBOARD EJECUTIVO V3',3)
    set_inline(dash,'A4','Pipeline, conversión, temperatura, salud de seguimiento, fuentes y motivos de cierre.',4)
    # clear top area 6:13 contents while preserving nav/title
    for r in range(6,14):
        row=find_row(dash,r,True)
        for c in list(row.findall('m:c',NS)):
            if col_num(ref_col(c.attrib['r']))<=17: clear_cell_contents(c)
    # remove merges in KPI area only, rebuild selected
    mcroot=dash.find('m:mergeCells',NS)
    if mcroot is not None:
        for mc in list(mcroot.findall('m:mergeCell',NS)):
            ref=mc.attrib['ref']
            if any(str(rr) in ref for rr in range(6,14)):
                mcroot.remove(mc)
    def add_merge(ref):
        nonlocal mcroot
        if mcroot is None:
            mcroot=ET.Element(qn(M,'mergeCells'),{'count':'0'}); insert_before_first(dash,mcroot,['conditionalFormatting','dataValidations','hyperlinks','pageMargins','drawing'])
        ET.SubElement(mcroot,qn(M,'mergeCell'),{'ref':ref}); mcroot.set('count',str(len(mcroot.findall('m:mergeCell',NS))))
    cards=[
        ('A6:B6','A7:B7','PIPELINE','SUM(tblProspectos[Valor potencial MXN])',11),
        ('D6:E6','D7:E7','PONDERADO','SUM(tblProspectos[Pipeline ponderado MXN])',11),
        ('G6:H6','G7:H7','HOT','COUNTIF(tblProspectos[Temperatura],"HOT")',7),
        ('J6:K6','J7:K7','VENCIDOS','COUNTIF(tblProspectos[Alerta],"VENCIDO")',7),
        ('A9:B9','A10:B10','CLIENTES','COUNTIF(tblProspectos[Estatus],"Cliente")',7),
        ('D9:E9','D10:E10','CONVERSIÓN','IFERROR(COUNTIF(tblProspectos[Estatus],"Cliente")/COUNTIF(tblProspectos[Empresa],"<>"),0)',12),
        ('G9:H9','G10:H10','SIN RESP. 3+','COUNTIFS(tblProspectos[Intentos sin respuesta],">=3")',7),
        ('J9:K9','J10:K10','DATOS DE ETAPA','COUNTIF(tblProspectos[Calidad de datos],"INCOMPLETO")',7),
    ]
    for hmerge,vmerge,label,formula,style in cards:
        add_merge(hmerge); add_merge(vmerge)
        hcell=hmerge.split(':')[0]; vcell=vmerge.split(':')[0]
        set_inline(dash,hcell,label,5); set_formula(dash,vcell,formula,style)
    # supporting tables
    # keep existing status/temperature/priority/health, refresh health and add sources/loss
    set_inline(dash,'J16','SALUD',13); set_inline(dash,'K16','PROSPECTOS',13)
    health=['VENCIDO','HOY','PRÓXIMO','SIN FECHA','OK','CLIENTE','CERRADO']
    for i,x in enumerate(health,17): set_inline(dash,f'J{i}',x,9); set_formula(dash,f'K{i}',f'COUNTIF(tblProspectos[Alerta],J{i})',9)
    set_inline(dash,'M16','FUENTE',13); set_inline(dash,'N16','PROSPECTOS',13)
    sources=['Tarjeta','Folleto','Referido','LinkedIn','Web','Evento / Cámara','Campaña','Alianza','Otro']
    for i,x in enumerate(sources,17): set_inline(dash,f'M{i}',x,9); set_formula(dash,f'N{i}',f'COUNTIF(tblProspectos[Fuente],M{i})',9)
    set_inline(dash,'P16','MOTIVO CIERRE',13); set_inline(dash,'Q16','PROSPECTOS',13)
    motives=['Ganado','Precio','Sin presupuesto','Sin respuesta','Timing','Competencia','No fit / fuera de alcance','Decisión interna','Duplicado','Otro']
    for i,x in enumerate(motives,17): set_inline(dash,f'P{i}',x,9); set_formula(dash,f'Q{i}',f'COUNTIF(tblProspectos[Motivo de pérdida/cierre],P{i})',9)
    # widths
    rebuild_cols(dash,[{'min':i,'max':i,'width':12.5,'customWidth':1} for i in range(1,18)])
    entries[paths['Dashboard']]=xml_bytes(dash)

    # Add 3 charts to existing drawing
    drawing=ET.fromstring(entries['xl/drawings/drawing1.xml'])
    rels=ET.fromstring(entries['xl/drawings/_rels/drawing1.xml.rels'])
    # avoid duplicate if rerun
    existing_ids={r.attrib['Id'] for r in rels.findall(qn(PKG_R,'Relationship'))}
    for num,(title,cat,val,color,anchor) in enumerate([
        ('Salud de seguimiento','Dashboard!$J$17:$J$23','Dashboard!$K$17:$K$23','C8A24A',(0,47,6,62)),
        ('Fuentes','Dashboard!$M$17:$M$25','Dashboard!$N$17:$N$25','2E7D60',(7,47,13,62)),
        ('Motivos de cierre','Dashboard!$P$17:$P$26','Dashboard!$Q$17:$Q$26','6E8798',(14,47,20,62)),
    ],3):
        rid=f'rId{num}'
        if rid not in existing_ids:
            ET.SubElement(rels,qn(PKG_R,'Relationship'),{'Id':rid,'Type':'http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart','Target':f'../charts/chart{num}.xml'})
            add_chart_anchor(drawing,rid,num,*anchor)
        entries[f'xl/charts/chart{num}.xml']=chart_bar(title,cat,val,color,horizontal=True)
    entries['xl/drawings/drawing1.xml']=xml_bytes(drawing)
    entries['xl/drawings/_rels/drawing1.xml.rels']=xml_bytes(rels)
    # Content types overrides for charts
    ct=ET.fromstring(entries['[Content_Types].xml'])
    existing={x.attrib.get('PartName') for x in ct.findall(qn(CT,'Override'))}
    for num in [3,4,5]:
        part=f'/xl/charts/chart{num}.xml'
        if part not in existing: ET.SubElement(ct,qn(CT,'Override'),{'PartName':part,'ContentType':'application/vnd.openxmlformats-officedocument.drawingml.chart+xml'})
    entries['[Content_Types].xml']=xml_bytes(ct)

    # Instructions V3
    inst=ET.fromstring(entries[paths['Instrucciones']])
    set_inline(inst,'A3','GUÍA RÁPIDA · CRM CIOB V3',3)
    set_inline(inst,'A4','Más inteligencia debajo, menos fricción arriba: Base captura, Seguimiento manda y Mi día prioriza.',4)
    set_inline(inst,'A17','NOVEDADES V3',13)
    set_inline(inst,'B18','Mi día',9); set_inline(inst,'C18','Filtra por responsable y trabaja la cola ya ordenada por urgencia, temperatura, score y valor.',9)
    set_inline(inst,'B19','Acciones rápidas',9); set_inline(inst,'C19','Desde Mi día abre WhatsApp, correo, web o salta a registrar una actividad.',9)
    set_inline(inst,'B20','Inteligencia',9); set_inline(inst,'C20','Días en etapa, intentos sin respuesta, completitud contextual, fecha/canal/acción sugeridos y control V3.',9)
    set_inline(inst,'B21','Cierres',9); set_inline(inst,'C21','Registra motivo de pérdida/cierre en Seguimiento; Base lo refleja automáticamente.',9)
    set_inline(inst,'B22','Base compacta',9); set_inline(inst,'C22','Sólo el núcleo queda visible; expande grupos de columnas cuando necesites el detalle.',9)
    entries[paths['Instrucciones']]=xml_bytes(inst)

    cp=checkpoints/'04_visual_dashboard.xlsx'; write_entries(entries,cp); return cp


def verify_package(path: Path) -> dict:
    req={'Mi día','Dashboard','Base de contactos','Seguimiento comercial','Configuración','Instrucciones'}
    out={'file':str(path),'size':path.stat().st_size,'sha256':sha256(path),'zipOk':False,'xmlOk':False,'sheetNames':[], 'tables':0,'charts':0,'dataValidations':0,'formulaCount':0,'brokenRefFormulaCount':0,'definedNames':0,'errors':[]}
    try:
        with zipfile.ZipFile(path) as z:
            out['zipOk']=z.testzip() is None
            names=set(z.namelist())
            for n in names:
                if n.endswith('.xml'): ET.fromstring(z.read(n))
            out['xmlOk']=True
            wb=ET.fromstring(z.read('xl/workbook.xml'))
            out['sheetNames']=[s.attrib.get('name','') for s in wb.findall('.//m:sheet',NS)]
            out['requiredSheets']=req.issubset(out['sheetNames'])
            out['definedNames']=len(wb.findall('.//m:definedName',NS))
            out['tables']=sum(bool(re.fullmatch(r'xl/tables/table\d+\.xml',n)) for n in names)
            out['charts']=sum(bool(re.fullmatch(r'xl/charts/chart\d+\.xml',n)) for n in names)
            for n in names:
                if re.fullmatch(r'xl/worksheets/sheet\d+\.xml',n):
                    root=ET.fromstring(z.read(n))
                    out['dataValidations']+=len(root.findall('.//m:dataValidation',NS))
                    for f in root.findall('.//m:f',NS):
                        out['formulaCount']+=1
                        tx=f.text or ''
                        if any(x in tx for x in ['#REF!','#VALUE!','#NAME?','#DIV/0!']): out['brokenRefFormulaCount']+=1
            out['pass']=out['zipOk'] and out['xmlOk'] and out['requiredSheets'] and out['tables']>=2 and out['charts']>=5 and out['dataValidations']>=20 and out['formulaCount']>0 and out['brokenRefFormulaCount']==0
    except Exception as e:
        out['errors'].append(f'{type(e).__name__}: {e}'); out['pass']=False
    return out


def snapshot_summary(path: Path) -> dict:
    entries=load_entries(path); sst=get_shared_strings(entries); paths=workbook_sheet_paths(entries)
    summary={}
    for name in ['Mi día','Dashboard','Base de contactos','Seguimiento comercial']:
        root=ET.fromstring(entries[paths[name]])
        dim=root.find('m:dimension',NS).attrib.get('ref')
        cols=[c.attrib for c in root.findall('m:cols/m:col',NS)]
        summary[name]={'dimension':dim,'cols':cols[:60],'merges':[m.attrib['ref'] for m in root.findall('.//m:mergeCell',NS)][:30]}
        if name=='Mi día': summary[name]['headers']=[cell_text(root,f'{num_col(i)}9',sst) for i in range(1,15)]
        if name=='Base de contactos': summary[name]['headers']=[cell_text(root,f'{num_col(i)}6',sst) for i in range(1,col_num('AX')+1)]
        if name=='Seguimiento comercial': summary[name]['headers']=[cell_text(root,f'{num_col(i)}6',sst) for i in range(1,17)]
    return summary


def build(inp: Path, out: Path, checkpoints: Path, evidence_path: Path):
    size=inp.stat().st_size; digest=sha256(inp)
    if size!=EXPECTED_SIZE or digest!=EXPECTED_SHA:
        raise SystemExit(f'BASELINE_IDENTITY_MISMATCH size={size} sha256={digest}')
    checkpoints.mkdir(parents=True,exist_ok=True)
    entries=load_entries(inp)
    original_rows=baseline_rows(entries)
    # checkpoint 1
    cp1,unlocked=apply_guardrails(entries,checkpoints)
    # checkpoint 2
    cp2=apply_intelligence(entries,checkpoints,unlocked)
    # checkpoint 3
    cp3=apply_productivity(entries,checkpoints)
    # checkpoint 4
    cp4=apply_visual(entries,checkpoints)
    # final candidate
    out.parent.mkdir(parents=True,exist_ok=True); write_entries(entries,out)
    # reopen verification
    verify=verify_package(out)
    after_entries=load_entries(out); after_rows=baseline_rows(after_entries)
    preserved=[(r.get('ID'),r.get('Empresa'),r.get('Nombre')) for r in original_rows]==[(r.get('ID'),r.get('Empresa'),r.get('Nombre')) for r in after_rows]
    baseline_unchanged=(inp.stat().st_size==EXPECTED_SIZE and sha256(inp)==EXPECTED_SHA)
    evidence={
        'schemaVersion':'ciob.crm.v3.evidence.v1',
        'baseline':{'path':str(inp),'size':size,'sha256':digest,'unchanged':baseline_unchanged,'rowCount':len(original_rows)},
        'output':{'path':str(out),'size':out.stat().st_size,'sha256':sha256(out)},
        'checkpoints':[{'name':x.name,'size':x.stat().st_size,'sha256':sha256(x)} for x in [cp1,cp2,cp3,cp4]],
        'dataPreserved':preserved,