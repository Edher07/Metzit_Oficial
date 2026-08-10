# Metzit — Agua y Pueblo — Backend Flask

Aplicación web de gestión comunitaria del agua de riego: turnos de riego,
avisos comunitarios, faenas y reuniones, catálogo agrícola y administración
de usuarios. Reescrita como una app **Flask + SQLite** con una página HTML
y una hoja de estilos por cada pantalla visible.

## Estructura del proyecto

```
app/
├── backend/                  Todo el backend Python en una sola carpeta
│   ├── config.py               Configuración de la app
│   ├── constantes.py           Paleta de colores, navegación, catálogos
│   ├── modelos.py               Dataclasses (una por tabla)
│   ├── datos.py                  Acceso a datos (SQL crudo sobre SQLite)
│   ├── servicios.py                Lógica de negocio / validaciones
│   ├── sesion.py                    Manejo de sesión / login / decoradores
│   └── rutas_*.py                    Rutas de Flask (Blueprints), una por sección
├── static/
│   ├── css/                 Una hoja de estilos por página + utility.css
│   ├── js/                    JavaScript de cliente
│   └── assets/                  Imágenes (logo, etc.)
├── views/                      Una plantilla HTML por pantalla visible
├── app.py                   Fábrica de la aplicación Flask
├── database.py                 Esquema SQLite + datos semilla
├── run.py                       Punto de entrada (`python run.py`)
├── requirements.txt
├── runtime.txt
└── .gitignore
```

A diferencia de otros proyectos hermanos, aquí **todo el código Python del
backend vive en una sola carpeta (`backend/`)** en lugar de estar repartido
en subcarpetas de config/controllers/models/repositories/services/etc.

## Cómo correrlo

```bash
cd app
pip install -r requirements.txt
python run.py
```

Abre `http://localhost:5000` en tu navegador. La base de datos SQLite
(`metzit.sqlite3`) se crea automáticamente en el primer arranque. Solo se
siembra la cuenta del comisariado; el resto de usuarios, turnos, avisos,
faenas/reuniones y multas no existen hasta que se dan de alta desde la app.

### Cuentas de prueba

Todas las cuentas de demostración usan la contraseña **`1234`**.

| Rol         | Usuario       | Nombre              |
|-------------|---------------|----------------------|
| Comisariado | `comisariado` | Manuel Ramiro Soto   |

También puedes crear una cuenta de usuario nueva desde la pantalla de login
("¿No tienes cuenta? Regístrate").

## Notas técnicas

- No usa ningún ORM: todas las consultas SQL viven en `backend/datos.py`.
- Los turnos están ligados a un usuario real mediante `usuario_id` (clave
  foránea), y la asistencia a faenas/reuniones se guarda en una tabla de
  unión `actividad_participantes` — ambas mejoras respecto al prototipo
  original, que solo guardaba nombres en texto libre y arreglos en memoria.
- Los iconos usan Lucide (vía CDN).
- Las contraseñas se guardan siempre con hash (`werkzeug.security`), nunca
  en texto plano.
- Solo el rol `comisariado` puede crear/eliminar turnos, avisos, faenas,
  cultivos y administrar usuarios; el rol `usuario` tiene acceso de solo
  lectura además de poder confirmar su propia asistencia a faenas/reuniones.
