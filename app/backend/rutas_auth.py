from flask import Blueprint, render_template, request, redirect, url_for, flash

import servicios
from sesion import iniciar_sesion, cerrar_sesion, usuario_actual

bp = Blueprint("auth", __name__)


@bp.route("/", methods=["GET"])
def login():
    if usuario_actual() is not None:
        return redirect(url_for("dashboard.ver"))
    return render_template("login.html", modo="login")


@bp.route("/login", methods=["POST"])
def procesar_login():
    usuario = request.form.get("usuario", "")
    password = request.form.get("password", "")
    u, error = servicios.autenticar(usuario, password)
    if error:
        flash(error, "error")
        return render_template("login.html", modo="login", usuario_valor=usuario), 400
    iniciar_sesion(u)
    return redirect(url_for("dashboard.ver"))


# El alta de cuentas la realiza únicamente el comisariado desde el módulo de
# Usuarios (ver rutas_usuarios.py -> usuarios.crear). No existe autorregistro
# público.


@bp.route("/logout", methods=["POST"])
def logout():
    cerrar_sesion()
    return redirect(url_for("auth.login"))
