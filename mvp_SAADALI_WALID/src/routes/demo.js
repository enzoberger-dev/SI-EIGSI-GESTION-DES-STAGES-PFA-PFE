const express = require('express');
const database = require('../db/database');
const requireRoles = require('../middleware/require-roles');

const router = express.Router();

router.get('/api/demo-data', requireRoles('SERVICE_STAGES', 'RESPONSABLE'), (_req, res) => {
  const stages = database
    .prepare(
      `SELECT STAGE.id_stage, STAGE.sujet, STAGE.type, STAGE.statut_conformite,
              UTILISATEUR.prenom || ' ' || UTILISATEUR.nom AS etudiant,
              ENTREPRISE.raison_sociale AS entreprise,
              OFFRE.titre AS offre
       FROM STAGE
       JOIN UTILISATEUR ON UTILISATEUR.id_utilisateur = STAGE.id_etudiant
       JOIN ENTREPRISE ON ENTREPRISE.id_entreprise = STAGE.id_entreprise
       LEFT JOIN OFFRE ON OFFRE.id_offre = STAGE.id_offre
       ORDER BY STAGE.id_stage`,
    )
    .all();

  res.json({ donneesFictives: true, stages });
});

module.exports = router;
