# Inventario por facturación

Aplicación Streamlit para revisar compras, registrar stock por unidades y mantener costo/margen por producto.

## Documentos

- **XML DTE del SII:** la app identifica cada DTE dentro del archivo, extrae proveedor, RUT, tipo, folio, fecha, total y líneas del detalle. Cada factura queda en la bandeja separada para revisión. Solo la confirmación modifica stock.
- **PDF e imagen:** pueden cargarse en lote y revisarse con OCR Tesseract local o con OpenAI opcional. La opción OpenAI envía el documento a la API y puede generar consumo; no se activa sola.
- El importador XML está en `sii_xml.py`; el ejemplo de prueba anonimizado está en `samples/dte_ejemplo_sii.xml`.

El SII permite generar un archivo XML de respaldo desde Historial de DTE recibidos: [guía oficial](https://www.sii.cl/destacados/factura_electronica/guias_ayuda/como_generar_archivo_respaldo.htm). Descarga ese respaldo y cárgalo en Documentos de compra. No hace falta entregar la Clave Tributaria a esta app.

## Ejecutar en Windows

1. Instala Python 3.10 o superior.
2. Para imagen/PDF local, instala Tesseract OCR con español e inglés y verifica que `tesseract` esté en PATH.
3. Ejecuta `pip install -r requirements.txt`.
4. Ejecuta `streamlit run app.py`.

## Revisar y confirmar

Comprueba nombres, cantidades enteras y costos del detalle antes de confirmar. El importador muestra costo unitario XML y total del documento; confirma tratamiento del costo según tu criterio contable. Se bloquean folios ya registrados para evitar sumar stock dos veces.

La app guarda base en `inventario.db` y XML/documentos confirmados en `documentos/`; esos datos comerciales deben permanecer fuera de GitHub. El precio sugerido usa markup: `costo × (1 + margen/100)`.
