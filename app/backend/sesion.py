from functools import wraps
from flask import session, redirect, url_for, flash, g

from datos import usuario_por_id


def iniciar_sesion(usuario):
    session.clear()
    session["usuario_id"] = usuario.id
    # A propósito NO se marca la sesión como "permanente": así la cookie de
    # inicio de sesión dura solo mientras el navegador/pestaña siga abierto.
    # Al cerrar el navegador (o abrir el Codespace de nuevo más tarde) pedirá
    # usuario y contraseña otra vez, en vez de quedar conectado por semanas.


def cerrar_sesion():
    session.clear()


def usuario_actual():
    if "usuario_id" not in session:
        return None
    if not hasattr(g, "_usuario_actual"):
        g._usuario_actual = usuario_por_id(session["usuario_id"])
    return g._usuario_actual


def login_required(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if usuario_actual() is None:
            flash("Inicia sesión para continuar.", "error")
            return redirect(url_for("auth.login"))
        return vista(*args, **kwargs)
    return envoltura


def admin_required(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        u = usuario_actual()
        if u is None:
            flash("Inicia sesión para continuar.", "error")
            return redirect(url_for("auth.login"))
        if u.rol != "comisariado":
            flash("No tienes permisos para acceder a esta sección.", "error")
            return redirect(url_for("dashboard.ver"))
        return vista(*args, **kwargs)
    return envoltura
