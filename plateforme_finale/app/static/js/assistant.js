/* Assistant IA (lot 9) : bulle flottante en bas à droite + relecture du sujet de stage.
   Le site reste utilisable sans ce fichier : la bulle et le bouton de relecture n'apparaissent simplement pas.
   Rien n'est conservé sur le serveur ; la conversation reste dans le navigateur (sessionStorage), pour suivre
   la personne de page en page, et disparaît à la fermeture de l'onglet. */
(function () {
  "use strict";

  function jeton() {
    var champ = document.querySelector("input[name=csrfmiddlewaretoken]");
    return champ ? champ.value : "";
  }

  function post(url, donnees) {
    var corps = new URLSearchParams();
    Object.keys(donnees).forEach(function (cle) { corps.append(cle, donnees[cle]); });
    return fetch(url, {
      method: "POST",
      headers: { "X-CSRFToken": jeton(), "Content-Type": "application/x-www-form-urlencoded" },
      body: corps.toString(),
      credentials: "same-origin"
    }).then(function (r) { if (!r.ok) { throw new Error("HTTP " + r.status); } return r.json(); });
  }

  function mention(mode) {
    return mode === "ia"
      ? "Généré par une IA : peut contenir des erreurs."
      : "Mode démonstration (sans IA).";
  }

  function lire(cle, defaut) {
    try { var v = sessionStorage.getItem(cle); return v === null ? defaut : JSON.parse(v); } catch (e) { return defaut; }
  }
  function ecrire(cle, valeur) {
    try { sessionStorage.setItem(cle, JSON.stringify(valeur)); } catch (e) { /* stockage bloqué : tant pis */ }
  }

  /* ---------------------------------------------------------------- la bulle */
  var racine = document.getElementById("assistant-widget");
  if (racine) {
    var bulle = racine.querySelector(".assistant-bulle");
    var fenetre = racine.querySelector(".assistant-fenetre");
    var fil = racine.querySelector(".assistant-fil");
    var formulaire = racine.querySelector(".assistant-saisie");
    var zone = formulaire.querySelector("textarea");
    var envoyer = formulaire.querySelector(".bouton");
    var agrandir = racine.querySelector(".assistant-agrandir");
    var fermer = racine.querySelector(".assistant-fermer");
    var messages = lire("assistant_fil", []);
    var etat = lire("assistant_etat", "ferme");   // ferme (bulle), normal, grand
    var url = racine.getAttribute("data-url");

    bulle.hidden = false;

    var accueil = "Bonjour ! Je peux vous aider à utiliser le site. Posez-moi une question.";

    function dessiner(m) {
      var p = document.createElement("div");
      p.className = "msg " + (m.de === "moi" ? "msg-utilisateur" : "msg-assistant");
      p.appendChild(document.createTextNode(m.texte));      /* texte brut : jamais du HTML */
      if (m.mention) {
        var s = document.createElement("span");
        s.className = "msg-mention";
        s.textContent = m.mention;
        p.appendChild(s);
      }
      fil.appendChild(p);
      fil.scrollTop = fil.scrollHeight;
      return p;
    }

    function sauver() { ecrire("assistant_fil", messages.slice(-20)); }

    function afficherEtat(nouveau) {
      etat = nouveau;
      racine.setAttribute("data-etat", etat);
      var ouvert = etat !== "ferme";
      bulle.hidden = ouvert;
      bulle.setAttribute("aria-expanded", ouvert ? "true" : "false");
      agrandir.setAttribute("aria-label", etat === "grand" ? "Réduire la fenêtre" : "Agrandir la fenêtre");
      ecrire("assistant_etat", etat);
    }

    messages.forEach(dessiner);
    if (!messages.length) { dessiner({ de: "assistant", texte: accueil }); }
    afficherEtat(etat);
    if (etat !== "ferme") { fil.scrollTop = fil.scrollHeight; }

    bulle.addEventListener("click", function () { afficherEtat("normal"); zone.focus(); });
    fermer.addEventListener("click", function () { afficherEtat("ferme"); bulle.focus(); });
    agrandir.addEventListener("click", function () { afficherEtat(etat === "grand" ? "normal" : "grand"); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && etat !== "ferme" && racine.contains(document.activeElement)) { afficherEtat("ferme"); bulle.focus(); }
    });

    zone.addEventListener("keydown", function (e) {          /* Entrée envoie, Maj+Entrée = retour à la ligne */
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); formulaire.requestSubmit(); }
    });

    formulaire.addEventListener("submit", function (e) {
      e.preventDefault();
      var question = zone.value.trim();
      if (!question) { return; }
      var moi = { de: "moi", texte: question };
      messages.push(moi); dessiner(moi);
      zone.value = "";
      envoyer.disabled = true;
      var attente = dessiner({ de: "assistant", texte: "…" });
      post(url, { question: question }).then(function (r) {
        var rep = { de: "assistant", texte: r.texte, mention: mention(r.mode) };
        attente.remove(); messages.push(rep); dessiner(rep);
      }).catch(function () {
        var rep = { de: "assistant", texte: "L'assistant n'est pas disponible pour le moment. Consultez la page « À propos et aide »." };
        attente.remove(); messages.push(rep); dessiner(rep);
      }).then(function () { envoyer.disabled = false; sauver(); zone.focus(); });
    });
  }

  /* ---------------------------------------------------------------- relecture du sujet (fiche de stage) */
  var bloc = document.querySelector(".relecture");
  if (bloc) {
    var bouton = bloc.querySelector(".relecture-bouton");
    var sortie = bloc.querySelector(".relecture-resultat");
    var champ = document.getElementById(bloc.getAttribute("data-champ"));
    if (bouton && sortie && champ) {
      bouton.hidden = false;
      bouton.addEventListener("click", function () {
        sortie.textContent = "Relecture en cours…";
        bouton.disabled = true;
        post(bloc.getAttribute("data-url"), { sujet: champ.value }).then(function (r) {
          sortie.textContent = r.texte;                       /* texte brut : jamais du HTML */
          var m = document.createElement("p");
          m.className = "mention-ia";
          m.textContent = mention(r.mode) + " C'est votre encadrant qui valide la fiche.";
          sortie.appendChild(m);
        }).catch(function () {
          sortie.textContent = "La relecture n'est pas disponible pour le moment. Vous pouvez continuer sans.";
        }).then(function () { bouton.disabled = false; });
      });
    }
  }
})();
