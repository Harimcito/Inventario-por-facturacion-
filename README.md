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
