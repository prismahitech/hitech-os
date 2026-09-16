#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re, sys, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
M='http://schemas.openxmlformats.org/spreadsheetml/2006/main'; R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'; PR='http://schemas.openxmlformats.org/package/2006/relationships'
NS={'m':M,'r':R}
EXPECTED_SIZE=159678; EXPECTED_SHA='e8eb06bcf05b88500c4733a9b54b11f355ce3a7c51773b062fefafab86b27bf9'
REQ_V3_COLS={'Idioma preferido','Canal preferido','Motivo de pérdida/cierre','Días en etapa','Intentos sin respuesta','Completitud contextual %','Seguimiento sugerido','Canal sugerido','Acción sugerida V3','Control V3','Email normalizado','Tel normalizado','WA normalizado','Orden Mi día'}
REQ_NAMES={'ListaIdioma','ListaMotivoCierre','ResultadoDias','ListaResponsable','ListaCanal','ListaEstatus'}
BAD=('#REF!','#VALUE!','#NAME?','#DIV/0!')
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def sheets(z):
 wb=ET.fromstring(z.read('xl/workbook.xml')); rel=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
 mp={x.attrib['Id']:x.attrib['Target'] for x in rel.findall(f'{{{PR}}}Relationship')}
 return {s.attrib['name']:'xl/'+mp[s.attrib[f'{{{R}}}id']] for s in wb.findall('.//m:sheet',NS)}
def shared(z):
 root=ET.fromstring(z.read('xl/sharedStrings.xml')); return [''.join(t.text or '' for t in si.findall('.//m:t',NS)) for si in root.findall('m:si',NS)]
def ctext(root,ref,sst):
 c=root.find(f".//m:c[@r='{ref}']",NS)
 if c is None:return ''
 if c.attrib.get('t')=='inlineStr':return ''.join(t.text or '' for t in c.findall('.//m:t',NS))
 v=c.find('m:v',NS)
 if v is None:return ''
 if c.attrib.get('t')=='s':return sst[int(v.text)]
 return v.text or ''
def _cell_map(root):
 return {c.attrib.get('r'):c for c in root.findall('.//m:c',NS)}
def _cell_value(c, ss):
 if c is None:return ''
 if c.attrib.get('t')=='inlineStr':return ''.join(t.text or '' for t in c.findall('.//m:t',NS))
 v=c.find('m:v',NS)
 if v is None or v.text is None:return ''
 if c.attrib.get('t')=='s':return ss[int(v.text)]
 return v.text or ''
def rows_signature(z):
 ss=shared(z); sp=sheets(z); root=ET.fromstring(z.read(sp['Base de contactos'])); cells=_cell_map(root); out=[]
 for r in range(7,507):
  emp=_cell_value(cells.get(f'B{r}'),ss)
  if emp: out.append((_cell_value(cells.get(f'A{r}'),ss),emp,_cell_value(cells.get(f'C{r}'),ss)))
 return out

def literal_signature(z, sheet_name, max_row, max_col, min_row=7):
 ss=shared(z); sp=sheets(z); root=ET.fromstring(z.read(sp[sheet_name])); out={}
 cells={c.attrib.get('r'):c for c in root.findall('.//m:c',NS)}
 for ref,c in cells.items():
  m=re.fullmatch(r'([A-Z]+)(\d+)',ref or '')
  if not m: continue
  cno=0
  for ch in m.group(1): cno=cno*26+ord(ch)-64
  row=int(m.group(2))
  if row<min_row or row>max_row or cno>max_col or c.find('m:f',NS) is not None: continue
  val=_cell_value(c,ss)
  if val!='': out[ref]=val
 return out

def balanced(formula):
 q=False; p=0; b=0; i=0
 while i<len(formula):
  ch=formula[i]
  if ch=='"':
   if q and i+1<len(formula) and formula[i+1]=='"': i+=2; continue
   q=not q
  elif not q:
   if ch=='(':p+=1
   elif ch==')':p-=1
   elif ch=='[':b+=1
   elif ch==']':b-=1
   if p<0 or b<0:return False
  i+=1
 return (not q) and p==0 and b==0
def main():
 if len(sys.argv)!=3: raise SystemExit('usage: verify_v3_semantics.py BASELINE FINAL')
 bp,fp=map(Path,sys.argv[1:]); checks={}; errors=[]
 checks['baselineIdentity']=bp.exists() and bp.stat().st_size==EXPECTED_SIZE and sha(bp)==EXPECTED_SHA
 if not checks['baselineIdentity']: errors.append('BASELINE_IDENTITY_MISMATCH')
 with zipfile.ZipFile(bp) as bz, zipfile.ZipFile(fp) as z:
  checks['zipIntegrity']=z.testzip() is None
  xmlok=True
  for n in z.namelist():
   if n.endswith('.xml'):
    try: ET.fromstring(z.read(n))
    except Exception as e: xmlok=False; errors.append(f'XML:{n}:{e}')
  checks['xmlIntegrity']=xmlok
  sp=sheets(z); checks['requiredSheets']=set(['Mi día','Dashboard','Base de contactos','Seguimiento comercial','Configuración','Instrucciones']).issubset(sp)
  wb=ET.fromstring(z.read('xl/workbook.xml'))
  dns={x.attrib.get('name'):(x.text or '') for x in wb.findall('.//m:definedName',NS)}
  checks['definedNames']=REQ_NAMES.issubset(dns)
  checks['dynamicCatalogNames']=all(('OFFSET(' in dns.get(n,'') or n in {'ListaIdioma','ListaMotivoCierre','ResultadoDias'}) for n in REQ_NAMES)
  calc=wb.find('m:calcPr',NS); checks['fullCalcOnLoad']=calc is not None and calc.attrib.get('fullCalcOnLoad')=='1'
  t1=ET.fromstring(z.read('xl/tables/table1.xml')); t2=ET.fromstring(z.read('xl/tables/table2.xml'))
  cols1={x.attrib.get('name') for x in t1.findall('.//m:tableColumn',NS)}; cols2={x.attrib.get('name') for x in t2.findall('.//m:tableColumn',NS)}
  checks['prospectTableRef']=t1.attrib.get('ref')=='A6:AX506'; checks['trackingTableRef']=t2.attrib.get('ref')=='A6:P1006'
  checks['v3ProspectColumns']=REQ_V3_COLS.issubset(cols1); checks['trackingClosureColumns']={'Motivo de pérdida/cierre','Cambio etapa?'}.issubset(cols2)
  t1forms={x.attrib.get('name'):(x.find('m:calculatedColumnFormula',NS).text if x.find('m:calculatedColumnFormula',NS) is not None else '') for x in t1.findall('.//m:tableColumn',NS)}
  checks['seguimientoSourceOfTruth']=all('tblSeguimiento' in t1forms.get(n,'') for n in ['Estatus','Último contacto','Próximo seguimiento','Próxima acción','Motivo de pérdida/cierre','Días en etapa','Intentos sin respuesta'])
  formulas=[]
  for n in z.namelist():
   if n.endswith('.xml'):
    root=ET.fromstring(z.read(n))
    for f in root.findall('.//m:f',NS): formulas.append((n,f.text or ''))
    for f in root.findall('.//m:calculatedColumnFormula',NS): formulas.append((n,f.text or ''))
  checks['noBrokenFormulaTokens']=not any(any(b in f for b in BAD) for _,f in formulas)
  badbal=[(n,f[:100]) for n,f in formulas if not balanced(f)]
  checks['formulaBalance']=not badbal
  if badbal: errors.append('UNBALANCED_FORMULAS:'+json.dumps(badbal[:5],ensure_ascii=False))
  base=ET.fromstring(z.read(sp['Base de contactos'])); seg=ET.fromstring(z.read(sp['Seguimiento comercial'])); mid=ET.fromstring(z.read(sp['Mi día'])); cfg=ET.fromstring(z.read(sp['Configuración']))
  dvs_base=base.findall('.//m:dataValidation',NS); dvs_seg=seg.findall('.//m:dataValidation',NS); dvs_mid=mid.findall('.//m:dataValidation',NS)
  base_sq={d.attrib.get('sqref') for d in dvs_base}; seg_sq={d.attrib.get('sqref') for d in dvs_seg}; mid_sq={d.attrib.get('sqref') for d in dvs_mid}
  checks['softContactValidations']={'H7:H506','F7:F506','G7:G506','I7:I506'}.issubset(base_sq)
  checks['newPreferenceDropdowns']={'AK7:AK506','AL7:AL506'}.issubset(base_sq)
  checks['trackingCrossValidations']='G7:G1006' in seg_sq and 'K7:K1006' in seg_sq and 'M7:M1006' in seg_sq and 'O7:O1006' in seg_sq
  checks['ownerSelector']='C5' in mid_sq
  email_dv=next((d for d in dvs_base if d.attrib.get('sqref')=='H7:H506'),None); ef=(email_dv.find('m:formula1',NS).text if email_dv is not None else '')
  checks['emailValidationSafe']='IFERROR' in ef
  checks['protectedAutomaticFields']=all(r.find('m:sheetProtection',NS) is not None for r in (base,seg,cfg))
  hidden=sum(1 for c in base.findall('m:cols/m:col',NS) if c.attrib.get('hidden')=='1'); checks['compactGroupedBase']=hidden>=20 and all(c.attrib.get('outlineLevel')=='1' for c in base.findall('m:cols/m:col',NS) if c.attrib.get('hidden')=='1')
  mid_form='\n'.join(f.text or '' for f in mid.findall('.//m:f',NS)); checks['quickActions']=all(x in mid_form for x in ['HYPERLINK','wa.me','mailto:','Seguimiento comercial'])
  checks['miDiaPriorityFormula']='Orden Mi día' in mid_form and 'AGGREGATE(15,6' in mid_form
  checks['charts']=sum(1 for n in z.namelist() if re.fullmatch(r'xl/charts/chart\d+\.xml',n))>=5
  cfgtext=' '.join(ctext(cfg,ref,shared(z)) for ref in ['AF5','AF6','AH5','AH6','AJ5','AJ6','AK6'])
  checks['configV3Catalogs']=all(x in cfgtext for x in ['Idioma','Motivo','Resultado'])
  bb=literal_signature(bz,'Base de contactos',506,36); fb=literal_signature(z,'Base de contactos',506,36); bs=literal_signature(bz,'Seguimiento comercial',1006,14); fs=literal_signature(z,'Seguimiento comercial',1006,14)
  checks['dataPreserved']=rows_signature(bz)==rows_signature(z) and len(rows_signature(z))==27 and all(fb.get(k)==v for k,v in bb.items()) and all(fs.get(k)==v for k,v in bs.items())
  checks['baselineStillUnchanged']=bp.stat().st_size==EXPECTED_SIZE and sha(bp)==EXPECTED_SHA
  raw='\n'.join((z.read(n).decode('utf-8','ignore') for n in z.namelist() if n.endswith('.xml')))
  checks['noBrokenRefsAnywhere']=not any(x in raw for x in BAD)
 passed=all(checks.values()) and not errors
 print(json.dumps({'pass':passed,'checks':checks,'errors':errors,'finalSize':fp.stat().st_size,'finalSha256':sha(fp)},ensure_ascii=False,indent=2))
 return 0 if passed else 1
if __name__=='__main__': raise SystemExit(main())