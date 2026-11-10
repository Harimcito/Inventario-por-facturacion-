"""Inicio de sesión local con hashes lentos y bloqueo tras intentos fallidos."""
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from pathlib import Path

import streamlit as st


PBKDF2_ITERATIONS = 600_000
IDLE_TIMEOUT_SECONDS = 30 * 60
LOCKOUT_SECONDS = 15 * 60
MAX_FAILED_ATTEMPTS = 5
_AUTH_LOCK = threading.RLock()


def _auth_path(root: Path) -> Path:
    return root / ".streamlit" / "auth.json"


def _read(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, OSError) as exc:
        st.error(f"No se pudo leer la configuración de acceso ({exc}).")
        st.stop()


def _write(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(temporary, 0o600)
    except OSError:
        pass
    os.replace(temporary, path)


def _password_hash(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS).hex()


def _valid_password(password: str) -> bool:
    return len(password) >= 12


def render_login(root: Path) -> bool:
    """Muestra configuración inicial o login; devuelve True solo con sesión válida."""
    path = _auth_path(root)
    now = time.time()
    with _AUTH_LOCK:
        account = _read(path)

    if account is None:
        st.markdown("### Configura el acceso privado")
        st.write("Crea el usuario y la contraseña que protegerán este inventario. La contraseña se guarda como hash local.")
        with st.form("initial_account", clear_on_submit=False):
            username = st.text_input("Usuario", autocomplete="username")
            password = st.text_input("Contraseña", type="password", autocomplete="new-password")
            confirmation = st.text_input("Repite la contraseña", type="password", autocomplete="new-password")
            submitted = st.form_submit_button("Crear acceso", type="primary")
        if submitted:
            normalized = username.strip()
            if len(normalized) < 3:
                st.error("El usuario debe tener al menos 3 caracteres.")
            elif not _valid_password(password):
                st.error("Usa una contraseña de al menos 12 caracteres.")
            elif password.casefold() == normalized.casefold():
                st.error("La contraseña no puede ser igual al usuario.")
            elif password != confirmation:
                st.error("Las contraseñas no coinciden.")
            else:
                salt = secrets.token_bytes(16)
                new_account = {
                    "username": normalized, "salt": salt.hex(),
                    "password_hash": _password_hash(password, salt),
                    "iterations": PBKDF2_ITERATIONS, "version": 1,
                    "failed_attempts": 0, "locked_until": 0,
                }
                with _AUTH_LOCK:
                    if _read(path) is not None:
                        st.error("El acceso ya fue configurado. Inicia sesión con tu usuario.")
                    else:
                        _write(path, new_account)
                        st.success("Acceso creado. Inicia sesión para continuar.")
                        st.rerun()
        return False

    if (st.session_state.get("_inventory_authenticated")
            and st.session_state.get("_inventory_auth_version") == account.get("version")
            and now - st.session_state.get("_inventory_last_activity", 0) < IDLE_TIMEOUT_SECONDS):
        st.session_state["_inventory_last_activity"] = now
        return True
    st.session_state.pop("_inventory_authenticated", None)
    st.session_state.pop("_inventory_auth_version", None)
    st.session_state.pop("_inventory_last_activity", None)

    st.markdown("### Iniciar sesión")
    st.write("Ingresa tus credenciales para abrir el inventario.")
    locked_for = max(0, int(account.get("locked_until", 0) - now))
    if locked_for:
        st.warning(f"Acceso temporalmente bloqueado. Vuelve a intentar en {locked_for // 60 + 1} min.")
        return False
    with st.form("inventory_login", clear_on_submit=True):
        username = st.text_input("Usuario", autocomplete="username")
        password = st.text_input("Contraseña", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Entrar", type="primary")
    if not submitted:
        return False

    with _AUTH_LOCK:
        account = _read(path)
        if account is None:
            st.rerun()
        if account.get("locked_until", 0) > now:
            st.warning("Acceso temporalmente bloqueado. Intenta más tarde.")
            return False
        salt = bytes.fromhex(account["salt"])
        expected = _password_hash(password, salt)
        valid = (username.strip().casefold() == account["username"].casefold()
                 and hmac.compare_digest(expected, account["password_hash"]))
        if valid:
            account["failed_attempts"] = 0
            account["locked_until"] = 0
            _write(path, account)
        else:
            account["failed_attempts"] = int(account.get("failed_attempts", 0)) + 1
            if account["failed_attempts"] >= MAX_FAILED_ATTEMPTS:
                account["failed_attempts"] = 0
                account["locked_until"] = now + LOCKOUT_SECONDS
            _write(path, account)

    if not valid:
        st.error("Usuario o contraseña incorrectos.")
        return False
    st.session_state["_inventory_authenticated"] = True
    st.session_state["_inventory_auth_version"] = account.get("version", 1)
    st.session_state["_inventory_last_activity"] = now
    st.rerun()
    return True


def render_security_sidebar(root: Path):
    path = _auth_path(root)
    with st.sidebar:
        account = _read(path) or {}
        st.caption(f"Sesión: {account.get('username', 'Usuario')}")
        st.caption("Se cierra tras 30 minutos sin actividad.")
        if st.button("Cerrar sesión", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        with st.expander("Cambiar contraseña"):
            with st.form("change_password"):
                current = st.text_input("Contraseña actual", type="password")
                new = st.text_input("Nueva contraseña", type="password")
                confirm = st.text_input("Repite la nueva contraseña", type="password")
                submitted = st.form_submit_button("Actualizar contraseña")
            if submitted:
                with _AUTH_LOCK:
                    account = _read(path)
                    expected = _password_hash(current, bytes.fromhex(account["salt"]))
                    if not hmac.compare_digest(expected, account["password_hash"]):
                        st.error("La contraseña actual no coincide.")
                    elif not _valid_password(new):
                        st.error("Usa una contraseña de al menos 12 caracteres.")
                    elif new.casefold() == account["username"].casefold():
                        st.error("La contraseña no puede ser igual al usuario.")
                    elif new != confirm:
                        st.error("Las contraseñas nuevas no coinciden.")
                    else:
                        salt = secrets.token_bytes(16)
                        account.update({
                            "salt": salt.hex(), "password_hash": _password_hash(new, salt),
                            "iterations": PBKDF2_ITERATIONS,
                            "version": int(account.get("version", 1)) + 1,
                            "failed_attempts": 0, "locked_until": 0,
                        })
                        _write(path, account)
                        st.session_state["_inventory_auth_version"] = account["version"]
                        st.success("Contraseña actualizada. Las otras sesiones deberán volver a iniciar sesión.")
