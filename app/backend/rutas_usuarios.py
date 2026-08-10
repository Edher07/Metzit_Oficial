from flask import Blueprint, render_template, request, redirect, url_for, flash

import servicios
from sesion import admin_required, usuario_actual

bp = Blueprint("usuarios", __name__)


@bp.route("/usuarios")
@admin_required
def listar():
    usuarios = servicios.listar_usuarios()
    return render_template("usuarios.html", usuarios=usuarios)


@bp.route("/usuarios/nuevo", methods=["POST"])
@admin_required
def crear():
    # Solo el comisariado puede registrar/validar nuevas cuentas de usuario.
    nuevo, error = servicios.registrar_usuario_por_comisariado(
        usuario=request.form.get("usuario", ""),
        password=request.form.get("password", ""),
        nombre=request.form.get("nombre", ""),
        direccion=request.form.get("direccion", ""),
        telefono=request.form.get("telefono", ""),
        parcela=request.form.get("parcela", ""),
        rol=request.form.get("rol", "usuario"),
    )
    flash("Usuario registrado correctamente." if not error else error, "success" if not error else "error")
    return redirect(url_for("usuarios.listar"))


@bp.route("/usuarios/<int:usuario_id>/editar", methods=["POST"])
@admin_required
def editar(usuario_id):
    _, error = servicios.editar_usuario(
        usuario_id,
        nombre=request.form.get("nombre", ""),
        direccion=request.form.get("direccion", ""),
        telefono=request.form.get("telefono", ""),
        parcela=request.form.get("parcela", ""),
        rol=request.form.get("rol", "usuario"),
        password=request.form.get("password", ""),
    )
    flash("Usuario actualizado correctamente." if not error else error, "success" if not error else "error")
    return redirect(url_for("usuarios.listar"))


@bp.route("/usuarios/<int:usuario_id>/alternar-activo", methods=["POST"])
@admin_required
def alternar_activo(usuario_id):
    actual = usuario_actual()
    if usuario_id == actual.id:
        flash("No puedes desactivar tu propia cuenta.", "error")
        return redirect(url_for("usuarios.listar"))
    servicios.alternar_usuario_activo(usuario_id)
    return redirect(url_for("usuarios.listar"))


# Nota: ya no se permite eliminar usuarios físicamente. Desactivar una cuenta
# (arriba) es la única forma de darla de baja, para no perder el historial de
# turnos, multas y avisos asociados a ese usuario.
