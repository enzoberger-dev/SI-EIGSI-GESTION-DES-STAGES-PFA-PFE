const fs = require('node:fs');
const path = require('node:path');
const PDFDocument = require('pdfkit');
const express = require('express');
const database = require('../db/database');
const requireAuth = require('../middleware/require-auth');
const requireRoles = require('../middleware/require-roles');

const router = express.Router();
const serviceOnly = requireRoles('SERVICE_STAGES');
const rolesWithConventionAccess = ['ETUDIANT', 'ENCADRANT', 'SERVICE_STAGES', 'RESPONSABLE'];
const pdfDirectory = path.join(__dirname, '..', '..', 'uploads', 'conventions');
const stageForPdf = database.prepare(
  `SELECT S.id_stage, S.type, S.sujet, S.description, S.ville, S.date_debut, S.date_fin,
          S.statut_conformite,
          S.nom_tuteur_entreprise, S.email_tuteur_entreprise,
          E.raison_sociale AS entreprise, E.contact_email AS email_entreprise,
          Student.prenom || ' ' || Student.nom AS etudiant,
          Student.email AS email_etudiant,
          Advisor.prenom || ' ' || Advisor.nom AS encadrant
   FROM STAGE S
   JOIN ENTREPRISE E ON E.id_entreprise = S.id_entreprise
   JOIN UTILISATEUR Student ON Student.id_utilisateur = S.id_etudiant
   JOIN UTILISATEUR Advisor ON Advisor.id_utilisateur = S.id_encadrant
   WHERE S.id_stage = ?`,
);

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
    <link rel="stylesheet" href="/css/conventions.css">
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
    generated: '<p class="success-message" role="status">Le PDF de la convention a été généré.</p>',
    validated: '<p class="success-message" role="status">Votre validation a été enregistrée.</p>',
    refused: '<p class="success-message" role="status">La convention est refusée. L’étudiant peut corriger sa fiche de stage.</p>',
    error: '<p class="error-message" role="alert">Vérifiez les renseignements, le commentaire de refus et l’ordre des validations.</p>',
  };
  return messages[code] || '';
}

function conventionStatus(status) {
  return {
    EN_VALIDATION: 'En cours de validation',
    VALIDEE: 'Validée par les trois niveaux',
    REFUSEE: 'Refusée — correction de la fiche attendue',
  }[status] || status;
}

function nextLevel(database, convention) {
  const rows = database
    .prepare(
      `SELECT niveau, decision
       FROM VALIDATION_CONVENTION
       WHERE id_convention = ? AND cycle = ?
       ORDER BY niveau`,
    )
    .all(convention.id_convention, convention.cycle);
  if (rows.some((row) => row.decision === 'REFUSE')) {
    return null;
  }
  return rows.length + 1;
}

function userCanValidate(user, level, stage) {
  if (level === 1) {
    return user.role === 'ENCADRANT' && user.id === stage.id_encadrant;
  }
  if (level === 2) {
    return user.role === 'SERVICE_STAGES';
  }
  return level === 3 && user.role === 'RESPONSABLE';
}

function authorizedForStage(user, stage) {
  if (user.role === 'ETUDIANT') {
    return user.id === stage.id_etudiant;
  }
  if (user.role === 'ENCADRANT') {
    return user.id === stage.id_encadrant;
  }
  return user.role === 'SERVICE_STAGES' || user.role === 'RESPONSABLE';
}

function renderPdf(conventionNumber, stage) {
  return new Promise((resolve, reject) => {
    const document = new PDFDocument({ size: 'A4', margin: 54, info: { Title: `Convention ${conventionNumber}` } });
    const chunks = [];
    document.on('data', (chunk) => chunks.push(chunk));
    document.on('error', reject);
    document.on('end', () => resolve(Buffer.concat(chunks)));

    document.fontSize(10).fillColor('#24506f').text('EIGSI CASABLANCA', { align: 'center' });
    document.moveDown(0.5);
    document.fontSize(19).fillColor('#163b59').text('CONVENTION DE STAGE', { align: 'center' });
    document.moveDown(0.35);
    document.fontSize(11).fillColor('#52687b').text(conventionNumber, { align: 'center' });
    document.moveDown(1.4);

    const field = (label, value) => {
      document.fontSize(10).fillColor('#24506f').text(label, { continued: true });
      document.fontSize(11).fillColor('#172b3a').text(`  ${value || 'Non renseigné'}`);
      document.moveDown(0.55);
    };

    field('Étudiant :', `${stage.etudiant} (${stage.email_etudiant})`);
    field('Entreprise :', `${stage.entreprise} — ${stage.ville}`);
    field('Contact entreprise :', stage.email_entreprise);
    field('Encadrant pédagogique :', stage.encadrant);
    field('Type de stage :', stage.type);
    field('Sujet :', stage.sujet);
    field('Dates du stage :', `du ${stage.date_debut} au ${stage.date_fin}`);
    field('Tuteur en entreprise :', `${stage.nom_tuteur_entreprise} (${stage.email_tuteur_entreprise})`);
    document.fontSize(10).fillColor('#24506f').text('Missions principales :');
    document.moveDown(0.3);
    document.fontSize(11).fillColor('#172b3a').text(stage.description, { align: 'left' });
    document.moveDown(2);
    document.fontSize(9).fillColor('#52687b').text(
      'Document généré par l’application de gestion des stages. La convention est soumise aux validations de l’école ; ce PDF ne constitue pas une signature électronique.',
      { align: 'left' },
    );
    document.end();
  });
}

router.get('/conventions', requireAuth, requireRoles(...rolesWithConventionAccess), (req, res, next) => {
  try {
    const user = req.session.user;
    let stageFilter = '';
    const parameters = [];
    if (user.role === 'ETUDIANT') {
      stageFilter = 'WHERE S.id_etudiant = ?';
      parameters.push(user.id);
    } else if (user.role === 'ENCADRANT') {
      stageFilter = 'WHERE S.id_encadrant = ?';
      parameters.push(user.id);
    }

    const records = database
      .prepare(
        `SELECT S.id_stage, S.id_etudiant, S.id_encadrant, S.type, S.sujet,
                S.statut_conformite, S.motif_refus,
                E.raison_sociale AS entreprise,
                Student.prenom || ' ' || Student.nom AS etudiant,
                C.id_convention, C.numero, C.pdf_path, C.statut AS convention_statut,
                C.cycle, C.date_creation
         FROM STAGE S
         JOIN ENTREPRISE E ON E.id_entreprise = S.id_entreprise
         JOIN UTILISATEUR Student ON Student.id_utilisateur = S.id_etudiant
         LEFT JOIN CONVENTION C ON C.id_stage = S.id_stage
         ${stageFilter}
         ORDER BY S.id_stage DESC`,
      )
      .all(...parameters);

    const conventionCards = records
      .filter((record) => record.id_convention)
      .map((record) => {
        const stage = database
          .prepare('SELECT id_etudiant, id_encadrant FROM STAGE WHERE id_stage = ?')
          .get(record.id_stage);
        const level = record.convention_statut === 'EN_VALIDATION' ? nextLevel(database, record) : null;
        const mayValidate =
          level && userCanValidate(user, level, stage) && record.pdf_path;
        const history = database
          .prepare(
            `SELECT V.cycle, V.niveau, V.decision, V.commentaire, V.date_decision,
                    U.prenom || ' ' || U.nom AS validateur
             FROM VALIDATION_CONVENTION V
             JOIN UTILISATEUR U ON U.id_utilisateur = V.id_validateur
             WHERE V.id_convention = ?
             ORDER BY V.cycle DESC, V.niveau`,
          )
          .all(record.id_convention)
          .map(
            (entry) =>
              `<li>Cycle ${entry.cycle} — ${['', 'Encadrant', 'Service Stages', 'Responsable'][entry.niveau]} : ${entry.decision === 'VALIDE' ? 'validé' : 'refusé'} par ${escapeHtml(entry.validateur)} le ${escapeHtml(entry.date_decision)}${entry.commentaire ? ` — ${escapeHtml(entry.commentaire)}` : ''}</li>`,
          )
          .join('');
        const correctionLink =
          user.role === 'ETUDIANT' &&
          user.id === record.id_etudiant &&
          record.convention_statut === 'REFUSEE' &&
          record.statut_conformite === 'REFUSE'
            ? `<a class="button-link" href="/stage?correction=${record.id_stage}">Corriger ma fiche puis la renvoyer</a>`
            : '';
        const correctionProgress =
          record.convention_statut === 'REFUSEE' && record.statut_conformite === 'EN_ATTENTE'
            ? '<p class="correction-progress">La fiche corrigée attend la revalidation de l’encadrant.</p>'
            : record.convention_statut === 'REFUSEE' && record.statut_conformite === 'CONFORME'
              ? '<p class="correction-progress">La fiche est conforme ; le Service Stages peut générer une nouvelle version du PDF.</p>'
              : '';
        const validationForm = mayValidate
          ? `<form class="convention-decision" action="/conventions/${record.id_convention}/decision" method="post">
              <label for="comment-${record.id_convention}">Commentaire (obligatoire en cas de refus)</label>
              <textarea id="comment-${record.id_convention}" name="commentaire" rows="3" maxlength="1000"></textarea>
              <div class="convention-actions">
                <button class="button" type="submit" name="decision" value="VALIDE">Valider — niveau ${level}</button>
                <button class="button button-danger" type="submit" name="decision" value="REFUSE">Refuser</button>
              </div>
            </form>`
          : '';

        return `<article class="convention-card">
          <div class="convention-heading">
            <div><p class="eyebrow">${escapeHtml(record.type)} · ${escapeHtml(record.etudiant)}</p><h2>${escapeHtml(record.numero)}</h2></div>
            <span class="convention-status">${escapeHtml(conventionStatus(record.convention_statut))}</span>
          </div>
          <p><strong>Entreprise :</strong> ${escapeHtml(record.entreprise)} · <strong>Sujet :</strong> ${escapeHtml(record.sujet)}</p>
          <p><strong>Version :</strong> ${record.cycle} · <strong>Créée :</strong> ${escapeHtml(record.date_creation)}</p>
          ${record.pdf_path ? `<a class="button-link" href="/conventions/${record.id_convention}/pdf">Ouvrir le PDF de la convention</a>` : ''}
          ${correctionProgress}
          ${record.convention_statut === 'REFUSEE' && record.statut_conformite === 'CONFORME' && user.role === 'SERVICE_STAGES' ? `<form class="regenerate-form" action="/conventions/stages/${record.id_stage}/generer" method="post"><button class="button" type="submit">Régénérer après correction et relancer les validations</button></form>` : ''}
          ${correctionLink}
          ${validationForm}
          ${history ? `<details class="validation-history"><summary>Historique des validations</summary><ul>${history}</ul></details>` : '<p>Aucune validation enregistrée pour cette convention.</p>'}
        </article>`;
      })
      .join('');

    const eligibleStages =
      user.role === 'SERVICE_STAGES'
        ? records
            .filter(
              (record) =>
                record.statut_conformite === 'CONFORME' &&
                (!record.id_convention ||
                  record.convention_statut === 'REFUSEE' ||
                  (record.convention_statut === 'EN_VALIDATION' && !record.pdf_path)),
            )
            .map(
              (record) =>
                `<tr><td>${escapeHtml(record.etudiant)}</td><td>${escapeHtml(record.entreprise)}</td><td>${escapeHtml(record.sujet)}</td><td>${record.id_convention ? `Convention ${escapeHtml(record.numero)} — nouvelle version` : 'À générer'}</td><td><form action="/conventions/stages/${record.id_stage}/generer" method="post"><button class="button" type="submit">${record.id_convention ? 'Régénérer le PDF' : 'Générer le PDF'}</button></form></td></tr>`,
            )
            .join('')
        : '';

    res.send(
      layout(
        'Conventions',
        user,
        `${showMessage(req.query.message)}
          <h1>${user.role === 'ETUDIANT' ? 'Suivre ma convention' : 'Conventions de stage'}</h1>
          <p class="intro">Le PDF est généré après validation de la fiche de stage. Les validations se font dans l’ordre : encadrant, Service Stages, responsable.</p>
          ${eligibleStages ? `<section class="convention-section"><h2>Stages conformes à préparer</h2><div class="convention-table-wrap"><table><thead><tr><th>Étudiant</th><th>Entreprise</th><th>Sujet</th><th>État</th><th>Action</th></tr></thead><tbody>${eligibleStages || '<tr><td colspan="5">Aucun stage conforme à préparer.</td></tr>'}</tbody></table></div></section>` : ''}
          <section class="convention-list" aria-label="Conventions">
            ${conventionCards || '<p>Aucune convention à afficher pour votre compte.</p>'}
          </section>`,
      ),
    );
  } catch (error) {
    return next(error);
  }
});

router.post('/conventions/stages/:stageId/generer', serviceOnly, async (req, res, next) => {
  const stageId = Number(req.params.stageId);
  if (!Number.isSafeInteger(stageId)) {
    return res.status(404).send('Ce stage est introuvable.');
  }

  let createdFile = null;
  try {
    const stage = stageForPdf.get(stageId);
    if (!stage || stage.statut_conformite !== 'CONFORME') {
      return res.status(409).send('La convention ne peut être générée que pour un stage conforme.');
    }

    const existing = database
      .prepare('SELECT id_convention, numero, cycle, statut, pdf_path FROM CONVENTION WHERE id_stage = ?')
      .get(stageId);
    const canRepairMissingPdf =
      existing && existing.statut === 'EN_VALIDATION' && !existing.pdf_path;
    if (existing && existing.statut !== 'REFUSEE' && !canRepairMissingPdf) {
      return res.status(409).send('Cette convention est déjà en cours de validation ou elle est validée.');
    }

    const currentYear = new Date().getFullYear();
    const number = existing ? existing.numero : `CONV-${currentYear}-${String(stageId).padStart(4, '0')}`;
    const cycle = existing
      ? canRepairMissingPdf
        ? existing.cycle
        : existing.cycle + 1
      : 1;
    const fileName = `convention-stage-${stageId}-cycle-${cycle}.pdf`;
    const relativePath = path.join('conventions', fileName);
    const absolutePath = path.join(pdfDirectory, fileName);
    const pdf = await renderPdf(number, stage);
    await fs.promises.mkdir(pdfDirectory, { recursive: true });
    await fs.promises.writeFile(absolutePath, pdf, { flag: 'wx' });
    createdFile = absolutePath;

    const createOrRenew = database.transaction(() => {
      const currentStage = database
        .prepare('SELECT statut_conformite FROM STAGE WHERE id_stage = ?')
        .get(stageId);
      if (!currentStage || currentStage.statut_conformite !== 'CONFORME') {
        throw new Error('STAGE_NOT_CONFORME');
      }
      const currentConvention = database
        .prepare('SELECT id_convention, cycle, statut FROM CONVENTION WHERE id_stage = ?')
        .get(stageId);
      if (!currentConvention) {
        database
          .prepare(
            `INSERT INTO CONVENTION (id_stage, numero, pdf_path, statut, date_creation)
             VALUES (?, ?, ?, 'EN_VALIDATION', ?)`,
          )
            .run(stageId, number, relativePath, new Date().toISOString());
      } else if (
        currentConvention.statut === 'EN_VALIDATION' &&
        !existing.pdf_path &&
        currentConvention.cycle === cycle
      ) {
        database
          .prepare('UPDATE CONVENTION SET pdf_path = ? WHERE id_convention = ? AND pdf_path IS NULL')
          .run(relativePath, currentConvention.id_convention);
      } else {
        if (currentConvention.statut !== 'REFUSEE' || currentConvention.cycle + 1 !== cycle) {
          throw new Error('CONVENTION_ALREADY_CHANGED');
        }
        database
          .prepare(
            `UPDATE CONVENTION
             SET pdf_path = ?, statut = 'EN_VALIDATION', cycle = ?, date_creation = ?
             WHERE id_convention = ? AND statut = 'REFUSEE'`,
          )
          .run(relativePath, cycle, new Date().toISOString(), currentConvention.id_convention);
      }
    });
    createOrRenew();
    createdFile = null;
    return res.redirect('/conventions?message=generated');
  } catch (error) {
    if (createdFile) {
      try {
        await fs.promises.unlink(createdFile);
      } catch (cleanupError) {
        if (cleanupError.code !== 'ENOENT') {
          return next(cleanupError);
        }
      }
    }
    if (error.message === 'STAGE_NOT_CONFORME') {
      return res.status(409).send('La fiche doit être conforme avant de générer la convention.');
    }
    if (error.message === 'CONVENTION_ALREADY_CHANGED') {
      return res.status(409).send('La convention a changé pendant la génération. Actualisez la page.');
    }
    return next(error);
  }
});

router.post('/conventions/:id/decision', requireAuth, requireRoles('ENCADRANT', 'SERVICE_STAGES', 'RESPONSABLE'), (req, res, next) => {
  const conventionId = Number(req.params.id);
  const decision = req.body.decision;
  const comment = typeof req.body.commentaire === 'string' ? req.body.commentaire.trim() : '';
  if (!Number.isSafeInteger(conventionId) || !['VALIDE', 'REFUSE'].includes(decision)) {
    return res.redirect('/conventions?message=error');
  }
  if (decision === 'REFUSE' && !comment) {
    return res.redirect('/conventions?message=error');
  }

  try {
    const saveDecision = database.transaction(() => {
      const convention = database
        .prepare(
          `SELECT C.id_convention, C.id_stage, C.cycle, C.statut,
                  S.id_etudiant, S.id_encadrant, S.statut_conformite
           FROM CONVENTION C
           JOIN STAGE S ON S.id_stage = C.id_stage
           WHERE C.id_convention = ?`,
        )
        .get(conventionId);
      if (!convention || convention.statut !== 'EN_VALIDATION') {
        throw new Error('CONVENTION_NOT_PENDING');
      }

      const level = nextLevel(database, convention);
      if (!userCanValidate(req.session.user, level, convention)) {
        throw new Error('WRONG_VALIDATOR_OR_ORDER');
      }

      const date = new Date().toISOString();
      database
        .prepare(
          `INSERT INTO VALIDATION_CONVENTION
             (id_convention, cycle, id_validateur, niveau, decision, commentaire, date_decision)
           VALUES (?, ?, ?, ?, ?, ?, ?)`,
        )
        .run(conventionId, convention.cycle, req.session.user.id, level, decision, comment || null, date);

      if (decision === 'REFUSE') {
        database
          .prepare("UPDATE CONVENTION SET statut = 'REFUSEE' WHERE id_convention = ?")
          .run(conventionId);
        database
          .prepare(
            `UPDATE STAGE
             SET statut_conformite = 'REFUSE', motif_refus = ?, statut_dossier = 'RECHERCHE'
             WHERE id_stage = ?`,
          )
          .run(comment, convention.id_stage);
      } else if (level === 3) {
        database
          .prepare("UPDATE CONVENTION SET statut = 'VALIDEE' WHERE id_convention = ?")
          .run(conventionId);
      }
    });
    saveDecision();
    return res.redirect(`/conventions?message=${decision === 'REFUSE' ? 'refused' : 'validated'}`);
  } catch (error) {
    if (error.message === 'CONVENTION_NOT_PENDING' || error.message === 'WRONG_VALIDATOR_OR_ORDER') {
      return res.status(409).send('Cette validation n’est pas disponible pour votre rôle ou à cette étape.');
    }
    return next(error);
  }
});

router.get('/conventions/:id/pdf', requireAuth, requireRoles(...rolesWithConventionAccess), (req, res, next) => {
  const conventionId = Number(req.params.id);
  if (!Number.isSafeInteger(conventionId)) {
    return res.status(404).send('Ce document est introuvable.');
  }

  try {
    const convention = database
      .prepare(
        `SELECT C.numero, C.pdf_path, S.id_etudiant, S.id_encadrant
         FROM CONVENTION C
         JOIN STAGE S ON S.id_stage = C.id_stage
         WHERE C.id_convention = ?`,
      )
      .get(conventionId);
    if (!convention || !authorizedForStage(req.session.user, convention)) {
      return res.status(404).send('Ce document est introuvable pour votre compte.');
    }
    if (!convention.pdf_path || !/^conventions[\\/]+convention-stage-\d+-cycle-\d+\.pdf$/.test(convention.pdf_path)) {
      return res.status(404).send('Le PDF de cette convention n’est pas disponible.');
    }

    const absolutePath = path.join(pdfDirectory, path.basename(convention.pdf_path));
    return res.download(absolutePath, `${convention.numero}.pdf`, (error) => {
      if (error && !res.headersSent) {
        return next(error);
      }
      return undefined;
    });
  } catch (error) {
    return next(error);
  }
});

module.exports = router;
