/* Relecture du sujet de stage par l'assistant (lot 9). Le formulaire marche sans ce fichier : seul le bouton disparaît. */
(function () {
  "use strict";
  var bloc = document.querySelector(".relecture");
  if (!bloc) { return; }
  var bouton = bloc.querySelector(".relecture-bouton");
  var sortie = bloc.querySelector(".relecture-resultat");
  var champ = document.getElementById(bloc.getAttribute("data-champ"));
  var jeton = document.querySelector("input[name=csrfmiddlewaretoken]");
  if (!bouton || !sortie || !champ || !jeton) { return; }
  bouton.hidden = false;

  bouton.addEventListener("click", function () {
    sortie.textContent = "Relecture en cours…";
    bouton.disabled = true;
    var donnees = new URLSearchParams();
    donnees.append("sujet", champ.value);
    fetch(bloc.getAttribute("data-url"), {
      method: "POST",
      headers: { "X-CSRFToken": jeton.value, "Content-Type": "application/x-www-form-urlencoded" },
      body: donnees.toString(),
      credentials: "same-origin"
    }).then(function (r) { return r.json(); }).then(function (r) {
      /* textContent : la réponse de l'IA n'est jamais interprétée comme du HTML */
      sortie.textContent = r.texte;
      var mention = document.createElement("p");
      mention.className = "mention-ia";
      mention.textContent = r.mode === "ia"
        ? "Généré par une IA : peut contenir des erreurs. C'est votre encadrant qui valide la fiche."
        : "Mode démonstration (sans IA) : remarques simples. C'est votre encadrant qui valide la fiche.";
      sortie.appendChild(mention);
    }).catch(function () {
      sortie.textContent = "La relecture n'est pas disponible pour le moment. Vous pouvez continuer sans.";
    }).then(function () { bouton.disabled = false; });
  });
})();
