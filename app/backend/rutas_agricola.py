from flask import Blueprint, render_template, request, redirect, url_for, flash

import servicios
from sesion import login_required, admin_required
from constantes import ACCENT_OPTIONS, ACCENT_TO_BADGE

bp = Blueprint("agricola", __name__)


@bp.route("/agricola")
@login_required
def listar():
    cultivos = servicios.listar_cultivos()
    return render_template("agricola.html", cultivos=cultivos, accent_options=ACCENT_OPTIONS, accent_badge=ACCENT_TO_BADGE)


@bp.route("/agricola/nuevo", methods=["POST"])
@admin_required
def crear():
    ok, error = servicios.crear_cultivo(
        nombre=request.form.get("nombre", ""),
        temporada=request.form.get("temporada", ""),
        frecuencia_riego=request.form.get("frecuencia_riego", ""),
        consumo_agua=request.form.get("consumo_agua", ""),
        descripcion=request.form.get("descripcion", ""),
        accent=request.form.get("accent", ACCENT_OPTIONS[0]["value"]),
    )
    flash("Cultivo agregado correctamente." if ok else error, "success" if ok else "error")
    return redirect(url_for("agricola.listar"))


@bp.route("/agricola/<int:cultivo_id>/eliminar", methods=["POST"])
@admin_required
def eliminar(cultivo_id):
    servicios.eliminar_cultivo(cultivo_id)
    flash("Cultivo eliminado.", "success")
    return redirect(url_for("agricola.listar"))
