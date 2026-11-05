import sqlite3
from pathlib import Path
import streamlit as st

DB = Path("inventario.db")

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.executescript("""
    CREATE TABLE IF NOT EXISTS products(
      id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, category TEXT DEFAULT '',
      stock INTEGER NOT NULL DEFAULT 0, cost INTEGER NOT NULL DEFAULT 0,
      margin REAL NOT NULL DEFAULT 30, active INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS receipts(
      id INTEGER PRIMARY KEY, supplier TEXT, invoice_no TEXT, doc_date TEXT,
      filename TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS movements(
      id INTEGER PRIMARY KEY, product_id INTEGER, receipt_id INTEGER,
      quantity INTEGER NOT NULL, unit_cost INTEGER NOT NULL,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(product_id) REFERENCES products(id),
      FOREIGN KEY(receipt_id) REFERENCES receipts(id)
    );
    """)
    return con

st.set_page_config(page_title="Inventario Gioval", page_icon="📦", layout="wide")
st.title("📦 Inventario por facturación")
st.caption("Carga documentos, revisa los productos y confirma el ingreso al stock.")
tab_stock, tab_receipt, tab_rules = st.tabs(["Inventario", "Ingresar compra", "Configuración"])

with tab_stock:
    con = db()
    products = con.execute("SELECT * FROM products WHERE active=1 ORDER BY name").fetchall()
    if products:
        st.dataframe([{"Producto":p["name"],"Categoría":p["category"],"Stock":p["stock"],
          "Costo":p["cost"],"Margen %":p["margin"],"Precio sugerido":round(p["cost"]*(1+p["margin"]/100))}
          for p in products], use_container_width=True, hide_index=True)
    else: st.info("Aún no hay productos. Registra la primera compra en Ingresar compra.")
    with st.expander("Crear o editar producto"):
        with st.form("product"):
            name=st.text_input("Nombre del producto")
            category=st.text_input("Categoría")
            stock=st.number_input("Stock inicial (unidades)",min_value=0,step=1)
            cost=st.number_input("Costo unitario ($)",min_value=0,step=1)
            margin=st.number_input("Margen sobre costo (%)",min_value=0.0,value=30.0,step=1.0)
            if st.form_submit_button("Guardar producto") and name.strip():
                con.execute("INSERT INTO products(name,category,stock,cost,margin) VALUES(?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET category=excluded.category, stock=excluded.stock, cost=excluded.cost, margin=excluded.margin",
                    (name.strip(),category.strip(),stock,cost,margin)); con.commit(); st.rerun()

with tab_receipt:
    st.subheader("Documento de compra")
    uploaded=st.file_uploader("Factura o boleta (PDF, JPG, PNG)",type=["pdf","jpg","jpeg","png"])
    st.caption("Primera versión: captura asistida. Revisa y confirma cada línea antes de afectar el stock.")
    supplier=st.text_input("Proveedor")
    invoice=st.text_input("N.º de documento")
    doc_date=st.date_input("Fecha")
    con=db()
    catalog=[r["name"] for r in con.execute("SELECT name FROM products WHERE active=1 ORDER BY name")]
    n=st.number_input("Cantidad de productos",min_value=1,max_value=30,value=1)
    rows=[]
    for i in range(int(n)):
        a,b,c=st.columns([3,1,1])
        with a: product=st.selectbox(f"Producto {i+1}",["+ Nuevo producto"]+catalog,key=f"p{i}")
        with b: qty=st.number_input("Unidades",min_value=1,step=1,key=f"q{i}")
        with c: cost=st.number_input("Costo unitario",min_value=0,step=1,key=f"c{i}")
        rows.append((product,qty,cost))
    if st.button("Confirmar ingreso",type="primary",disabled=not uploaded):
        con.execute("INSERT INTO receipts(supplier,invoice_no,doc_date,filename) VALUES(?,?,?,?)",
          (supplier,invoice,str(doc_date),uploaded.name)); rid=con.execute("SELECT last_insert_rowid()").fetchone()[0]
        for product,qty,cost in rows:
            if product=="+ Nuevo producto" or not product:
                continue
            pid=con.execute("SELECT id FROM products WHERE name=?",(product,)).fetchone()[0]
            con.execute("UPDATE products SET stock=stock+?, cost=? WHERE id=?",(qty,cost,pid))
            con.execute("INSERT INTO movements(product_id,receipt_id,quantity,unit_cost) VALUES(?,?,?,?)",(pid,rid,qty,cost))
        con.commit(); st.success("Compra registrada y stock actualizado."); st.rerun()

with tab_rules:
    st.markdown("### Precio sugerido")
    st.write("Precio = costo unitario × (1 + margen / 100). El margen se configura por producto y puede editarse en Inventario.")
    st.info("La extracción automática del documento y la exportación Excel son las siguientes etapas. Este prototipo no lee el archivo todavía; requiere revisar manualmente los datos antes de confirmar.")
