/* Menu sur téléphone : ouvrir / fermer (lot 8). Le site reste utilisable si ce fichier ne se charge pas. */
(function () {
  "use strict";
  var bouton = document.querySelector(".menu-bouton");
  var menu = document.getElementById("menu");
  if (!bouton || !menu) { return; }
  var fermer = function () { menu.classList.remove("ouvert"); bouton.setAttribute("aria-expanded", "false"); };
  bouton.addEventListener("click", function () {
    var ouvert = menu.classList.toggle("ouvert");
    bouton.setAttribute("aria-expanded", ouvert ? "true" : "false");
  });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") { fermer(); bouton.focus(); } });
  document.addEventListener("click", function (e) {
    if (menu.classList.contains("ouvert") && !menu.contains(e.target) && !bouton.contains(e.target)) { fermer(); }
  });
})();
