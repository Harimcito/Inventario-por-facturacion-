import os, re, json, sqlite3
from pathlib import Path
from datetime import date
import streamlit as st
from PIL import Image
import pytesseract
import pypdfium2 as pdfium
from sii_xml import parse_dtes

ROOT=Path(__file__).parent
DB=ROOT/"inventario.db"
DOCS=ROOT/"documentos"; DOCS.mkdir(exist_ok=True)

def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
 c.executescript("""
 CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY,name TEXT UNIQUE,category TEXT DEFAULT '',stock INTEGER DEFAULT 0,cost INTEGER DEFAULT 0,margin REAL DEFAULT 30,active INTEGER DEFAULT 1);
 CREATE TABLE IF NOT EXISTS receipts(id INTEGER PRIMARY KEY,supplier TEXT,invoice_no TEXT,doc_date TEXT,filename TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
 CREATE TABLE IF NOT EXISTS movements(id INTEGER PRIMARY KEY,product_id INTEGER,receipt_id INTEGER,quantity INTEGER,unit_cost INTEGER,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
 """); return c

def images(data,name):
 if name.lower().endswith(".pdf"):
  pdf=pdfium.PdfDocument(data); return [p.render(scale=1.7).to_pil().convert("RGB") for p in pdf]
 return [Image.open(__import__("io").BytesIO(data)).convert("RGB")]

def local_ocr(data,name):
 return "\n".join(pytesseract.image_to_string(im,lang="spa+eng") for im in images(data,name))

def openai_extract(data,name):
 from openai import OpenAI
 client=OpenAI(api_key=st.secrets.get("OPENAI_API_KEY",os.getenv("OPENAI_API_KEY")))
 chunks=[]
 for im in images(data,name):
  import base64, io
  b=io.BytesIO(); im.thumbnail((1800,1800)); im.save(b,format="JPEG",quality=82)
  chunks.append({"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+base64.b64encode(b.getvalue()).decode()}})
 prompt="""Lee esta factura/boleta chilena. Devuelve SOLO JSON: {proveedor, numero, fecha(YYYY-MM-DD o vacío), productos:[{nombre,cantidad(unidades enteras),costo_unitario(entero CLP)}]}. No inventes valores: usa vacío o 0 si no se distingue. Divide cajas solo si el documento indica unidades claramente."""
 res=client.chat.completions.create(model="gpt-4o-mini",messages=[{"role":"user","content":[{"type":"text","text":prompt},*chunks]}],response_format={"type":"json_object"},max_tokens=3000)
 return json.loads(res.choices[0].message.content)

st.set_page_config(page_title="Inventario Gioval",page_icon="📦",layout="wide")
st.markdown("<style>.block-container{max-width:1280px;padding:1.25rem 1.5rem 3rem}h1{font-size:clamp(1.65rem,4.2vw,2.25rem);line-height:1.15}[data-testid=stMetric]{background:rgba(128,128,128,.11);border:1px solid rgba(128,128,128,.24);padding:14px 16px;border-radius:14px}section[data-testid=stSidebar]{background:rgb(14,17,23)}</style>",unsafe_allow_html=True)
con=db()
st.sidebar.title("📦 Inventario")
page=st.sidebar.radio("Secciones",["Resumen","Revisar documentos","Productos","Movimientos"])
st.sidebar.caption("Cada documento afecta el stock solo después de confirmarlo.")
if page=="Resumen":
 st.title("Inventario de mercadería"); st.caption("Compras revisadas, stock y precios sugeridos.")
 ps=con.execute("select * from products where active=1 order by name").fetchall()
 docs=con.execute("select count(*) n from receipts").fetchone()["n"]
 a,b,c,d=st.columns(4); a.metric("Productos",len(ps)); b.metric("Unidades",sum(p["stock"] for p in ps)); c.metric("Documentos",docs); d.metric("Stock bajo",sum(p["stock"]<=3 for p in ps))
 st.subheader("Stock actual")
 if ps: st.dataframe([{"Producto":p["name"],"Categoría":p["category"],"Stock":p["stock"],"Costo":p["cost"],"Margen %":p["margin"],"Precio sugerido":round(p["cost"]*(1+p["margin"]/100))} for p in ps],use_container_width=True,hide_index=True)
 else: st.info("Agrega productos desde Productos o desde la revisión de una compra.")
elif page=="Revisar documentos":
 st.title("Facturas y boletas"); st.caption("Carga en lote. El OCR crea un borrador separado para cada archivo; revisa y confirma cada uno.")
 uploads=st.file_uploader("Selecciona varios PDF o imágenes",type=["pdf","png","jpg","jpeg","xml"],accept_multiple_files=True)
 if uploads and st.button(f"Preparar {len(uploads)} documento(s)",type="primary"):
  q=st.session_state.setdefault("queue",{})
  for f in uploads:
   data=f.getvalue()
   if f.name.lower().endswith(".xml"):
    try:
     for idx,dte in enumerate(parse_dtes(data),1):
      label=f"{dte['proveedor'] or 'Proveedor'} - F{dte['numero'] or idx} ({idx}).xml"
      label=re.sub(r"[^A-Za-z0-9ÁÉÍÓÚáéíóúÑñ._() -]","_",label)[:160]
      q.setdefault(label,{"bytes":data,"source_name":f.name,"supplier":dte["proveedor"],"number":dte["numero"],
       "date":date.fromisoformat(dte["fecha"]) if dte["fecha"] else date.today(),"items":dte["productos"],"raw":"","dte":True,"total":dte["total"]})
    except Exception as e: st.error(f"No pude leer {f.name}: {e}")
   elif f.name not in q:
    q[f.name]={"bytes":data,"source_name":f.name,"supplier":"","number":"","date":date.today(),"items":[],"raw":"","dte":False}
  st.rerun()
 q=st.session_state.setdefault("queue",{})
 if q:
  name=st.selectbox("Documento por revisar",list(q),format_func=lambda n:"🟠 "+n); item=q[name]
  x,y=st.columns([1,1.2],gap="large")
  with x:
   st.subheader("Original")
   if name.lower().endswith((".jpg",".jpeg",".png")): st.image(item["bytes"],use_container_width=True)
   else: st.download_button("Descargar / abrir PDF",item["bytes"],file_name=name)
   if item.get("dte"):
    st.success("XML DTE leído localmente desde los datos estructurados del SII.")
    if item.get("total"): st.caption(f"Total declarado en el documento: $ {item['total']}")
   else:
    engine=st.radio("Lectura",["OCR local (Tesseract)","OpenAI opcional"],horizontal=False,key="engine"+name)
    if st.button("Leer documento",key="ocr"+name):
     try:
      if engine=="OCR local (Tesseract)":
       text=local_ocr(item["bytes"],name); item["raw"]=text
       item["supplier"]=item["supplier"] or (text.splitlines()[0][:100] if text.strip() else "")
       st.warning("OCR extrajo texto. Revisa los campos y las líneas manualmente.")
      else:
       data=openai_extract(item["bytes"],name)
       item["supplier"]=data.get("proveedor",""); item["number"]=data.get("numero","")
       try: item["date"]=date.fromisoformat(data.get("fecha",""))
       except: pass
       item["items"]=data.get("productos",[])
       st.success("Lectura asistida lista. Confirma cada campo.")
     except Exception as e:
      st.error("No se pudo leer. Comprueba el motor local o la clave OPENAI_API_KEY. Detalle: "+str(e)[:300])
    if item["raw"]:
     with st.expander("Texto OCR local"): st.text(item["raw"])
  with y:
   st.subheader("Revisión editable")
   item["supplier"]=st.text_input("Proveedor",item["supplier"],key="s"+name)
   item["number"]=st.text_input("Número del documento",item["number"],key="n"+name)
   item["date"]=st.date_input("Fecha",value=item["date"],key="d"+name)
   catalog=con.execute("select id,name from products where active=1 order by name").fetchall()
   names=[p["name"] for p in catalog]
   if not item["items"]: item["items"]=[{"nombre":"","cantidad":1,"costo_unitario":0}]
   st.markdown("**Productos del documento**")
   changed=[]
   for i,r in enumerate(item["items"]):
    aa,bb,cc=st.columns([3,1,1.3])
    with aa: nm=st.text_input(f"Producto {i+1}",r.get("nombre",""),key=f"nm{name}{i}")
    with bb: qty=st.number_input("Unidades (enteras)",0.0,100000.0,float(r.get("cantidad") or 1),step=1.0,key=f"qt{name}{i}")
    with cc: cost=st.number_input("Costo unitario",0,100000000,int(r.get("costo_unitario") or 0),key=f"cs{name}{i}")
    changed.append({"nombre":nm,"cantidad":qty,"costo_unitario":cost})
   item["items"]=changed
   if st.button("＋ Agregar línea",key="add"+name): item["items"].append({"nombre":"","cantidad":1,"costo_unitario":0}); st.rerun()
   if st.button("Confirmar documento e ingresar al stock",type="primary",key="ok"+name):
    if not all(r["nombre"].strip() for r in changed): st.error("Completa el nombre de cada producto.")
    elif any(float(r["cantidad"]) % 1 for r in changed): st.error("El inventario usa unidades enteras. Corrige cantidades fraccionarias antes de confirmar.")
    else:
     prior=con.execute("select id from receipts where supplier=? and invoice_no=?",(item["supplier"],item["number"])).fetchone() if item["number"] else None
     if prior: st.error("Este proveedor y folio ya están registrados; no se modificó el stock.")
     else:
      rid=con.execute("insert into receipts(supplier,invoice_no,doc_date,filename) values(?,?,?,?)",(item["supplier"],item["number"],str(item["date"]),item.get("source_name",name))).lastrowid
      for r in changed:
       row=con.execute("select id from products where name=?",(r["nombre"].strip(),)).fetchone()
       if not row:
        con.execute("insert into products(name,stock,cost) values(?,?,?)",(r["nombre"].strip(),0,r["costo_unitario"]))
        row=con.execute("select id from products where name=?",(r["nombre"].strip(),)).fetchone()
       con.execute("update products set stock=stock+?,cost=? where id=?",(int(r["cantidad"]),r["costo_unitario"],row["id"]))
       con.execute("insert into movements(product_id,receipt_id,quantity,unit_cost) values(?,?,?,?)",(row["id"],rid,int(r["cantidad"]),r["costo_unitario"]))
      import uuid
      (DOCS/(uuid.uuid4().hex+"_"+Path(item.get("source_name",name)).name)).write_bytes(item["bytes"])
      con.commit(); del q[name]; st.success("Confirmado; stock actualizado."); st.rerun()
   if st.button("Eliminar de la bandeja",key="del"+name): del q[name]; st.rerun()
 else: st.info("Selecciona uno o más documentos para empezar.")
elif page=="Productos":
 st.title("Productos"); st.caption("Stock por unidades; margen editable por producto.")
 with st.expander("＋ Nuevo producto"):
  with st.form("new"):
   n=st.text_input("Nombre"); cat=st.text_input("Categoría"); stock=st.number_input("Stock",0,100000,0); cost=st.number_input("Costo",0,100000000,0); margin=st.number_input("Margen sobre costo (%)",0.,10000.,30.)
   if st.form_submit_button("Guardar") and n.strip():
    try: con.execute("insert into products(name,category,stock,cost,margin) values(?,?,?,?,?)",(n,cat,stock,cost,margin)); con.commit(); st.rerun()
    except sqlite3.IntegrityError: st.error("Ese producto ya existe.")
 ps=con.execute("select * from products order by name").fetchall()
 if ps: st.dataframe([{"Producto":p["name"],"Categoría":p["category"],"Stock":p["stock"],"Costo":p["cost"],"Margen %":p["margin"],"Precio sugerido":round(p["cost"]*(1+p["margin"]/100))} for p in ps],use_container_width=True,hide_index=True)
 if ps:
  with st.expander("Editar stock, categoría, costo y margen"):
   p=st.selectbox("Producto",ps,format_func=lambda p:p["name"])
   with st.form("edit"):
    cat=st.text_input("Categoría",p["category"]); stock=st.number_input("Stock",0,100000,p["stock"]); cost=st.number_input("Costo",0,100000000,p["cost"]); margin=st.number_input("Margen %",0.,10000.,float(p["margin"]))
    if st.form_submit_button("Guardar cambios"):
     con.execute("update products set category=?,stock=?,cost=?,margin=? where id=?",(cat,stock,cost,margin,p["id"])); con.commit(); st.rerun()
elif page=="Movimientos":
 st.title("Movimientos"); rows=con.execute("select m.created_at,p.name,r.supplier,r.invoice_no,r.filename,m.quantity,m.unit_cost from movements m join products p on p.id=m.product_id join receipts r on r.id=m.receipt_id order by m.id desc").fetchall()
 if rows: st.dataframe([dict(r) for r in rows],use_container_width=True,hide_index=True)
 else: st.info("Aún no hay movimientos.")
