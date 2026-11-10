"""Normalización conservadora de nombres de productos leídos de facturas."""
import re
import unicodedata


def clean_product_name(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
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


def normalize_supplier(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or "")).casefold()
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]", "", value)


def normalize_rut(value: str) -> str:
    return re.sub(r"[^0-9kK]", "", str(value or "")).upper()
