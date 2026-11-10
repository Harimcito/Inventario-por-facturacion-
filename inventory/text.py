"""Normalización conservadora de nombres de productos leídos de facturas."""
import re
import unicodedata
import html


def _repair_ocr_words(text: str) -> str:
    fixes = [
        (r"comisi(?:ones|[?\ufffd]nes)", "comisiones"),
        (r"\bcomisi(?:on|[?\ufffd]n|n)\b", "comisión"),
        (r"transacci(?:ones|[?\ufffd]nes)", "transacciones"),
        (r"\btransacci(?:on|[?\ufffd]n|n)\b", "transacción"),
        (r"d[?\ufffd]bito", "débito"),
        (r"cr[?\ufffd]dito", "crédito"),
        (r"m[?\ufffd]vil", "móvil"),
        (r"telef[?\ufffd]nico", "telefónico"),
        (r"\ufffdptico", "óptico"),
        (r"ergon\ufffdmico", "ergonómico"),
        (r"inal\ufffdmbrico", "inalámbrico"),
        (r"\bcomision\b", "comisión"),
        (r"\btransaccion\b", "transacción"),
        (r"debito", "débito"),
        (r"credito", "crédito"),
        (r"telefonico", "telefónico"),
        (r"optico", "óptico"),
        (r"ergonomico", "ergonómico"),
        (r"inalambrico", "inalámbrico"),
        (r"generica", "genérica"),
        (r"espaola", "española"),
        (r"magntico", "magnético"),
        (r"magnetico", "magnético"),
        (r"metalico", "metálico"),
        (r"plastico", "plástico"),
        (r"lapiz", "lápiz"),
        (r"elastico", "elástico"),
        (r"deposito", "depósito"),
        (r"swicht\s*5", "Switch 5"),
    ]
    for pattern, replacement in fixes:
        def preserve_case(match):
            if match.group(0).isupper():
                return replacement.upper()
            if match.group(0)[:1].isupper():
                return replacement.capitalize()
            return replacement
        text = re.sub(pattern, preserve_case, text, flags=re.IGNORECASE)
    return text


def clean_product_name(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    for _ in range(3):
        decoded = html.unescape(text)
        if decoded == text:
            break
        text = decoded
    text = _repair_ocr_words(text)
    text = re.sub(r"(?<=[^\W\d_])\ufffd(?=[^\W\d_])", "", text, flags=re.UNICODE)
    text = text.replace("\ufffd", " - ")
    text = re.sub(r"(?<=[^\W\d_])[?\ufffd](?=[^\W\d_])", "", text, flags=re.UNICODE)
    tokens = text.split()
    cleaned_tokens = []
    for index, token in enumerate(tokens):
        if (token in {"?", "\ufffd"} and cleaned_tokens and index + 1 < len(tokens)
                and len(cleaned_tokens[-1]) == len(tokens[index + 1]) == 1
                and cleaned_tokens[-1].isalpha() and tokens[index + 1].isalpha()):
            continue
        cleaned_tokens.append(token)
    tokens = cleaned_tokens
    # Los OCR a veces devuelven una letra por token (p. ej. "A z u c a r").
    # Unimos solo rachas de 4+ letras sueltas, dejando intactas las palabras normales.
    output = []
    index = 0
    while index < len(tokens):
        if len(tokens[index]) == 1 and tokens[index].isalpha():
            end = index + 1
            while end < len(tokens) and len(tokens[end]) == 1 and tokens[end].isalpha():
                # Preserve a separate trailing product variant such as "A" in
                # "P r o d u c t o A" instead of turning it into "ProductoA".
                if (end - index >= 4 and tokens[end].isupper()
                        and any(token.islower() for token in tokens[index:end])):
                    break
                end += 1
            if end - index >= 4:
                output.append("".join(tokens[index:end]))
                index = end
                continue
        output.append(tokens[index])
        index += 1
    text = " ".join(output)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    text = re.sub(r"[\x00-\x1f\x7f]", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" ?\ufffd")
    return text[:250]


def display_product_name(value: str) -> str:
    """Nombre legible para tablas, respetando códigos y siglas cortas."""
    text = clean_product_name(value)
    if not text:
        return text
    if not (text.isupper() or text.islower()):
        connectors = {"de", "del", "la", "las", "el", "los", "en", "con", "por", "para", "y"}
        parts = text.split()
        text = " ".join(part.lower() if i and part.casefold().strip(".,;:") in connectors else part
                         for i, part in enumerate(parts))
        return re.sub(r"\b[a-zA-Z]{1,6}(?:-[a-zA-Z0-9]{1,8}){1,3}\b", lambda m: m.group(0).upper(), text)
    keep_upper = {"USB", "DPI", "BT", "A3", "A4", "HDMI", "LED", "SSD", "RAM", "PC", "TV", "EQ", "HJS", "KL", "MT", "CM", "MM", "GR", "GRS", "COL", "MTS"}
    connectors = {"de", "del", "la", "las", "el", "los", "en", "con", "por", "para", "y"}
    def format_part(part: str) -> str:
        if not part:
            return part
        if any(ch.isdigit() for ch in part) or part.upper() in keep_upper:
            return part
        if part.casefold() in connectors:
            return part.casefold()
        if part.isupper() and len(part) <= 3:
            return part.lower() if part.casefold() in {"de", "del", "la", "las", "el", "los", "en", "con", "por", "para", "y"} else part
        return part[:1].upper() + part[1:].lower()
    text = re.sub(r"[A-Za-zÁÉÍÓÚÑÜáéíóúñü]+|[A-Za-z0-9][A-Za-z0-9+./-]*",
                  lambda m: format_part(m.group(0)), text)
    return re.sub(r"\b[a-zA-Z]{1,6}(?:-[a-zA-Z0-9]{1,8}){1,3}\b", lambda m: m.group(0).upper(), text)


def normalize_product_key(value: str) -> str:
    """Clave comparable: ignora tildes, mayúsculas y separadores OCR comunes."""
    text = unicodedata.normalize("NFKD", clean_product_name(value).casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]", "", text)


def normalize_supplier(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or "")).casefold()
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]", "", value)


def normalize_rut(value: str) -> str:
    return re.sub(r"[^0-9kK]", "", str(value or "")).upper()

