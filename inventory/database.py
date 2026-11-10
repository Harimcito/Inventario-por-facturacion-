"""Persistencia SQLite y operaciones de inventario."""
import sqlite3
from pathlib import Path

from inventory.text import clean_product_name, normalize_rut, normalize_supplier


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path, timeout=20)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    con.executescript("""
    CREATE TABLE IF NOT EXISTS products(
      id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, category TEXT DEFAULT '',
      stock INTEGER NOT NULL DEFAULT 0, cost INTEGER NOT NULL DEFAULT 0,
      margin REAL NOT NULL DEFAULT 30, active INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS receipts(
      id INTEGER PRIMARY KEY, supplier TEXT, invoice_no TEXT, doc_date TEXT,
      filename TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      rut TEXT DEFAULT '', doc_type TEXT DEFAULT '', duplicate_of INTEGER
    );
    CREATE TABLE IF NOT EXISTS movements(
      id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id),
      receipt_id INTEGER NOT NULL REFERENCES receipts(id), quantity INTEGER NOT NULL,
      unit_cost INTEGER NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_receipts_folio ON receipts(supplier, invoice_no);
    CREATE INDEX IF NOT EXISTS idx_movements_receipt ON movements(receipt_id);
    """)
    receipt_columns = {row[1] for row in con.execute("PRAGMA table_info(receipts)")}
    for column, definition in (("rut", "TEXT DEFAULT ''"), ("doc_type", "TEXT DEFAULT ''"),
                               ("duplicate_of", "INTEGER")):
        if column not in receipt_columns:
            con.execute(f"ALTER TABLE receipts ADD COLUMN {column} {definition}")
    con.execute("CREATE INDEX IF NOT EXISTS idx_receipts_duplicate ON receipts(duplicate_of)")
    return con


def find_duplicate(con, receipt: dict):
    """Busca un DTE ya registrado, tolerando cambios menores en razón social."""
    number = str(receipt.get("number", "")).strip()
    if not number:
        return None
    candidates = con.execute(
        "SELECT * FROM receipts WHERE invoice_no=? AND duplicate_of IS NULL ORDER BY id",
        (number,),
    ).fetchall()
    rut = normalize_rut(receipt.get("rut", ""))
    supplier = normalize_supplier(receipt.get("supplier", ""))
    doc_type = str(receipt.get("kind", "")).strip()
    for candidate in candidates:
        existing_type = str(candidate["doc_type"] or "").strip()
        if doc_type and existing_type and doc_type != existing_type:
            continue
        existing_rut = normalize_rut(candidate["rut"] or "")
        if rut and existing_rut:
            if rut == existing_rut:
                return candidate
            continue
        if supplier and supplier == normalize_supplier(candidate["supplier"] or ""):
            return candidate
    return None


def record_receipt(con, receipt: dict, items: list[dict], document_path: Path,
                   duplicate_of: int | None = None) -> int:
    """Registra factura; una copia marcada como repetida no crea stock ni movimientos."""
    supplier = str(receipt.get("supplier", "")).strip()
    number = str(receipt.get("number", "")).strip()
    if not supplier:
        raise ValueError("Indica el proveedor antes de confirmar.")
    duplicate = find_duplicate(con, receipt)
    if duplicate and duplicate_of is None:
        raise ValueError("Esta factura ya está registrada. Puedes archivarla como repetida sin cambiar el stock.")
    if duplicate_of is not None and (not duplicate or duplicate["id"] != duplicate_of):
        raise ValueError("La factura repetida no coincide con el documento original registrado.")
    if duplicate_of is None:
        if not items or any(not str(i.get("nombre", "")).strip() for i in items):
            raise ValueError("Completa el nombre de todos los productos.")
        if any(int(i["cantidad"]) <= 0 for i in items):
            raise ValueError("Las unidades deben ser mayores que cero.")

    document_path.parent.mkdir(parents=True, exist_ok=True)
    with document_path.open("xb") as output:
        output.write(receipt["bytes"])
    try:
        with con:
            cur = con.execute(
                """INSERT INTO receipts(supplier,invoice_no,doc_date,filename,rut,doc_type,duplicate_of)
                   VALUES(?,?,?,?,?,?,?)""",
                (supplier, number, str(receipt["date"]), receipt.get("source_name", ""),
                 receipt.get("rut", ""), receipt.get("kind", ""), duplicate_of),
            )
            receipt_id = cur.lastrowid
            if duplicate_of is not None:
                return receipt_id
            for item in items:
                name = clean_product_name(item["nombre"])
                if not name:
                    raise ValueError("El nombre del producto quedó vacío después de limpiarlo.")
                qty, cost = int(item["cantidad"]), int(item.get("costo_unitario", 0))
                con.execute("INSERT OR IGNORE INTO products(name,stock,cost) VALUES(?,0,?)", (name, cost))
                product_id = con.execute("SELECT id FROM products WHERE name=?", (name,)).fetchone()["id"]
                con.execute("UPDATE products SET stock=stock+?, cost=? WHERE id=?", (qty, cost, product_id))
                con.execute(
                    "INSERT INTO movements(product_id,receipt_id,quantity,unit_cost) VALUES(?,?,?,?)",
                    (product_id, receipt_id, qty, cost),
                )
    except Exception:
        document_path.unlink(missing_ok=True)
        raise
    return receipt_id
