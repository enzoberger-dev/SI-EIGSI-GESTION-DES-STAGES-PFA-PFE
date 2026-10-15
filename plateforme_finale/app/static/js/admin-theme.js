/* Administration : thème clair à la première visite (plus lisible). Ensuite, le choix fait avec le bouton
   « thème » est respecté. (Django enregistre « auto » dès le chargement : on ne peut donc pas s'y fier
   pour savoir si la personne a choisi, d'où un repère à nous.) */
(function () {
  "use strict";
  try {
    if (!localStorage.getItem("theme_eigsi_initialise")) {
      localStorage.setItem("theme_eigsi_initialise", "1");
      localStorage.setItem("theme", "light");
    }
    document.documentElement.dataset.theme = localStorage.getItem("theme") || "light";
  } catch (e) {
    document.documentElement.dataset.theme = "light";   // stockage bloqué : on reste en clair
  }
})();
