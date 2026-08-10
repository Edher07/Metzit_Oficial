/* JavaScript de cliente compartido por toda la aplicación Metzit.
 * Reemplaza los pequeños onclick= en línea por listeners declarativos basados
 * en atributos data-*, para no repetir lógica en cada plantilla. */

function toggleHidden(id) {
  var el = document.getElementById(id);
  if (el) el.classList.toggle("hidden");
}

function toggleMobileSidebar() {
  var shell = document.querySelector(".app-shell");
  if (shell) shell.classList.toggle("mob-open");
}

function togglePasswordField(id) {
  var input = document.getElementById(id);
  if (!input) return;
  input.type = input.type === "password" ? "text" : "password";
}

document.addEventListener("DOMContentLoaded", function () {
  // Botones "+ Nuevo turno/aviso/faena/cultivo" que muestran u ocultan un
  // formulario inline: <button data-toggle-target="form-nuevo-turno">
  document.querySelectorAll("[data-toggle-target]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      toggleHidden(btn.getAttribute("data-toggle-target"));
    });
  });

  // Botón de menú móvil que abre/cierra la barra lateral.
  document.querySelectorAll("[data-mobile-toggle]").forEach(function (btn) {
    btn.addEventListener("click", toggleMobileSidebar);
  });

  // Botón de "ojo" para mostrar/ocultar la contraseña en el login.
  document.querySelectorAll("[data-toggle-password]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      togglePasswordField(btn.getAttribute("data-toggle-password"));
    });
  });

  if (window.lucide) lucide.createIcons();
});
