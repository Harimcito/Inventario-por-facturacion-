"""Persistencia SQLite y operaciones de inventario."""
import sqlite3
from pathlib import Path


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
      filename TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS movements(
      id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id),
      receipt_id INTEGER NOT NULL REFERENCES receipts(id), quantity INTEGER NOT NULL,
      unit_cost INTEGER NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_receipts_folio ON receipts(supplier, invoice_no);
    CREATE INDEX IF NOT EXISTS idx_movements_receipt ON movements(receipt_id);
    """)
    return con


def record_receipt(con, receipt: dict, items: list[dict], document_path: Path) -> int:
    """Registra factura, líneas y aumento de stock en una transacción."""
    supplier = receipt.get("supplier", "").strip()
    number = receipt.get("number", "").strip()
    if not supplier:
        raise ValueError("Indica el proveedor antes de confirmar.")
    if not items or any(not str(i.get("nombre", "")).strip() for i in items):
        raise ValueError("Completa el nombre de todos los productos.")
    if any(int(i["cantidad"]) <= 0 for i in items):
        raise ValueError("Las unidades deben ser mayores que cero.")
    existing = con.execute(
        "SELECT id FROM receipts WHERE supplier=? AND invoice_no=? AND invoice_no<>''",
        (supplier, number),
    ).fetchone() if number else None
    if existing:
        raise ValueError("Este folio del proveedor ya está registrado; no se modificó el stock.")
    document_path.parent.mkdir(parents=True, exist_ok=True)
    with document_path.open("xb") as output:
        output.write(receipt["bytes"])
    try:
        with con:
            cur = con.execute(
                "INSERT INTO receipts(supplier,invoice_no,doc_date,filename) VALUES(?,?,?,?)",
                (supplier, number, str(receipt["date"]), receipt.get("source_name", "")),
            )
            receipt_id = cur.lastrowid
            for item in items:
                name = str(item["nombre"]).strip()
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
