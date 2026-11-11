"""Lectura de XML DTE y extracción asistida de documentos."""
import base64
import io
import json
import os
from datetime import date

from PIL import Image
import pypdfium2 as pdfium
import pytesseract

from sii_xml import parse_dtes
from inventory.text import clean_product_name, parse_invoice_quantity, parse_clp


def document_images(data: bytes, filename: str):
    if filename.lower().endswith(".pdf"):
        pdf = pdfium.PdfDocument(data)
        return [page.render(scale=1.7).to_pil().convert("RGB") for page in pdf]
    return [Image.open(io.BytesIO(data)).convert("RGB")]


def document_preview(data: bytes, filename: str):
    """Renderiza una sola página para revisión visual, incluso en PDFs extensos."""
    if filename.lower().endswith(".pdf"):
        pdf = pdfium.PdfDocument(data)
        if len(pdf) == 0:
            raise ValueError("El PDF no contiene páginas.")
        return pdf[0].render(scale=1.35).to_pil().convert("RGB"), len(pdf)
    return Image.open(io.BytesIO(data)).convert("RGB"), 1


def local_ocr(data: bytes, filename: str) -> str:
    return "\n".join(pytesseract.image_to_string(img, lang="spa+eng") for img in document_images(data, filename))


def openai_key() -> str:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if key:
        return key
    try:
        return str(__import__("streamlit").secrets.get("OPENAI_API_KEY", "")).strip()
    except Exception:
        return ""


def ai_extract(data: bytes, filename: str, api_key: str):
    from openai import OpenAI
    images = document_images(data, filename)
    contents = [{"type": "text", "text": (
        "Lee esta factura/boleta chilena y devuelve JSON con proveedor, numero, "
        "fecha YYYY-MM-DD y productos [{nombre,cantidad,costo_unitario}]. Incluye TODAS las líneas de detalle, "
        "también servicios, fletes, comisiones e impuestos/ajustes; no las omitas ni las conviertas en productos. "
        "Conserva en nombre los datos que identifican el artículo si aparecen: marca, modelo, SKU, tamaño, color, "
        "formato, sabor, presentación y cantidad del envase. No agregues información inferida. "
        "No inventes datos; usa vacío o cero cuando no se distingan. "
        "El inventario cuenta unidades enteras: no conviertas cajas sin evidencia."
    )}]
    for image in images:
        image.thumbnail((1800, 1800))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=82)
        payload = base64.b64encode(buffer.getvalue()).decode("ascii")
        contents.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{payload}"}})
    result = OpenAI(api_key=api_key).chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "user", "content": contents}],
        response_format={"type": "json_object"}, max_tokens=3000,
    )
    data = json.loads(result.choices[0].message.content)
    data["productos"] = [
        {**item, "nombre": clean_product_name(item.get("nombre", "")),
         "cantidad": parse_invoice_quantity(item.get("cantidad", 0)),
         "costo_unitario": parse_clp(item.get("costo_unitario", 0))}
        for item in data.get("productos", [])
    ]
    return data


def drafts_from_upload(filename: str, data: bytes):
    if filename.lower().endswith(".xml"):
        drafts = []
        for index, dte in enumerate(parse_dtes(data), start=1):
            try:
                doc_date = date.fromisoformat(dte["fecha"]) if dte.get("fecha") else date.today()
            except ValueError:
                doc_date = date.today()
            drafts.append({
                "bytes": data, "source_name": filename,
                "supplier": dte["proveedor"], "number": dte["numero"],
                "date": doc_date,
                "items": [{**item, "nombre": clean_product_name(item.get("nombre", ""))}
                          for item in dte["productos"]],
                "raw": "",
                "dte": True, "total": dte["total"], "rut": dte["rut"], "kind": dte["tipo"],
            })
        return drafts
    return [{"bytes": data, "source_name": filename, "supplier": "", "number": "",
             "date": date.today(), "items": [], "raw": "", "dte": False}]

