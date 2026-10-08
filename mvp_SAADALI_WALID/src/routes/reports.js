const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const express = require('express');
const multer = require('multer');
const database = require('../db/database');
const requireRoles = require('../middleware/require-roles');

const router = express.Router();
const studentOnly = requireRoles('ETUDIANT');
const advisorOnly = requireRoles('ENCADRANT');
const reportDirectory = path.join(__dirname, '..', '..', 'uploads', 'rapports');
const maximumFileSize = 10 * 1024 * 1024;
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: maximumFileSize, files: 1 },
  fileFilter: (_req, file, callback) => {
    if (file.mimetype !== 'application/pdf') {
      return callback(new Error('PDF_ONLY'));
    }
    return callback(null, true);
  },
});

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
    <link rel="stylesheet" href="/css/reports.css">
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
    uploaded: '<p class="success-message" role="status">Votre dépôt a été enregistré.</p>',
    correction: '<p class="success-message" role="status">La demande de correction a été enregistrée.</p>',
    evaluated: '<p class="success-message" role="status">L’évaluation a été enregistrée.</p>',
    error: '<p class="error-message" role="alert">Le dépôt ou l’action n’a pas pu être effectué. Vérifiez les informations et réessayez.</p>',
    'invalid-file': '<p class="error-message" role="alert">Le fichier doit être un véritable document PDF.</p>',
    'file-too-large': '<p class="error-message" role="alert">Le fichier dépasse la taille maximale de 10 Mo.</p>',
    'file-missing': '<p class="error-message" role="alert">Choisissez un fichier PDF avant de l’envoyer.</p>',
    'date-not-reached': '<p class="error-message" role="alert">Le dépôt sera possible à partir de la date de fin de votre stage.</p>',
    'report-pending': '<p class="error-message" role="alert">Votre dépôt actuel est encore en cours de vérification. Attendez le retour de votre encadrant.</p>',
    'report-closed': '<p class="error-message" role="alert">Ce rapport a déjà été évalué et ne peut pas être remplacé.</p>',
  };
  return Object.hasOwn(messages, code) ? messages[code] : '';
}

function statusLabel(status) {
  return {
    DEPOSE: 'Déposé — en attente de vérification',
    A_CORRIGER: 'À corriger',
    CORRIGE: 'Évalué',
  }[status] || status;
}

function uploadFile(req, res, next) {
  upload.single('rapport')(req, res, (error) => {
    if (error instanceof multer.MulterError) {
      if (error.code === 'LIMIT_FILE_SIZE') {
        return res.redirect('/rapports?message=file-too-large');
      }
      if (error.code === 'LIMIT_UNEXPECTED_FILE') {
        return res.redirect('/rapports?message=invalid-file');
      }
      return next(error);
    }
    if (error && error.message === 'PDF_ONLY') {
      return res.redirect('/rapports?message=invalid-file');
    }
    if (error) {
      return next(error);
    }
    return next();
  });
}

function canAccessReport(user, report) {
  return (
    (user.role === 'ETUDIANT' && user.id === report.id_etudiant) ||
    (user.role === 'ENCADRANT' && user.id === report.id_encadrant)
  );
}

function resolveReportPath(storedPath) {
  if (typeof storedPath !== 'string' || !/^rapports[\\/][0-9a-f-]{36}\.pdf$/i.test(storedPath)) {
    return null;
  }
  return path.join(reportDirectory, path.basename(storedPath));
}

function reportFileLink(report) {
  const absolutePath = resolveReportPath(report.fichier_path);
  return absolutePath && fs.existsSync(absolutePath)
    ? `<a class="button-link" href="/rapports/${report.id_depot_rapport}/fichier">Ouvrir le PDF</a>`
    : '<span class="report-file-missing">Fichier PDF indisponible</span>';
}

router.get('/rapports', studentOnly, (req, res, next) => {
  try {
    const stages = database
      .prepare(
        `SELECT S.id_stage, S.type, S.sujet, S.date_fin, S.statut_dossier,
                E.raison_sociale AS entreprise,
                U.prenom || ' ' || U.nom AS encadrant
         FROM STAGE S
         JOIN ENTREPRISE E ON E.id_entreprise = S.id_entreprise
         JOIN UTILISATEUR U ON U.id_utilisateur = S.id_encadrant
         WHERE S.id_etudiant = ?
         ORDER BY S.id_stage DESC`,
      )
      .all(req.session.user.id);
    const reportsForStage = database.prepare(
      `SELECT R.id_depot_rapport, R.fichier_path, R.date_depot, R.statut,
              R.commentaire_encadrant, V.commentaire AS evaluation_commentaire, V.note
       FROM DEPOT_RAPPORT_FINAL R
       LEFT JOIN EVALUATION_RAPPORT V ON V.id_depot_rapport = R.id_depot_rapport
       WHERE R.id_stage = ?
       ORDER BY R.id_depot_rapport DESC`,
    );
    const today = new Date().toISOString().slice(0, 10);
    const cards =
      stages
        .map((stage) => {
          const reports = reportsForStage.all(stage.id_stage);
          const latest = reports[0];
          const canUpload = stage.date_fin <= today && (!latest || latest.statut === 'A_CORRIGER');
          const uploadForm = canUpload
            ? `<form class="report-upload" action="/rapports/stages/${stage.id_stage}/deposer" method="post" enctype="multipart/form-data">
                <label for="rapport-${stage.id_stage}">${latest ? 'Choisissez le PDF corrigé' : 'Choisissez votre rapport final au format PDF'}</label>
                <input id="rapport-${stage.id_stage}" name="rapport" type="file" accept="application/pdf,.pdf" required>
                <p class="help-text">Un fichier PDF de 10 Mo maximum. Chaque nouvel envoi est conservé dans l’historique.</p>
                <button class="button" type="submit">${latest ? 'Envoyer la version corrigée' : 'Déposer mon rapport final'}</button>
              </form>`
            : stage.date_fin > today
              ? `<p class="report-notice">Le dépôt sera disponible à partir du ${escapeHtml(stage.date_fin)}, après la fin prévue du stage.</p>`
              : latest && latest.statut === 'DEPOSE'
                ? '<p class="report-notice">Votre dépôt le plus récent attend le retour de votre encadrant.</p>'
                : latest && latest.statut === 'CORRIGE'
                  ? '<p class="report-notice">Votre rapport a été évalué ; aucun nouveau dépôt n’est attendu.</p>'
                  : '';
          const history =
            reports
              .map(
                (report) =>
                  `<li class="report-history-item">
                    <div><strong>${escapeHtml(statusLabel(report.statut))}</strong><span> · Déposé le ${escapeHtml(report.date_depot)}</span></div>
                    ${reportFileLink(report)}
                    ${report.commentaire_encadrant ? `<p><strong>Retour de l’encadrant :</strong> ${escapeHtml(report.commentaire_encadrant)}</p>` : ''}
                    ${report.evaluation_commentaire ? `<p><strong>Évaluation :</strong> ${escapeHtml(report.evaluation_commentaire)}${report.note !== null ? ` — note : ${escapeHtml(report.note)}/20` : ''}</p>` : ''}
                  </li>`,
              )
              .join('') || '<li>Aucun dépôt pour le moment.</li>';

          return `<article class="report-card">
            <p class="report-type">${escapeHtml(stage.type)} · Fin prévue le ${escapeHtml(stage.date_fin)}</p>
            <h2>${escapeHtml(stage.sujet)}</h2>
            <p><strong>Entreprise :</strong> ${escapeHtml(stage.entreprise)} · <strong>Encadrant :</strong> ${escapeHtml(stage.encadrant)}</p>
            ${uploadForm}
            <details class="report-history" open>
              <summary>Historique de mes dépôts (${reports.length})</summary>
              <ol>${history}</ol>
            </details>
          </article>`;
        })
        .join('') || '<p>Aucun stage n’est associé à votre compte.</p>';

    res.send(
      layout(
        'Rapport final',
        req.session.user,
        `${showMessage(req.query.message)}
          <h1>Rapport final</h1>
          <p class="intro">Vous pouvez déposer votre rapport à partir de la date de fin de votre stage. Les versions envoyées et les retours restent visibles dans l’historique.</p>
          <section class="report-list" aria-label="Mes stages">${cards}</section>`,
      ),
    );
  } catch (error) {
    return next(error);
  }
});

router.post('/rapports/stages/:id/deposer', studentOnly, uploadFile, async (req, res, next) => {
  const stageId = Number(req.params.id);
  if (!Number.isSafeInteger(stageId)) {
    return res.status(404).send('Ce stage est introuvable.');
  }
  if (!req.file) {
    return res.redirect('/rapports?message=file-missing');
  }
  if (req.file.size < 5 || req.file.buffer.subarray(0, 5).toString('ascii') !== '%PDF-') {
    return res.redirect('/rapports?message=invalid-file');
  }

  let savedPath = null;
  try {
    const stage = database
      .prepare('SELECT id_stage, date_fin FROM STAGE WHERE id_stage = ? AND id_etudiant = ?')
      .get(stageId, req.session.user.id);
    if (!stage) {
      return res.status(404).send('Ce stage est introuvable pour votre compte.');
    }
    const today = new Date().toISOString().slice(0, 10);
    if (stage.date_fin > today) {
      return res.redirect('/rapports?message=date-not-reached');
    }

    const latest = database
      .prepare(
        'SELECT statut FROM DEPOT_RAPPORT_FINAL WHERE id_stage = ? ORDER BY id_depot_rapport DESC LIMIT 1',
      )
      .get(stageId);
    if (latest && latest.statut === 'DEPOSE') {
      return res.redirect('/rapports?message=report-pending');
    }
    if (latest && latest.statut === 'CORRIGE') {
      return res.redirect('/rapports?message=report-closed');
    }

    await fs.promises.mkdir(reportDirectory, { recursive: true });
    const fileName = `${crypto.randomUUID()}.pdf`;
    const absolutePath = path.join(reportDirectory, fileName);
    const relativePath = path.join('rapports', fileName);
    await fs.promises.writeFile(absolutePath, req.file.buffer, { flag: 'wx' });
    savedPath = absolutePath;

    database.transaction(() => {
      const currentStage = database
        .prepare('SELECT date_fin FROM STAGE WHERE id_stage = ? AND id_etudiant = ?')
        .get(stageId, req.session.user.id);
      if (!currentStage || currentStage.date_fin > new Date().toISOString().slice(0, 10)) {
        throw new Error('REPORT_NOT_YET_ALLOWED');
      }
      const currentLatest = database
        .prepare(
          'SELECT statut FROM DEPOT_RAPPORT_FINAL WHERE id_stage = ? ORDER BY id_depot_rapport DESC LIMIT 1',
        )
        .get(stageId);
      if (currentLatest && currentLatest.statut !== 'A_CORRIGER') {
        throw new Error(currentLatest.statut === 'DEPOSE' ? 'REPORT_PENDING' : 'REPORT_CLOSED');
      }
      database
        .prepare(
          `INSERT INTO DEPOT_RAPPORT_FINAL (id_stage, fichier_path, date_depot, statut)
           VALUES (?, ?, ?, 'DEPOSE')`,
        )
        .run(stageId, relativePath, new Date().toISOString());
    })();

    return res.redirect('/rapports?message=uploaded');
  } catch (error) {
    if (savedPath) {
      try {
        await fs.promises.unlink(savedPath);
      } catch (cleanupError) {
        if (cleanupError.code !== 'ENOENT') {
          return next(cleanupError);
        }
      }
    }
    if (error.message === 'REPORT_NOT_YET_ALLOWED') {
      return res.redirect('/rapports?message=date-not-reached');
    }
    if (error.message === 'REPORT_PENDING') {
      return res.redirect('/rapports?message=report-pending');
    }
    if (error.message === 'REPORT_CLOSED') {
      return res.redirect('/rapports?message=report-closed');
    }
    return next(error);
  }
});

router.get('/encadrant/rapports', advisorOnly, (req, res, next) => {
  try {
    const stages = database
      .prepare(
        `SELECT S.id_stage, S.type, S.sujet, S.date_fin,
                E.raison_sociale AS entreprise,
                Student.prenom || ' ' || Student.nom AS etudiant
         FROM STAGE S
         JOIN ENTREPRISE E ON E.id_entreprise = S.id_entreprise
         JOIN UTILISATEUR Student ON Student.id_utilisateur = S.id_etudiant
         WHERE S.id_encadrant = ?
         ORDER BY S.id_stage DESC`,
      )
      .all(req.session.user.id);
    const reportsForStage = database.prepare(
      `SELECT R.id_depot_rapport, R.fichier_path, R.date_depot, R.statut,
              R.commentaire_encadrant, V.commentaire AS evaluation_commentaire, V.note
       FROM DEPOT_RAPPORT_FINAL R
       LEFT JOIN EVALUATION_RAPPORT V ON V.id_depot_rapport = R.id_depot_rapport
       WHERE R.id_stage = ?
       ORDER BY R.id_depot_rapport DESC`,
    );
    const cards =
      stages
        .map((stage) => {
          const reports = reportsForStage.all(stage.id_stage);
          const latestId = reports[0]?.id_depot_rapport;
          const history =
            reports
              .map((report) => {
                const canReview = report.id_depot_rapport === latestId && report.statut === 'DEPOSE';
                const actions = canReview
                  ? `<div class="report-review-actions">
                      <form class="report-review-form" action="/encadrant/rapports/${report.id_depot_rapport}/corriger" method="post">
                        <label for="correction-${report.id_depot_rapport}">Commentaire expliquant les corrections demandées</label>
                        <textarea id="correction-${report.id_depot_rapport}" name="commentaire" rows="3" maxlength="2000" required></textarea>
                        <button class="button button-secondary" type="submit">Demander une correction</button>
                      </form>
                      <form class="report-review-form" action="/encadrant/rapports/${report.id_depot_rapport}/evaluer" method="post">
                        <label for="evaluation-${report.id_depot_rapport}">Commentaire d’évaluation</label>
                        <textarea id="evaluation-${report.id_depot_rapport}" name="commentaire" rows="3" maxlength="2000" required></textarea>
                        <label for="note-${report.id_depot_rapport}">Note sur 20 (facultative)</label>
                        <input id="note-${report.id_depot_rapport}" name="note" type="number" min="0" max="20" step="0.1">
                        <button class="button" type="submit">Enregistrer l’évaluation</button>
                      </form>
                    </div>`
                  : '';
                return `<li class="report-history-item">
                  <div><strong>${escapeHtml(statusLabel(report.statut))}</strong><span> · Déposé le ${escapeHtml(report.date_depot)}</span></div>
                  ${reportFileLink(report)}
                  ${report.commentaire_encadrant ? `<p><strong>Retour :</strong> ${escapeHtml(report.commentaire_encadrant)}</p>` : ''}
                  ${report.evaluation_commentaire ? `<p><strong>Évaluation :</strong> ${escapeHtml(report.evaluation_commentaire)}${report.note !== null ? ` — note : ${escapeHtml(report.note)}/20` : ''}</p>` : ''}
                  ${actions}
                </li>`;
              })
              .join('') || '<li>Aucun rapport déposé.</li>';

          return `<article class="report-card">
            <p class="report-type">${escapeHtml(stage.type)} · Fin prévue le ${escapeHtml(stage.date_fin)}</p>
            <h2>${escapeHtml(stage.etudiant)} — ${escapeHtml(stage.entreprise)}</h2>
            <p><strong>Sujet :</strong> ${escapeHtml(stage.sujet)}</p>
            <details class="report-history" open>
              <summary>Dépôts et retours (${reports.length})</summary>
              <ol>${history}</ol>
            </details>
          </article>`;
        })
        .join('') || '<p>Aucun stage ne vous est attribué.</p>';

    res.send(
      layout(
        'Rapports finaux à examiner',
        req.session.user,
        `${showMessage(req.query.message)}
          <h1>Rapports finaux</h1>
          <p class="intro">Examinez les rapports des stages qui vous sont attribués. Vous pouvez demander une correction ou enregistrer l’évaluation.</p>
          <section class="report-list" aria-label="Rapports à examiner">${cards}</section>`,
      ),
    );
  } catch (error) {
    return next(error);
  }
});

router.post('/encadrant/rapports/:id/corriger', advisorOnly, (req, res, next) => {
  const reportId = Number(req.params.id);
  const comment = typeof req.body.commentaire === 'string' ? req.body.commentaire.trim() : '';
  if (!Number.isSafeInteger(reportId) || !comment || comment.length > 2000) {
    return res.redirect('/encadrant/rapports?message=error');
  }

  try {
    const result = database
      .prepare(
        `UPDATE DEPOT_RAPPORT_FINAL
         SET statut = 'A_CORRIGER', commentaire_encadrant = ?
         WHERE id_depot_rapport = ? AND statut = 'DEPOSE'
           AND EXISTS (
             SELECT 1
             FROM STAGE S
             WHERE S.id_stage = DEPOT_RAPPORT_FINAL.id_stage
               AND S.id_encadrant = ?
               AND NOT EXISTS (
                 SELECT 1 FROM DEPOT_RAPPORT_FINAL Newer
                 WHERE Newer.id_stage = S.id_stage
                   AND Newer.id_depot_rapport > DEPOT_RAPPORT_FINAL.id_depot_rapport
               )
           )`,
      )
      .run(comment, reportId, req.session.user.id);
    if (result.changes !== 1) {
      return res.status(404).send('Ce dépôt n’est pas en attente pour votre compte.');
    }
    return res.redirect('/encadrant/rapports?message=correction');
  } catch (error) {
    return next(error);
  }
});

router.post('/encadrant/rapports/:id/evaluer', advisorOnly, (req, res, next) => {
  const reportId = Number(req.params.id);
  const comment = typeof req.body.commentaire === 'string' ? req.body.commentaire.trim() : '';
  const noteText = typeof req.body.note === 'string' ? req.body.note.trim() : '';
  const note = noteText ? Number(noteText) : null;
  if (
    !Number.isSafeInteger(reportId) ||
    !comment ||
    comment.length > 2000 ||
    (noteText && (!Number.isFinite(note) || note < 0 || note > 20))
  ) {
    return res.redirect('/encadrant/rapports?message=error');
  }

  try {
    const saveEvaluation = database.transaction(() => {
      const report = database
        .prepare(
          `SELECT R.id_depot_rapport
           FROM DEPOT_RAPPORT_FINAL R
           JOIN STAGE S ON S.id_stage = R.id_stage
           WHERE R.id_depot_rapport = ? AND R.statut = 'DEPOSE' AND S.id_encadrant = ?
             AND NOT EXISTS (
               SELECT 1 FROM DEPOT_RAPPORT_FINAL Newer
               WHERE Newer.id_stage = S.id_stage
                 AND Newer.id_depot_rapport > R.id_depot_rapport
             )`,
        )
        .get(reportId, req.session.user.id);
      if (!report) {
        throw new Error('REPORT_NOT_PENDING');
      }

      database
        .prepare(
          `INSERT INTO EVALUATION_RAPPORT (id_depot_rapport, id_encadrant, commentaire, note, date_evaluation)
           VALUES (?, ?, ?, ?, ?)`,
        )
        .run(reportId, req.session.user.id, comment, note, new Date().toISOString());
      database
        .prepare("UPDATE DEPOT_RAPPORT_FINAL SET statut = 'CORRIGE' WHERE id_depot_rapport = ?")
        .run(reportId);
    });
    saveEvaluation();
    return res.redirect('/encadrant/rapports?message=evaluated');
  } catch (error) {
    if (error.message === 'REPORT_NOT_PENDING') {
      return res.status(404).send('Ce dépôt n’est pas en attente pour votre compte.');
    }
    return next(error);
  }
});

router.get('/rapports/:id/fichier', requireRoles('ETUDIANT', 'ENCADRANT'), (req, res, next) => {
  const reportId = Number(req.params.id);
  if (!Number.isSafeInteger(reportId)) {
    return res.status(404).send('Ce fichier est introuvable.');
  }

  try {
    const report = database
      .prepare(
        `SELECT R.id_depot_rapport, R.fichier_path, S.id_etudiant, S.id_encadrant
         FROM DEPOT_RAPPORT_FINAL R
         JOIN STAGE S ON S.id_stage = R.id_stage
         WHERE R.id_depot_rapport = ?`,
      )
      .get(reportId);
    if (!report || !canAccessReport(req.session.user, report)) {
      return res.status(404).send('Ce fichier est introuvable pour votre compte.');
    }

    const absolutePath = resolveReportPath(report.fichier_path);
    if (!absolutePath || !fs.existsSync(absolutePath)) {
      return res.status(404).send('Le fichier PDF n’est plus disponible.');
    }
    res.set('Cache-Control', 'private, no-store');
    res.type('application/pdf');
    res.set('Content-Disposition', `inline; filename="rapport-${reportId}.pdf"`);
    return res.sendFile(absolutePath, (error) => {
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
