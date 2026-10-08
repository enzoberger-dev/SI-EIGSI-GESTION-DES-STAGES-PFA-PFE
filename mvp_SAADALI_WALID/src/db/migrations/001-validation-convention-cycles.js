function migrateValidationCycles(database) {
  const conventionColumns = database.pragma('table_info(CONVENTION)');
  if (!conventionColumns.some((column) => column.name === 'cycle')) {
    database.exec(
      'ALTER TABLE CONVENTION ADD COLUMN cycle INTEGER NOT NULL DEFAULT 1 CHECK (cycle > 0)',
    );
  }

  const columns = database.pragma('table_info(VALIDATION_CONVENTION)');
  if (columns.some((column) => column.name === 'cycle')) {
    return;
  }

  database.transaction(() => {
    database.exec(`
      CREATE TABLE VALIDATION_CONVENTION_NEW (
        id_validation INTEGER PRIMARY KEY,
        id_convention INTEGER NOT NULL REFERENCES CONVENTION(id_convention),
        cycle INTEGER NOT NULL DEFAULT 1 CHECK (cycle > 0),
        id_validateur INTEGER NOT NULL REFERENCES UTILISATEUR(id_utilisateur),
        niveau INTEGER NOT NULL CHECK (niveau BETWEEN 1 AND 3),
        decision TEXT NOT NULL CHECK (decision IN ('VALIDE', 'REFUSE')),
        commentaire TEXT,
        date_decision TEXT NOT NULL,
        UNIQUE (id_convention, cycle, niveau),
        CHECK (decision != 'REFUSE' OR length(trim(commentaire)) > 0)
      );

      INSERT INTO VALIDATION_CONVENTION_NEW
        (id_validation, id_convention, cycle, id_validateur, niveau, decision, commentaire, date_decision)
      SELECT id_validation, id_convention, 1, id_validateur, niveau, decision, commentaire, date_decision
      FROM VALIDATION_CONVENTION;

      DROP TABLE VALIDATION_CONVENTION;
      ALTER TABLE VALIDATION_CONVENTION_NEW RENAME TO VALIDATION_CONVENTION;
    `);
  })();
}

module.exports = migrateValidationCycles;
