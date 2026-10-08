const express = require('express');
const requireAuth = require('../middleware/require-auth');
const requireRoles = require('../middleware/require-roles');

const router = express.Router();

const roleLabels = {
  ETUDIANT: {
    label: 'Étudiant',
    screens: [
      { title: 'Déclarer mon stage', href: '/stage' },
      { title: 'Suivre mon stage', href: '/stage' },
      { title: 'Consulter les offres et candidater', href: '/offres' },
    ],
  },
  ENCADRANT: {
    label: 'Encadrant',
    screens: [
      { title: 'Vérifier la conformité du stage', href: '/encadrant/stages' },
      { title: 'Valider une convention', href: '/espace' },
    ],
  },
  SERVICE_STAGES: {
    label: 'Service Stages',
    screens: [
      { title: 'Affecter un encadrant', href: '/service/affectations' },
      { title: 'Gérer les offres', href: '/service/offres' },
      { title: 'Valider une convention', href: '/espace' },
    ],
  },
  ENTREPRISE: {
    label: 'Entreprise',
    screens: [{ title: 'Traiter les candidatures', href: '/entreprise/candidatures' }],
  },
  RESPONSABLE: {
    label: 'Responsable',
    screens: [
      { title: 'Valider une convention', href: '/espace' },
      { title: 'Piloter les stages', href: '/espace' },
    ],
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
    .map((screen) => {
      const ready =
        (user.role === 'ETUDIANT' && screen.href === '/stage') ||
        (user.role === 'ETUDIANT' && screen.href === '/offres') ||
        (user.role === 'ENCADRANT' && screen.href === '/encadrant/stages') ||
        (user.role === 'SERVICE_STAGES' &&
          ['/service/affectations', '/service/offres'].includes(screen.href)) ||
        (user.role === 'ENTREPRISE' && screen.href === '/entreprise/candidatures');
      return `<article class="screen-card">
        <h2>${escapeHtml(screen.title)}</h2>
        <p>${ready ? 'Ouvrir cet écran pour continuer.' : 'Écran prévu par les maquettes du projet.'}</p>
        ${
          ready
            ? `<a class="button-link" href="${screen.href}">Ouvrir</a>`
            : '<span>À construire</span>'
        }
      </article>`;
    })
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
      <p class="notice">Certaines fonctions du projet sont encore en cours de construction.</p>
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
