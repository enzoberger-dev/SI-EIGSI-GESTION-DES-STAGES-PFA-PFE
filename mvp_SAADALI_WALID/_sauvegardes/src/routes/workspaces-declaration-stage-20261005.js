const express = require('express');
const requireAuth = require('../middleware/require-auth');
const requireRoles = require('../middleware/require-roles');

const router = express.Router();

const roleLabels = {
  ETUDIANT: {
    label: 'Étudiant',
    screens: ['Déclarer mon stage', 'Suivre mon stage'],
  },
  ENCADRANT: {
    label: 'Encadrant',
    screens: ['Vérifier la conformité du stage', 'Valider une convention'],
  },
  SERVICE_STAGES: {
    label: 'Service Stages',
    screens: ['Valider une convention', 'Planifier les soutenances'],
  },
  RESPONSABLE: {
    label: 'Responsable',
    screens: ['Valider une convention', 'Piloter les stages'],
  },
};

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => {
    const entities = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
    };
    return entities[character];
  });
}

router.get('/espace', requireAuth, (req, res) => {
  const user = req.session.user;
  const details = roleLabels[user.role];
  const cards = details.screens
    .map(
      (screen) =>
        `<article class="screen-card"><h2>${escapeHtml(screen)}</h2><p>Écran prévu par les maquettes du projet.</p><span>À construire</span></article>`,
    )
    .join('');

  res.send(`<!doctype html>
<html lang="fr">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Mon espace — Gestion des stages</title>
    <link rel="stylesheet" href="/css/auth.css">
  </head>
  <body>
    <header class="site-header">
      <a class="brand" href="/espace">Gestion des stages PFA/PFE</a>
      <form action="/logout" method="post"><button class="button button-secondary" type="submit">Se déconnecter</button></form>
    </header>
    <main class="workspace">
      <p class="eyebrow">Mon espace · ${escapeHtml(details.label)}</p>
      <h1>Bonjour ${escapeHtml(user.firstName)} ${escapeHtml(user.lastName)}</h1>
      <p class="intro">Connecté avec ${escapeHtml(user.email)}. Les écrans ci-dessous correspondent à votre rôle dans les maquettes.</p>
      <section class="screen-grid" aria-label="Écrans de votre rôle">${cards}</section>
      <p class="notice">Cette première étape vérifie la connexion et les rôles. Les fonctions métier des écrans seront réalisées ensuite.</p>
    </main>
  </body>
</html>`);
});

router.get(
  '/espace/:role',
  requireAuth,
  (req, res, next) => {
    const routeRoles = {
      etudiant: 'ETUDIANT',
      encadrant: 'ENCADRANT',
      'service-stages': 'SERVICE_STAGES',
      responsable: 'RESPONSABLE',
    };
    const requiredRole = routeRoles[req.params.role];

    if (!requiredRole) {
      return next();
    }

    return requireRoles(requiredRole)(req, res, next);
  },
  (req, res) => {
    res.redirect('/espace');
  },
);

module.exports = router;
