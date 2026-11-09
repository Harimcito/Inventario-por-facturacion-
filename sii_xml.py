"""Importación robusta de XML DTE del SII para revisión de inventario."""
from decimal import Decimal, InvalidOperation
import xml.etree.ElementTree as ET

def _local(tag):
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag.split(":")[-1]

def _child(node, name):
    return next((x for x in list(node) if _local(x.tag) == name), None) if node is not None else None

def _text(node, name, default=""):
    x = _child(node, name)
    return (x.text or "").strip() if x is not None else default

def _decimal(value, default=Decimal("0")):
    try:
        return Decimal((value or "").replace(",", ".").strip())
    except (InvalidOperation, AttributeError):
        return default

def parse_dtes(xml_bytes):
    """Devuelve un registro por DTE; no ejecuta ni resuelve entidades externas."""
    parser = ET.XMLParser()
    root = ET.fromstring(xml_bytes, parser=parser)
    dtes = [node for node in root.iter() if _local(node.tag) == "DTE"
            and _child(node, "Documento") is not None]
    if _local(root.tag) == "DTE" and not dtes:
        dtes = [root]
    results = []
    seen = set()
    for dte in dtes:
        doc = _child(dte, "Documento")
        header = _child(doc, "Encabezado")
        if header is None:
            continue
        iddoc = _child(header, "IdDoc")
        issuer = _child(header, "Emisor")
        totals = _child(header, "Totales")
        supplier = _text(issuer, "RznSoc") or _text(issuer, "RznSocEmisor") or _text(issuer, "RUTEmisor")
        number = _text(iddoc, "Folio")
        kind = _text(iddoc, "TipoDTE")
        key = (supplier, number, kind)
        if key in seen:
            continue
        seen.add(key)
        rows = []
        for line in list(doc):
            if _local(line.tag) != "Detalle":
                continue
            name = _text(line, "NmbItem")
            desc = _text(line, "DscItem")
            qty = _decimal(_text(line, "QtyItem"), Decimal("1"))
            unit = _decimal(_text(line, "PrcItem"))
            amount = _decimal(_text(line, "MontoItem"))
            if not unit and qty:
                unit = amount / qty
            if name:
                rows.append({"nombre": (name + (" — " + desc if desc else ""))[:250],
                             "cantidad": float(qty), "costo_unitario": int(unit.quantize(Decimal("1")))})
        results.append({
            "proveedor": supplier,
            "rut": _text(issuer, "RUTEmisor"),
            "tipo": kind,
            "numero": number,
            "fecha": _text(iddoc, "FchEmis"),
            "total": _text(totals, "MntTotal"),
            "productos": rows
        })
    if not results:
        raise ValueError("No se encontraron nodos DTE con Documento y Encabezado.")
    return results
