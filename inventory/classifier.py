"""Clasificación local y conservadora de líneas de factura."""
import re
import unicodedata

MERCHANDISE = "Mercadería"
SERVICE = "Servicio tecnológico/profesional"
FREIGHT = "Flete o despacho"
FEE = "Comisión o recargo"
ADJUSTMENT = "Impuesto, descuento u otro ajuste"
LINE_TYPES = [MERCHANDISE, SERVICE, FREIGHT, FEE, ADJUSTMENT]

_RULES = [
    (FEE, r"\b(comision|comisiones|cargo por|recargo|interes|intereses|gasto de cobranza|tarifa de servicio|fee|cargo bancario)\b"),
    (SERVICE, r"\b(servicio|servicios|soporte|mantencion|mantenimiento|asesoria|consultoria|instalacion|reparacion|licencia|software|suscripcion|hosting|nube|cloud|plataforma|sistema|tecnologico|tecnologia|honorario|capacitacion|desarrollo web|dominio web)\b"),
    (FREIGHT, r"\b(flete|despacho|envio|transporte|delivery|reparto|retiro|courier|logistica)\b"),
    (ADJUSTMENT, r"\b(iva|impuesto|descuento|rebaja|redondeo|ajuste|nota de credito|retencion|exento|subtotal|total factura|otros cobros|anula comprobante|anula folios|cobro)\b"),
]


def classify_line(description: str) -> tuple[str, str]:
    """Devuelve (tipo sugerido, motivo); lo no reconocido se trata como mercadería."""
    from inventory.text import clean_product_name
    text = unicodedata.normalize("NFKD", clean_product_name(description).casefold())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    for line_type, pattern in _RULES:
        if re.search(pattern, text):
            return line_type, "Detectado por descripción; confirma antes de guardar."
    return MERCHANDISE, "Sin indicador de servicio o recargo; revisar la descripción."


def suggest_product_category(description: str) -> str:
    """Sugiere una categoría útil para el catálogo sin depender de una API."""
    from inventory.text import normalize_product_key
    key = normalize_product_key(description)
    if any(term in key for term in ("papel", "foto", "carpeta", "carpc", "cartulina", "corchetera", "sacacorchete", "sacapunta",
                                    "lapiz", "formulario", "elastico", "portaclips", "portala")):
        return "Oficina y papelería"
    if any(term in key for term in ("mouse", "teclado", "keyboard", "cable", "switch", "fuentedepoder", "alargador", "usb")):
        return "Tecnología y accesorios"
    if "afilador" in key or "sierra" in key:
        return "Herramientas"
    return ""

