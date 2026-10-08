const express = require('express');
const database = require('../db/database');
const requireRoles = require('../middleware/require-roles');

const router = express.Router();
const studentOnly = requireRoles('ETUDIANT');
const advisorOnly = requireRoles('ENCADRANT');
const stageServiceOnly = requireRoles('SERVICE_STAGES');

const ORIGINS = {
  RESEAU: 'Réseau personnel',
  SITE_EMPLOI: "Site d'emploi",
  OFFRE_PARTENAIRE: 'Offre partenaire',
};

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
    <link rel="stylesheet" href="/css/stages.css">
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

function showMessage(code) {
  const messages = {
    saved: '<p class="success-message" role="status">Brouillon enregistré.</p>',
    submitted: '<p class="success-message" role="status">Votre fiche a été transmise à votre encadrant.</p>',
    decided: '<p class="success-message" role="status">La décision a été enregistrée.</p>',
    assigned: '<p class="success-message" role="status">L’encadrant a été attribué à l’étudiant.</p>',
    error: '<p class="error-message" role="alert">Vérifiez les renseignements indiqués puis réessayez.</p>',
  };
  return messages[code] || '';
}

function readForm(body) {
  const text = (field) => (typeof body[field] === 'string' ? body[field].trim() : '');
  return {
    entreprise: text('entreprise'),
    ville: text('ville'),
    origine: text('origine'),
    id_offre: text('id_offre'),
    sujet: text('sujet'),
    type: text('type'),
    date_debut: text('date_debut'),
    date_fin: text('date_fin'),
    nom_tuteur_entreprise: text('nom_tuteur_entreprise'),
    email_tuteur_entreprise: text('email_tuteur_entreprise'),
    missions: text('missions'),
  };
}

function validateStageForm(form) {
  const required = [
    form.entreprise,
    form.ville,
    form.origine,
    form.sujet,
    form.type,
    form.date_debut,
    form.date_fin,
    form.nom_tuteur_entreprise,
    form.email_tuteur_entreprise,
    form.missions,
  ];

  if (required.some((value) => !value)) {
    return 'Tous les champs obligatoires doivent être remplis.';
  }
  if (!(form.type === 'PFA' || form.type === 'PFE')) {
    return 'Le type de stage est invalide.';
  }
  if (!Object.hasOwn(ORIGINS, form.origine)) {
    return "L’origine du stage est invalide.";
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email_tuteur_entreprise)) {
    return "L'adresse e-mail du tuteur est invalide.";
  }
  if (
    !/^\d{4}-\d{2}-\d{2}$/.test(form.date_debut) ||
    !/^\d{4}-\d{2}-\d{2}$/.test(form.date_fin) ||
    Number.isNaN(Date.parse(form.date_debut)) ||
    Number.isNaN(Date.parse(form.date_fin)) ||
    form.date_fin <= form.date_debut
  ) {
    return 'Les dates sont invalides : la fin doit être après le début.';
  }
  if (form.origine === 'OFFRE_PARTENAIRE' && !/^\d+$/.test(form.id_offre)) {
    return 'Choisissez une offre partenaire.';
  }

  return null;
}

function loadPublishedOffers() {
  return database
    .prepare(
      `SELECT O.id_offre, O.titre, O.type, O.id_entreprise,
              E.raison_sociale, E.ville
       FROM OFFRE O
       JOIN ENTREPRISE E ON E.id_entreprise = O.id_entreprise
       WHERE O.statut = 'PUBLIEE'
       ORDER BY O.titre`,
    )
    .all();
}

function renderStageForm({ user, form = {}, offers = [], action, title, notice, extraContent = '' }) {
  const offerOptions = offers
    .map(
      (offer) =>
        `<option value="${offer.id_offre}" data-type="${escapeHtml(offer.type)}" data-company="${escapeHtml(offer.raison_sociale)}" data-city="${escapeHtml(offer.ville)}" ${
          String(form.id_offre) === String(offer.id_offre) ? 'selected' : ''
        }>${escapeHtml(offer.titre)} (${escapeHtml(offer.type)})</option>`,
    )
    .join('');
  const formAction = action === 'correction' ? `/stage/${form.id_stage}/corriger` : '/stage/enregistrer';
  const submitLabel = action === 'correction' ? 'Renvoyer à mon encadrant' : 'Soumettre à mon encadrant';

  return layout(
    title,
    user,
    `${showMessage(notice)}
      <h1>${escapeHtml(title)}</h1>
      <p class="intro">Les champs marqués * sont obligatoires. L’encadrant est attribué par le Service Stages.</p>
      <form class="stage-form" action="${formAction}" method="post">
        <label for="entreprise">Entreprise *</label>
        <input id="entreprise" name="entreprise" maxlength="150" required value="${escapeHtml(form.entreprise)}">
        <label for="ville">Ville *</label>
        <input id="ville" name="ville" maxlength="100" required value="${escapeHtml(form.ville)}">
        <label for="origine">Origine du stage *</label>
        <select id="origine" name="origine" required>
          <option value="">Choisir une origine</option>
          <option value="RESEAU" ${form.origine === 'RESEAU' ? 'selected' : ''}>Réseau personnel</option>
          <option value="SITE_EMPLOI" ${form.origine === 'SITE_EMPLOI' ? 'selected' : ''}>Site d’emploi</option>
          <option value="OFFRE_PARTENAIRE" ${form.origine === 'OFFRE_PARTENAIRE' ? 'selected' : ''}>Offre partenaire</option>
        </select>
        <div id="offer-field" ${form.origine === 'OFFRE_PARTENAIRE' ? '' : 'hidden'}>
          <label for="id_offre">Offre partenaire *</label>
          <select id="id_offre" name="id_offre">
            <option value="">Choisir une offre publiée</option>${offerOptions}
          </select>
          <p class="help-text">L’entreprise et le type seront repris de l’offre choisie.</p>
        </div>
        <label for="sujet">Intitulé du sujet *</label>
        <input id="sujet" name="sujet" maxlength="200" required value="${escapeHtml(form.sujet)}">
        <label for="type">Type *</label>
        <select id="type" name="type" required>
          <option value="">Choisir PFA ou PFE</option>
          <option value="PFA" ${form.type === 'PFA' ? 'selected' : ''}>PFA</option>
          <option value="PFE" ${form.type === 'PFE' ? 'selected' : ''}>PFE</option>
        </select>
        <div class="form-row">
          <div><label for="date_debut">Date de début *</label><input id="date_debut" name="date_debut" type="date" required value="${escapeHtml(form.date_debut)}"></div>
          <div><label for="date_fin">Date de fin *</label><input id="date_fin" name="date_fin" type="date" required value="${escapeHtml(form.date_fin)}"></div>
        </div>
        <label for="nom_tuteur_entreprise">Nom du tuteur en entreprise *</label>
        <input id="nom_tuteur_entreprise" name="nom_tuteur_entreprise" maxlength="150" required value="${escapeHtml(form.nom_tuteur_entreprise)}">
        <label for="email_tuteur_entreprise">E-mail du tuteur *</label>
        <input id="email_tuteur_entreprise" name="email_tuteur_entreprise" type="email" maxlength="150" required value="${escapeHtml(form.email_tuteur_entreprise)}">
        <label for="missions">Missions principales *</label>
        <textarea id="missions" name="missions" rows="4" maxlength="3000" required>${escapeHtml(form.missions)}</textarea>
        <div class="form-actions">
          <button class="button button-secondary" type="submit" name="action" value="brouillon" formnovalidate>Enregistrer le brouillon</button>
          <button class="button" type="submit" name="action" value="soumettre">${submitLabel}</button>
        </div>
      </form>
      <script>
        const origin = document.getElementById('origine');
        const offerField = document.getElementById('offer-field');
        const offerSelect = document.getElementById('id_offre');
        const typeSelect = document.getElementById('type');
        const companyInput = document.getElementById('entreprise');
        origin.addEventListener('change', () => {
          const usesOffer = origin.value === 'OFFRE_PARTENAIRE';
          offerField.hidden = !usesOffer;
          offerSelect.required = usesOffer;
          if (!usesOffer) offerSelect.value = '';
        });
        offerSelect.addEventListener('change', () => {
          const option = offerSelect.selectedOptions[0];
          if (option && option.dataset.type) {
            typeSelect.value = option.dataset.type;
            companyInput.value = option.dataset.company || '';
            document.getElementById('ville').value = option.dataset.city || '';
          }
        });
      </script>${extraContent}`,
  );
}

function getPendingAssignment(studentId) {
  return database
    .prepare(
      `SELECT A.id_affectation, U.prenom, U.nom
       FROM AFFECTATION_ENCADRANT A
       JOIN UTILISATEUR U ON U.id_utilisateur = A.id_encadrant
       WHERE A.id_etudiant = ? AND A.statut = 'EN_ATTENTE'`,
    )
    .get(studentId);
}

function upsertDraft({ studentId, assignmentId, stageId = null, form }) {
  database
    .prepare(
      `INSERT INTO BROUILLON_STAGE
         (id_etudiant, id_affectation, id_stage, entreprise, ville, origine, id_offre,
          sujet, type, date_debut, date_fin, nom_tuteur_entreprise, email_tuteur_entreprise,
          missions, statut, date_modification)
       VALUES
         (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'BROUILLON', ?)
       ON CONFLICT(id_affectation) DO UPDATE SET
         id_stage = excluded.id_stage,
         entreprise = excluded.entreprise,
         ville = excluded.ville,
         origine = excluded.origine,
         id_offre = excluded.id_offre,
         sujet = excluded.sujet,
         type = excluded.type,
         date_debut = excluded.date_debut,
         date_fin = excluded.date_fin,
         nom_tuteur_entreprise = excluded.nom_tuteur_entreprise,
         email_tuteur_entreprise = excluded.email_tuteur_entreprise,
         missions = excluded.missions,
         statut = 'BROUILLON',
         date_modification = excluded.date_modification`,
    )
    .run(
      studentId,
      assignmentId,
      stageId,
      form.entreprise || null,
      form.ville || null,
      form.origine || null,
      form.id_offre ? Number(form.id_offre) : null,
      form.sujet || null,
      form.type || null,
      form.date_debut || null,
      form.date_fin || null,
      form.nom_tuteur_entreprise || null,
      form.email_tuteur_entreprise || null,
      form.missions || null,
      new Date().toISOString(),
    );
}

function companyIdForStage(form, offer) {
  if (offer) {
    return offer.id_entreprise;
  }

  const existing = database
    .prepare(
      `SELECT id_entreprise
       FROM ENTREPRISE
       WHERE lower(raison_sociale) = lower(?) AND lower(ville) = lower(?)
       ORDER BY id_entreprise
       LIMIT 1`,
    )
    .get(form.entreprise, form.ville);
  if (existing) {
    return existing.id_entreprise;
  }

  return database
    .prepare('INSERT INTO ENTREPRISE (raison_sociale, ville, contact_email) VALUES (?, ?, ?)')
    .run(form.entreprise, form.ville, form.email_tuteur_entreprise).lastInsertRowid;
}

function validateOffer(form) {
  if (form.origine !== 'OFFRE_PARTENAIRE') {
    return null;
  }

  const offer = database
    .prepare(
      `SELECT id_offre, id_entreprise, type
       FROM OFFRE
       WHERE id_offre = ? AND statut = 'PUBLIEE'`,
    )
    .get(Number(form.id_offre));
  if (!offer) {
    return { error: 'Cette offre partenaire n’est pas disponible.' };
  }
  if (offer.type !== form.type) {
    return { error: 'Le type de stage doit correspondre au type de l’offre.' };
  }
  return { offer };
}

const createStageFromDraft = database.transaction((studentId, assignmentId, form, offer) => {
  const assignment = database
    .prepare(
      `SELECT id_encadrant
       FROM AFFECTATION_ENCADRANT
       WHERE id_affectation = ? AND id_etudiant = ? AND statut = 'EN_ATTENTE'`,
    )
    .get(assignmentId, studentId);
  if (!assignment) {
    throw new Error('ASSIGNMENT_NO_LONGER_PENDING');
  }

  const companyId = companyIdForStage(form, offer);
  const stageResult = database
    .prepare(
      `INSERT INTO STAGE
         (id_etudiant, id_encadrant, id_entreprise, id_offre, type, sujet, description,
          ville, origine, nom_tuteur_entreprise, email_tuteur_entreprise, date_debut,
          date_fin, statut_conformite, statut_dossier)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'EN_ATTENTE', 'RECHERCHE')`,
    )
    .run(
      studentId,
      assignment.id_encadrant,
      companyId,
      offer ? offer.id_offre : null,
      form.type,
      form.sujet,
      form.missions,
      form.ville,
      form.origine,
      form.nom_tuteur_entreprise,
      form.email_tuteur_entreprise,
      form.date_debut,
      form.date_fin,
    );
  const stageId = Number(stageResult.lastInsertRowid);

  database
    .prepare(
      `UPDATE BROUILLON_STAGE
       SET id_stage = ?, statut = 'SOUMIS', date_modification = ?
       WHERE id_affectation = ? AND id_etudiant = ?`,
    )
    .run(stageId, new Date().toISOString(), assignmentId, studentId);
  database
    .prepare(`UPDATE AFFECTATION_ENCADRANT SET statut = 'UTILISEE' WHERE id_affectation = ?`)
    .run(assignmentId);

  return stageId;
});

const resubmitCorrectedStage = database.transaction((studentId, stageId, form, offer) => {
  const stage = database
    .prepare(
      `SELECT id_stage, id_encadrant
       FROM STAGE
       WHERE id_stage = ? AND id_etudiant = ? AND statut_conformite = 'REFUSE'`,
    )
    .get(stageId, studentId);
  if (!stage) {
    throw new Error('REFUSED_STAGE_NOT_FOUND');
  }

  const companyId = companyIdForStage(form, offer);
  database
    .prepare(
      `UPDATE STAGE
       SET id_entreprise = ?, id_offre = ?, type = ?, sujet = ?, description = ?,
           ville = ?, origine = ?, nom_tuteur_entreprise = ?, email_tuteur_entreprise = ?,
           date_debut = ?, date_fin = ?, statut_conformite = 'EN_ATTENTE',
           motif_refus = NULL, statut_dossier = 'RECHERCHE'
       WHERE id_stage = ? AND id_etudiant = ?`,
    )
    .run(
      companyId,
      offer ? offer.id_offre : null,
      form.type,
      form.sujet,
      form.missions,
      form.ville,
      form.origine,
      form.nom_tuteur_entreprise,
      form.email_tuteur_entreprise,
      form.date_debut,
      form.date_fin,
      stageId,
      studentId,
    );

  const draft = database
    .prepare('SELECT id_affectation FROM BROUILLON_STAGE WHERE id_stage = ? AND id_etudiant = ?')
    .get(stageId, studentId);
  if (draft) {
    upsertDraft({ studentId, assignmentId: draft.id_affectation, stageId, form });
    database
      .prepare(
        `UPDATE BROUILLON_STAGE
         SET statut = 'SOUMIS', date_modification = ?
         WHERE id_stage = ? AND id_etudiant = ?`,
      )
      .run(new Date().toISOString(), stageId, studentId);
  }

  return stage.id_encadrant;
});

router.get('/service/affectations', stageServiceOnly, (req, res) => {
  const students = database
    .prepare(
      `SELECT id_utilisateur, prenom, nom, email
       FROM UTILISATEUR WHERE role = 'ETUDIANT' ORDER BY nom, prenom`,
    )
    .all();
  const advisors = database
    .prepare(
      `SELECT id_utilisateur, prenom, nom, email
       FROM UTILISATEUR WHERE role = 'ENCADRANT' ORDER BY nom, prenom`,
    )
    .all();
  const assignments = database
    .prepare(
      `SELECT A.id_etudiant, E.prenom || ' ' || E.nom AS etudiant,
              G.prenom || ' ' || G.nom AS encadrant, A.date_affectation
       FROM AFFECTATION_ENCADRANT A
       JOIN UTILISATEUR E ON E.id_utilisateur = A.id_etudiant
       JOIN UTILISATEUR G ON G.id_utilisateur = A.id_encadrant
       WHERE A.statut = 'EN_ATTENTE'
       ORDER BY A.date_affectation DESC`,
    )
    .all();
  const studentOptions = students
    .map(
      (student) =>
        `<option value="${student.id_utilisateur}">${escapeHtml(student.prenom)} ${escapeHtml(student.nom)} — ${escapeHtml(student.email)}</option>`,
    )
    .join('');
  const advisorOptions = advisors
    .map(
      (advisor) =>
        `<option value="${advisor.id_utilisateur}">${escapeHtml(advisor.prenom)} ${escapeHtml(advisor.nom)}</option>`,
    )
    .join('');
  const rows =
    assignments
      .map(
        (assignment) =>
          `<tr><td>${escapeHtml(assignment.etudiant)}</td><td>${escapeHtml(assignment.encadrant)}</td><td>${escapeHtml(assignment.date_affectation)}</td></tr>`,
      )
      .join('') || '<tr><td colspan="3">Aucune affectation en attente.</td></tr>';

  res.send(
    layout(
      'Affecter un encadrant',
      req.session.user,
      `${showMessage(req.query.message)}
        <h1>Affecter un encadrant</h1>
        <p class="intro">Le Service Stages choisit l’encadrant avant que l’étudiant ne commence sa fiche.</p>
        <form class="stage-form" action="/service/affectations" method="post">
          <label for="id_etudiant">Étudiant</label><select id="id_etudiant" name="id_etudiant" required>${studentOptions}</select>
          <label for="id_encadrant">Encadrant pédagogique</label><select id="id_encadrant" name="id_encadrant" required>${advisorOptions}</select>
          <button class="button" type="submit">Enregistrer l’affectation</button>
        </form>
        <h2>Affectations en attente d’une déclaration</h2>
        <div class="table-wrap"><table><thead><tr><th>Étudiant</th><th>Encadrant</th><th>Attribué le</th></tr></thead><tbody>${rows}</tbody></table></div>`,
    ),
  );
});

router.post('/service/affectations', stageServiceOnly, (req, res, next) => {
  const studentId = Number(req.body.id_etudiant);
  const advisorId = Number(req.body.id_encadrant);
  if (!Number.isSafeInteger(studentId) || !Number.isSafeInteger(advisorId)) {
    return res.redirect('/service/affectations?message=error');
  }

  try {
    const assign = database.transaction(() => {
      const student = database
        .prepare(`SELECT 1 FROM UTILISATEUR WHERE id_utilisateur = ? AND role = 'ETUDIANT'`)
        .get(studentId);
      const advisor = database
        .prepare(`SELECT 1 FROM UTILISATEUR WHERE id_utilisateur = ? AND role = 'ENCADRANT'`)
        .get(advisorId);
      if (!student || !advisor) {
        throw new Error('INVALID_ASSIGNMENT_ROLES');
      }

      const previous = database
        .prepare(
          `SELECT id_affectation FROM AFFECTATION_ENCADRANT
           WHERE id_etudiant = ? AND statut = 'EN_ATTENTE'`,
        )
        .get(studentId);
      if (previous) {
        const draft = database
          .prepare(
            `SELECT 1 FROM BROUILLON_STAGE
             WHERE id_affectation = ? AND statut = 'BROUILLON'`,
          )
          .get(previous.id_affectation);
        if (draft) {
          throw new Error('DRAFT_ALREADY_STARTED');
        }
        database
          .prepare(`UPDATE AFFECTATION_ENCADRANT SET statut = 'ANNULEE' WHERE id_affectation = ?`)
          .run(previous.id_affectation);
      }

      database
        .prepare(
          `INSERT INTO AFFECTATION_ENCADRANT
             (id_etudiant, id_encadrant, id_agent, statut, date_affectation)
           VALUES (?, ?, ?, 'EN_ATTENTE', ?)`,
        )
        .run(studentId, advisorId, req.session.user.id, new Date().toISOString());
    });

    assign();
    return res.redirect('/service/affectations?message=assigned');
  } catch (error) {
    if (error.message === 'INVALID_ASSIGNMENT_ROLES' || error.message === 'DRAFT_ALREADY_STARTED') {
      return res.redirect('/service/affectations?message=error');
    }
    return next(error);
  }
});

router.get('/stage', studentOnly, (req, res) => {
  const studentId = req.session.user.id;
  const correctionStage = req.query.correction ? Number(req.query.correction) : null;

  if (correctionStage) {
    const stage = database
      .prepare(
        `SELECT S.id_stage, S.id_entreprise, S.id_offre, S.sujet, S.type, S.ville, S.origine,
                S.nom_tuteur_entreprise, S.email_tuteur_entreprise, S.date_debut, S.date_fin,
                S.description AS missions, E.raison_sociale AS entreprise,
                B.id_affectation
         FROM STAGE S
         JOIN ENTREPRISE E ON E.id_entreprise = S.id_entreprise
         LEFT JOIN BROUILLON_STAGE B ON B.id_stage = S.id_stage
         WHERE S.id_stage = ? AND S.id_etudiant = ? AND S.statut_conformite = 'REFUSE'`,
      )
      .get(correctionStage, studentId);
    if (!stage) {
      return res.status(404).send('Cette fiche refusée est introuvable.');
    }
    return res.send(
      renderStageForm({
        user: req.session.user,
        form: stage,
        offers: loadPublishedOffers(),
        action: 'correction',
        title: 'Corriger ma fiche de stage',
        notice: req.query.message,
      }),
    );
  }

  const assignment = getPendingAssignment(studentId);
  const currentDraft = assignment
    ? database
        .prepare('SELECT * FROM BROUILLON_STAGE WHERE id_affectation = ? AND statut = \'BROUILLON\'')
        .get(assignment.id_affectation)
    : null;
  const stages = database
    .prepare(
      `SELECT S.id_stage, S.sujet, S.type, S.statut_conformite, S.motif_refus,
              E.raison_sociale AS entreprise, U.prenom || ' ' || U.nom AS encadrant
       FROM STAGE S
       JOIN ENTREPRISE E ON E.id_entreprise = S.id_entreprise
       JOIN UTILISATEUR U ON U.id_utilisateur = S.id_encadrant
       WHERE S.id_etudiant = ?
       ORDER BY S.id_stage DESC`,
    )
    .all(studentId);
  const stageRows =
    stages
      .map((stage) => {
        const correction =
          stage.statut_conformite === 'REFUSE'
            ? ` <a class="button-link" href="/stage?correction=${stage.id_stage}">Corriger et renvoyer</a>`
            : '';
        const status =
          stage.statut_conformite === 'CONFORME'
            ? 'Conforme'
            : stage.statut_conformite === 'REFUSE'
              ? `Refusé — ${escapeHtml(stage.motif_refus)}`
              : 'En attente de vérification';
        return `<tr><td>${escapeHtml(stage.entreprise)}</td><td>${escapeHtml(stage.sujet)}</td><td>${status}</td><td>${escapeHtml(stage.encadrant)}${correction}</td></tr>`;
      })
      .join('') || '<tr><td colspan="4">Aucune fiche soumise pour le moment.</td></tr>';

  if (!assignment && !currentDraft) {
    return res.send(
      layout(
        'Déclarer mon stage',
        req.session.user,
        `${showMessage(req.query.message)}
          <h1>Déclarer mon stage</h1>
          <p class="intro">Le Service Stages doit d’abord attribuer un encadrant avant la création de votre fiche.</p>
          <h2>Mes stages</h2><div class="table-wrap"><table><thead><tr><th>Entreprise</th><th>Sujet</th><th>État</th><th>Encadrant / action</th></tr></thead><tbody>${stageRows}</tbody></table></div>`,
      ),
    );
  }

  return res.send(
    renderStageForm({
      user: req.session.user,
      form: currentDraft || {},
      offers: loadPublishedOffers(),
      title: 'Déclarer mon stage',
      notice: req.query.message,
      extraContent: `<section class="stage-list">
        <h2>Mes stages</h2>
        <div class="table-wrap"><table><thead><tr><th>Entreprise</th><th>Sujet</th><th>État</th><th>Encadrant / action</th></tr></thead><tbody>${stageRows}</tbody></table></div>
      </section>`,
    }),
  );
});

router.post('/stage/enregistrer', studentOnly, (req, res, next) => {
  const studentId = req.session.user.id;
  const assignment = getPendingAssignment(studentId);
  if (!assignment) {
    return res.status(409).send('Le Service Stages doit attribuer un encadrant avant la déclaration.');
  }

  const form = readForm(req.body);
  try {
    upsertDraft({ studentId, assignmentId: assignment.id_affectation, form });
    if (req.body.action === 'brouillon') {
      return res.redirect('/stage?message=saved');
    }

    const validationError = validateStageForm(form);
    const offerResult = validationError ? null : validateOffer(form);
    if (validationError || (offerResult && offerResult.error)) {
      return res.redirect('/stage?message=error');
    }

    createStageFromDraft(
      studentId,
      assignment.id_affectation,
      form,
      offerResult ? offerResult.offer : null,
    );
    return res.redirect('/stage?message=submitted');
  } catch (error) {
    if (error.message === 'ASSIGNMENT_NO_LONGER_PENDING') {
      return res.status(409).send('Cette affectation a déjà été utilisée. Contactez le Service Stages.');
    }
    return next(error);
  }
});

router.post('/stage/:id/corriger', studentOnly, (req, res, next) => {
  const stageId = Number(req.params.id);
  if (!Number.isSafeInteger(stageId)) {
    return res.status(404).send('Cette fiche est introuvable.');
  }

  const form = readForm(req.body);
  const validationError = validateStageForm(form);
  const offerResult = validationError ? null : validateOffer(form);
  if (validationError || (offerResult && offerResult.error)) {
    return res.redirect(`/stage?correction=${stageId}&message=error`);
  }

  try {
    const advisorId = resubmitCorrectedStage(
      req.session.user.id,
      stageId,
      form,
      offerResult ? offerResult.offer : null,
    );
    database
      .prepare(
        `UPDATE BROUILLON_STAGE
         SET statut = 'SOUMIS', date_modification = ?
         WHERE id_stage = ? AND id_etudiant = ?`,
      )
      .run(new Date().toISOString(), stageId, req.session.user.id);
    return res.redirect('/stage?message=submitted');
  } catch (error) {
    if (error.message === 'REFUSED_STAGE_NOT_FOUND') {
      return res.status(404).send('Cette fiche refusée est introuvable.');
    }
    if (error.message === 'ASSIGNMENT_NO_LONGER_PENDING') {
      return res.status(409).send('Cette affectation a déjà été utilisée.');
    }
    return next(error);
  }
});

router.get('/encadrant/stages', advisorOnly, (req, res) => {
  const stages = database
    .prepare(
      `SELECT S.id_stage, S.sujet, S.type, S.ville, S.origine, S.date_debut, S.date_fin,
              S.description AS missions, S.nom_tuteur_entreprise, S.email_tuteur_entreprise,
              S.statut_conformite, S.motif_refus,
              E.raison_sociale AS entreprise, U.prenom || ' ' || U.nom AS etudiant
       FROM STAGE S
       JOIN ENTREPRISE E ON E.id_entreprise = S.id_entreprise
       JOIN UTILISATEUR U ON U.id_utilisateur = S.id_etudiant
       WHERE S.id_encadrant = ?
       ORDER BY CASE S.statut_conformite WHEN 'EN_ATTENTE' THEN 0 ELSE 1 END, S.id_stage DESC`,
    )
    .all(req.session.user.id);
  const cards =
    stages
      .map((stage) => {
        const decisionForm =
          stage.statut_conformite === 'EN_ATTENTE'
            ? `<form class="decision-form" action="/encadrant/stages/${stage.id_stage}/decision" method="post">
                <label for="commentaire-${stage.id_stage}">Motif si refus (obligatoire en cas de refus)</label>
                <textarea id="commentaire-${stage.id_stage}" name="commentaire" rows="2" maxlength="1000"></textarea>
                <div class="form-actions">
                  <button class="button" type="submit" name="decision" value="CONFORME">Conforme</button>
                  <button class="button button-danger" type="submit" name="decision" value="REFUSE">Refuser</button>
                </div>
              </form>`
            : `<p class="status-pill">${stage.statut_conformite === 'CONFORME' ? 'Conforme' : `Refusé — ${escapeHtml(stage.motif_refus)}`}</p>`;
        return `<article class="review-card">
          <h2>${escapeHtml(stage.etudiant)} — ${escapeHtml(stage.entreprise)}</h2>
          <p><strong>${escapeHtml(stage.type)} :</strong> ${escapeHtml(stage.sujet)}</p>
          <dl class="stage-details">
            <dt>Ville</dt><dd>${escapeHtml(stage.ville)}</dd>
            <dt>Origine</dt><dd>${escapeHtml(ORIGINS[stage.origine])}</dd>
            <dt>Dates</dt><dd>${escapeHtml(stage.date_debut)} au ${escapeHtml(stage.date_fin)}</dd>
            <dt>Tuteur en entreprise</dt><dd>${escapeHtml(stage.nom_tuteur_entreprise)} — ${escapeHtml(stage.email_tuteur_entreprise)}</dd>
            <dt>Missions</dt><dd>${escapeHtml(stage.missions)}</dd>
          </dl>${decisionForm}</article>`;
      })
      .join('') || '<p>Aucune fiche ne vous a été attribuée.</p>';

  res.send(
    layout(
      'Vérifier la conformité du stage',
      req.session.user,
      `${showMessage(req.query.message)}
        <h1>Fiches de stage à vérifier</h1>
        <p class="intro">Vérifiez les informations puis choisissez si le sujet correspond au cursus. Un motif est exigé en cas de refus.</p>
        <section class="review-list">${cards}</section>`,
    ),
  );
});

router.post('/encadrant/stages/:id/decision', advisorOnly, (req, res, next) => {
  const stageId = Number(req.params.id);
  const decision = req.body.decision;
  const comment = typeof req.body.commentaire === 'string' ? req.body.commentaire.trim() : '';
  if (!Number.isSafeInteger(stageId) || !['CONFORME', 'REFUSE'].includes(decision)) {
    return res.redirect('/encadrant/stages?message=error');
  }
  if (decision === 'REFUSE' && !comment) {
    return res.redirect('/encadrant/stages?message=error');
  }

  try {
    const saveDecision = database.transaction(() => {
      const stage = database
        .prepare(
          `SELECT id_stage
           FROM STAGE
           WHERE id_stage = ? AND id_encadrant = ? AND statut_conformite = 'EN_ATTENTE'`,
        )
        .get(stageId, req.session.user.id);
      if (!stage) {
        throw new Error('STAGE_NOT_ASSIGNED_OR_PENDING');
      }

      const date = new Date().toISOString();
      database
        .prepare(
          `INSERT INTO VALIDATION_STAGE
             (id_stage, id_validateur, decision, commentaire, date_decision)
           VALUES (?, ?, ?, ?, ?)`,
        )
        .run(stageId, req.session.user.id, decision, comment || null, date);
      database
        .prepare(
          `UPDATE STAGE
           SET statut_conformite = ?, motif_refus = ?,
               statut_dossier = CASE WHEN ? = 'CONFORME' THEN 'CONVENTION' ELSE 'RECHERCHE' END
           WHERE id_stage = ?`,
        )
        .run(decision, decision === 'REFUSE' ? comment : null, decision, stageId);
    });

    saveDecision();
    return res.redirect('/encadrant/stages?message=decided');
  } catch (error) {
    if (error.message === 'STAGE_NOT_ASSIGNED_OR_PENDING') {
      return res.status(404).send('Cette fiche n’est pas en attente pour votre compte.');
    }
    return next(error);
  }
});

module.exports = router;
