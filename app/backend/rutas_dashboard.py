from flask import Blueprint, render_template

import servicios
from sesion import login_required, usuario_actual

bp = Blueprint("dashboard", __name__)


@bp.route("/inicio")
@login_required
def ver():
    resumen = servicios.resumen_dashboard(usuario_actual())
    return render_template("dashboard.html", resumen=resumen)
