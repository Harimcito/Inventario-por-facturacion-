# Inventario por facturación

Aplicación sencilla para un usuario, adaptable a computador y teléfono, pensada para 10–15 facturas/boletas mensuales de 5–6 proveedores.

## Estado

Prototipo inicial en Streamlit y SQLite. Permite mantener productos en unidades, stock, costo unitario, margen editable por producto y precio sugerido; admite registrar una compra con datos revisados manualmente y conserva cabecera y movimientos en base local.

## Ejecutar en Windows

1. Instalar Python 3.10+.
2. En una terminal: `pip install -r requirements.txt`
3. Ejecutar: `streamlit run app.py`

## Decisiones y siguientes pasos

- Flujo objetivo: cargar PDF/imagen → extraer proveedor, número, fecha y líneas como borrador → revisar/editar → confirmar movimiento → actualizar stock.
- Este primer prototipo todavía no implementa OCR, almacenamiento del archivo original ni exportación Excel. No confirma automáticamente datos extraídos.
- Para OCR, probar primero los documentos reales de los 5–6 proveedores y elegir una opción de bajo costo; incorporar proveedor/fecha/número y productos con confianza por campo.
- Añadir revisión de duplicados por proveedor + número de documento, edición de movimientos, historial auditable, respaldo y exportación XLSX.
- Mantener el archivo de datos fuera del repositorio. SQLite local es simple para un único usuario; para acceso sincronizado desde distintos dispositivos se requiere alojar la app y base de datos/archivos en un servicio con almacenamiento persistente. No sincronizar SQLite mediante carpetas compartidas en nube.
- El margen actual es markup sobre costo: precio = costo × (1 + margen/100). Si se desea margen bruto sobre precio de venta, la fórmula cambia y debe decidirse antes de usar precios como definitivos.

Se revisará la lectura OCR y el despliegue después de definir presupuesto de alojamiento y método de acceso desde ambos dispositivos.
