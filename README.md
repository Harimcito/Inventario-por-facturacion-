# Inventario por facturación · Gioval

Aplicación local para leer facturas y boletas, revisar los productos y registrar stock por unidades.

## Acceso y contraseñas

En el primer inicio, crea tu usuario y contraseña desde la app. Se exige una contraseña de al menos 6 caracteres; se guarda un hash PBKDF2 con salt en `.streamlit/auth.json`, archivo excluido de Git. Tras 5 intentos fallidos se bloquea el acceso durante 15 minutos, las sesiones vencen luego de 30 minutos sin actividad y la contraseña se puede cambiar desde el menú lateral. Para reiniciar el acceso local, detén la app y elimina `.streamlit/auth.json`; la base de inventario no se elimina.

El iniciador escucha solo en `127.0.0.1`. Para abrir el sistema desde otro dispositivo hay que configurar acceso de red y HTTPS antes de publicarlo; el login por sí solo no cifra la conexión HTTP.

## Importación desde el SII y lectura con IA

El SII permite generar un respaldo XML de DTE recibidos. Descárgalo desde su portal y cárgalo en la app; cada factura se separa para revisar sus líneas antes de confirmar. La API key de OpenAI puede ingresarse en la vista de compras y se conserva solo en la sesión para leer PDF o imágenes. El XML se procesa localmente.

## Ejecutar en Windows

1. Instala Python 3.10 o superior y ejecuta `pip install -r requirements.txt`.
2. Para OCR local de imágenes/PDF, instala Tesseract con español e inglés.
3. Abre `abrir_inventario.ps1`. El iniciador busca un puerto libre entre 8506 y 8599; el 8501 queda reservado para Giovalia.

La base SQLite y documentos originales se guardan en local y están excluidos de Git.

## Uso diario

- En **Ingresar facturas** puedes revisar cada documento, asociar sus líneas de mercadería a productos existentes y confirmar cuando los datos estén correctos.
- El clasificador sugiere separar mercadería, servicios tecnológicos/profesionales, fletes, comisiones y ajustes. Solo **Mercadería** crea o actualiza productos y stock; las demás líneas se conservan dentro del detalle de la factura. Revisa la sugerencia y cámbiala si hace falta antes de confirmar.
- La ficha de producto incluye una descripción breve para formato o variante y nombres alternativos de proveedores. Al asociar una línea de factura a un producto existente, la descripción del proveedor se aprende como alias para sugerir la misma coincidencia la próxima vez.
- **Facturas** permite buscar por proveedor o folio, consultar las líneas reconocidas y descargar el original. Las repetidas quedan identificadas y no aumentan stock.
- En **Productos** cada producto tiene margen y mínimo de stock propio. Los cambios manuales de unidades requieren un motivo y quedan auditados en **Movimientos**.
- **Respaldo y exportación** permite descargar el catálogo como CSV y una copia ZIP de la base de datos más los documentos originales. Guarda ese ZIP en otro lugar seguro.

## Facturas duplicadas y nombres

La app compara proveedor/RUT, tipo DTE y folio. Si encuentra una factura repetida, permite archivarla como repetida: guarda el archivo y su referencia al registro original, sin crear movimientos ni aumentar stock. Las lecturas XML y OpenAI limpian signos `?` incrustados y secuencias de letras separadas. En Productos hay una vista previa para corregir nombres ya guardados; los conflictos con productos existentes se dejan sin cambio.

