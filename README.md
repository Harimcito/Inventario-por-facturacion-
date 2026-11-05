# Inventario por facturación

Aplicación Streamlit para revisar facturas y boletas, registrar stock por unidades y mantener costo/margen por producto.

## Ejecutar en Windows

1. Instala Python 3.10 o superior.
2. Instala Tesseract OCR con idiomas español e inglés y verifica que `tesseract` esté en PATH.
3. Ejecuta `pip install -r requirements.txt`.
4. En la carpeta del proyecto, ejecuta `streamlit run app.py`.

## Flujo de documentos

Carga varios PDF o imágenes; cada archivo entra como documento separado en la bandeja. El OCR local Tesseract extrae texto. Puedes optar manualmente por OpenAI para leer proveedor, folio, fecha y líneas de productos con más estructura; eso envía el documento a OpenAI y puede generar consumo de API. Configura `OPENAI_API_KEY` como variable de entorno o secreto de Streamlit. Nunca pongas la clave en el código.

Revisa/edita todos los campos y confirma cada documento por separado. El stock solo cambia al confirmar. El registro guarda movimientos ligados al documento.

## Importante

La extracción OCR es un borrador: confirma nombres, unidades y costos contra el original. Tesseract extrae texto, pero no entiende de forma fiable las tablas de todas las facturas; la opción OpenAI intenta estructurar esas líneas. La app guarda la base local en `inventario.db` y documentos confirmados en `documentos/`; no subas esos datos comerciales al repositorio.

El precio sugerido usa markup sobre costo: `costo × (1 + margen/100)`. El margen se edita por producto.
