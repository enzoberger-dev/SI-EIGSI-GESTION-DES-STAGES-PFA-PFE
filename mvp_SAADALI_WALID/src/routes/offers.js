const express = require('express');
const database = require('../db/database');
const requireRoles = require('../middleware/require-roles');

const router = express.Router();
const studentOnly = requireRoles('ETUDIANT');
const serviceOnly = requireRoles('SERVICE_STAGES');
const enterpriseOnly = requireRoles('ENTREPRISE');

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (character) => {
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

function layout(title, user, content) {
  return `<!doctype html>
<html lang="fr">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>${escapeHtml(title)} — Gestion des stages</title>
    <link rel="stylesheet" href="/css/auth.css">
    <link rel="stylesheet" href="/css/offers.css">
  </head>
  <body>
    <header class="site-header">
      <a class="brand" href="/espace">Gestion des stages PFA/PFE</a>
      <form action="/logout" method="post"><button class="button button-secondary" type="submit">Se déconnecter</button></form>
    </header>
    <main class="workspace">
      <a href="/espace">← Mon espace</a>
      <p class="eyebrow">${escapeHtml(user.firstName)} ${escapeHtml(user.lastName)}</p>
      ${content}
    </main>
  </body>
</html>`;
}

function message(code) {
  const messages = {
    'offer-created': '<p class="success-message" role="status">L’offre est maintenant publiée.</p>',
    applied: '<p class="success-message" role="status">Votre candidature a été envoyée.</p>',
    decided: '<p class="success-message" role="status">La décision a été enregistrée.</p>',
    error: '<p class="error-message" role="alert">Les renseignements sont incomplets ou invalides. Vérifiez le formulaire et réessayez.</p>',
    duplicate: '<p class="error-message" role="alert">Vous avez déjà candidaté à cette offre.</p>',
    unavailable: '<p class="error-message" role="alert">Cette offre n’est plus disponible.</p>',
    'decision-conflict': '<p class="error-message" role="alert">Cette candidature a déjà été traitée. Actualisez la page pour voir son état.</p>',
  };
  return messages[code] || '';
}

function candidatureStatus(status) {
  return {
    EN_ATTENTE: 'En attente de réponse',
    RETENUE: 'Retenue',
    REFUSEE: 'Refusée',
    RETIRÉE: 'Retirée',
  }[status] || 'État inconnu';
}

router.get('/service/offres', serviceOnly, (req, res) => {
  const companies = database
    .prepare('SELECT id_entreprise, raison_sociale, ville FROM ENTREPRISE ORDER BY raison_sociale')
    .all();
  const offers = database
    .prepare(
      `SELECT O.id_offre, O.titre, O.type, O.ville, O.duree_mois, O.statut,
              E.raison_sociale AS entreprise,
              COUNT(C.id_candidature) AS nombre_candidatures
       FROM OFFRE O
       JOIN ENTREPRISE E ON E.id_entreprise = O.id_entreprise
       LEFT JOIN CANDIDATURE C ON C.id_offre = O.id_offre
       GROUP BY O.id_offre
       ORDER BY O.date_creation DESC, O.id_offre DESC`,
    )
    .all();
  const companyOptions = companies
    .map(
      (company) =>
        `<option value="${company.id_entreprise}">${escapeHtml(company.raison_sociale)} — ${escapeHtml(company.ville)}</option>`,
    )
    .join('');
  const offerRows =
    offers
      .map(
        (offer) =>
          `<tr><td>${escapeHtml(offer.titre)}</td><td>${escapeHtml(offer.entreprise)}</td><td>${escapeHtml(offer.type)}</td><td>${escapeHtml(offer.ville)}</td><td>${offer.duree_mois} mois</td><td>${escapeHtml(offer.statut === 'PUBLIEE' ? 'Publiée' : offer.statut)}</td><td>${offer.nombre_candidatures}</td></tr>`,
      )
      .join('') || '<tr><td colspan="7">Aucune offre pour le moment.</td></tr>';

  res.send(
    layout(
      'Gérer les offres',
      req.session.user,
      `${message(req.query.message)}
        <h1>Gérer les offres de stage</h1>
        <p class="intro">Le Service Stages enregistre les offres et les publie pour les étudiants.</p>
        <form class="offer-form" action="/service/offres" method="post">
          <label for="id_entreprise">Entreprise</label>
          <select id="id_entreprise" name="id_entreprise" required>${companyOptions}</select>
          <label for="type">Type de stage</label>
          <select id="type" name="type" required><option value="PFA">PFA</option><option value="PFE">PFE</option></select>
          <label for="titre">Intitulé de l’offre</label>
          <input id="titre" name="titre" maxlength="200" required>
          <label for="description">Description des missions</label>
          <textarea id="description" name="description" rows="5" maxlength="3000" required></textarea>
          <label for="ville">Ville</label>
          <input id="ville" name="ville" maxlength="100" required>
          <label for="duree_mois">Durée en mois</label>
          <input id="duree_mois" name="duree_mois" type="number" min="1" step="1" required>
          <button class="button" type="submit">Publier l’offre</button>
        </form>
        <section class="offer-section">
          <h2>Offres et candidatures reçues</h2>
          <div class="offer-table-wrap"><table><thead><tr><th>Offre</th><th>Entreprise</th><th>Type</th><th>Ville</th><th>Durée</th><th>État</th><th>Candidatures</th></tr></thead><tbody>${offerRows}</tbody></table></div>
        </section>`,
    ),
  );
});

router.post('/service/offres', serviceOnly, (req, res, next) => {
  const companyId = Number(req.body.id_entreprise);
  const type = typeof req.body.type === 'string' ? req.body.type : '';
  const title = typeof req.body.titre === 'string' ? req.body.titre.trim() : '';
  const description = typeof req.body.description === 'string' ? req.body.description.trim() : '';
  const city = typeof req.body.ville === 'string' ? req.body.ville.trim() : '';
  const duration = Number(req.body.duree_mois);

  if (
    !Number.isSafeInteger(companyId) ||
    !['PFA', 'PFE'].includes(type) ||
    !title ||
    title.length > 200 ||
    !description ||
    description.length > 3000 ||
    !city ||
    city.length > 100 ||
    !Number.isSafeInteger(duration) ||
    duration < 1
  ) {
    return res.redirect('/service/offres?message=error');
  }

  try {
    const companyExists = database
      .prepare('SELECT 1 FROM ENTREPRISE WHERE id_entreprise = ?')
      .get(companyId);
    if (!companyExists) {
      return res.redirect('/service/offres?message=error');
    }

    const now = new Date().toISOString();
    database
      .prepare(
        `INSERT INTO OFFRE
           (id_entreprise, type, titre, description, ville, duree_mois, statut, date_creation, date_moderation)
         VALUES (?, ?, ?, ?, ?, ?, 'PUBLIEE', ?, ?)`,
      )
      .run(companyId, type, title, description, city, duration, now, now);
    return res.redirect('/service/offres?message=offer-created');
  } catch (error) {
    return next(error);
  }
});

router.get('/offres', studentOnly, (req, res) => {
  const offers = database
    .prepare(
      `SELECT O.id_offre, O.titre, O.description, O.type, O.ville, O.duree_mois,
              E.raison_sociale AS entreprise,
              C.id_candidature, C.statut AS candidature_statut,
              C.date_candidature, C.message AS candidature_message
       FROM OFFRE O
       JOIN ENTREPRISE E ON E.id_entreprise = O.id_entreprise
       LEFT JOIN CANDIDATURE C
         ON C.id_offre = O.id_offre AND C.id_etudiant = ?
       WHERE O.statut = 'PUBLIEE'
       ORDER BY O.date_creation DESC, O.id_offre DESC`,
    )
    .all(req.session.user.id);
  const offerCards =
    offers
      .map((offer) => {
        const application = offer.id_candidature
          ? `<p class="application-state"><strong>Ma candidature :</strong> ${escapeHtml(candidatureStatus(offer.candidature_statut))} — envoyée le ${escapeHtml(offer.date_candidature)}</p>`
          : `<form class="application-form" action="/offres/${offer.id_offre}/candidater" method="post">
              <label for="message-${offer.id_offre}">Message à l’entreprise (facultatif)</label>
              <textarea id="message-${offer.id_offre}" name="message" rows="3" maxlength="1000"></textarea>
              <button class="button" type="submit">Candidater</button>
            </form>`;
        return `<article class="offer-card">
          <p class="offer-type">${escapeHtml(offer.type)} · ${offer.duree_mois} mois</p>
          <h2>${escapeHtml(offer.titre)}</h2>
          <p><strong>${escapeHtml(offer.entreprise)}</strong> — ${escapeHtml(offer.ville)}</p>
          <p class="offer-description">${escapeHtml(offer.description)}</p>
          ${application}
        </article>`;
      })
      .join('') || '<p>Aucune offre n’est publiée actuellement.</p>';

  res.send(
    layout(
      'Offres de stage',
      req.session.user,
      `${message(req.query.message)}
        <h1>Offres de stage publiées</h1>
        <p class="intro">Consultez les offres et suivez ici les réponses des entreprises.</p>
        <section class="offer-list" aria-label="Offres publiées">${offerCards}</section>`,
    ),
  );
});

router.post('/offres/:id/candidater', studentOnly, (req, res, next) => {
  const offerId = Number(req.params.id);
  const messageText = typeof req.body.message === 'string' ? req.body.message.trim() : '';
  if (!Number.isSafeInteger(offerId) || messageText.length > 1000) {
    return res.redirect('/offres?message=error');
  }

  try {
    const apply = database.transaction(() => {
      const offer = database
        .prepare("SELECT 1 FROM OFFRE WHERE id_offre = ? AND statut = 'PUBLIEE'")
        .get(offerId);
      if (!offer) {
        throw new Error('OFFER_NOT_AVAILABLE');
      }
      const existing = database
        .prepare('SELECT 1 FROM CANDIDATURE WHERE id_offre = ? AND id_etudiant = ?')
        .get(offerId, req.session.user.id);
      if (existing) {
        throw new Error('APPLICATION_ALREADY_EXISTS');
      }

      database
        .prepare(
          `INSERT INTO CANDIDATURE (id_offre, id_etudiant, date_candidature, statut, message)
           VALUES (?, ?, ?, 'EN_ATTENTE', ?)`,
        )
        .run(offerId, req.session.user.id, new Date().toISOString(), messageText || null);
    });
    apply();
    return res.redirect('/offres?message=applied');
  } catch (error) {
    if (error.message === 'OFFER_NOT_AVAILABLE') {
      return res.redirect('/offres?message=unavailable');
    }
    if (
      error.message === 'APPLICATION_ALREADY_EXISTS' ||
      error.code === 'SQLITE_CONSTRAINT_UNIQUE'
    ) {
      return res.redirect('/offres?message=duplicate');
    }
    return next(error);
  }
});

router.get('/entreprise/candidatures', enterpriseOnly, (req, res) => {
  const applications = database
    .prepare(
      `SELECT C.id_candidature, C.statut, C.date_candidature, C.message,
              O.id_offre, O.titre, O.type, O.ville,
              U.prenom, U.nom, U.email
       FROM CANDIDATURE C
       JOIN OFFRE O ON O.id_offre = C.id_offre
       JOIN UTILISATEUR U ON U.id_utilisateur = C.id_etudiant
       WHERE O.id_entreprise = ?
       ORDER BY CASE C.statut WHEN 'EN_ATTENTE' THEN 0 ELSE 1 END,
                C.date_candidature DESC`,
    )
    .all(req.session.user.companyId);
  const cards =
    applications
      .map((application) => {
        const actions =
          application.statut === 'EN_ATTENTE'
            ? `<form class="decision-form" action="/entreprise/candidatures/${application.id_candidature}" method="post">
                <button class="button" type="submit" name="decision" value="RETENUE">Retenir</button>
                <button class="button button-secondary" type="submit" name="decision" value="REFUSEE">Refuser</button>
              </form>`
            : `<p class="application-state"><strong>Décision :</strong> ${escapeHtml(candidatureStatus(application.statut))}</p>`;
        return `<article class="application-card">
          <p class="offer-type">${escapeHtml(application.type)} · ${escapeHtml(application.ville)}</p>
          <h2>${escapeHtml(application.titre)}</h2>
          <p><strong>Candidat :</strong> ${escapeHtml(application.prenom)} ${escapeHtml(application.nom)} — <a href="mailto:${encodeURIComponent(application.email)}">${escapeHtml(application.email)}</a></p>
          <p><strong>Reçue le :</strong> ${escapeHtml(application.date_candidature)}</p>
          <p><strong>Message :</strong> ${escapeHtml(application.message || 'Aucun message transmis.')}</p>
          ${actions}
        </article>`;
      })
      .join('') || '<p>Aucune candidature n’a encore été reçue pour vos offres.</p>';

  res.send(
    layout(
      'Candidatures reçues',
      req.session.user,
      `${message(req.query.message)}
        <h1>Candidatures reçues</h1>
        <p class="intro">Les dossiers affichés concernent uniquement les offres de votre entreprise.</p>
        <section class="application-list" aria-label="Candidatures reçues">${cards}</section>`,
    ),
  );
});

router.post('/entreprise/candidatures/:id', enterpriseOnly, (req, res, next) => {
  const applicationId = Number(req.params.id);
  const decision = req.body.decision;
  if (!Number.isSafeInteger(applicationId) || !['RETENUE', 'REFUSEE'].includes(decision)) {
    return res.redirect('/entreprise/candidatures?message=error');
  }

  try {
    const saveDecision = database.transaction(() => {
      const application = database
        .prepare(
          `SELECT C.statut
           FROM CANDIDATURE C
           JOIN OFFRE O ON O.id_offre = C.id_offre
           WHERE C.id_candidature = ? AND O.id_entreprise = ?`,
        )
        .get(applicationId, req.session.user.companyId);
      if (!application) {
        throw new Error('APPLICATION_NOT_OWNED');
      }
      if (application.statut !== 'EN_ATTENTE') {
        throw new Error('APPLICATION_ALREADY_DECIDED');
      }

      database
        .prepare(
          `UPDATE CANDIDATURE
           SET statut = ?
           WHERE id_candidature = ? AND statut = 'EN_ATTENTE'`,
        )
        .run(decision, applicationId);
    });
    saveDecision();
    return res.redirect('/entreprise/candidatures?message=decided');
  } catch (error) {
    if (error.message === 'APPLICATION_NOT_OWNED') {
      return res.status(404).send('Cette candidature est introuvable pour votre entreprise.');
    }
    if (error.message === 'APPLICATION_ALREADY_DECIDED') {
      return res.redirect('/entreprise/candidatures?message=decision-conflict');
    }
    return next(error);
  }
});

module.exports = router;
