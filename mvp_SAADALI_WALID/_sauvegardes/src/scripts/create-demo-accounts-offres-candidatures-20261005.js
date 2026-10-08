const crypto = require('node:crypto');
const database = require('../db/database');
const { hashPassword } = require('../auth/passwords');

const demoAccounts = [
  { email: 'yasmine.benali@example.test', role: 'ETUDIANT' },
  { email: 'sara.bennani@example.test', role: 'ENCADRANT' },
  { email: 'nadia.alaoui@example.test', role: 'SERVICE_STAGES' },
  { email: 'karim.idrissi@example.test', role: 'RESPONSABLE' },
];

const updatePassword = database.prepare(
  `UPDATE UTILISATEUR
   SET password_hash = ?
   WHERE email = ? AND role = ? AND password_hash IS NULL`,
);
const findAccount = database.prepare(
  'SELECT id_utilisateur, password_hash FROM UTILISATEUR WHERE email = ? AND role = ?',
);

const results = database.transaction(() =>
  demoAccounts.map((account) => {
    const current = findAccount.get(account.email, account.role);
    if (!current) {
      throw new Error(`Compte de démonstration introuvable : ${account.email}`);
    }

    if (current.password_hash) {
      return { ...account, password: null, initialized: false };
    }

    const password = crypto.randomBytes(18).toString('base64url');
    updatePassword.run(hashPassword(password), account.email, account.role);

    return { ...account, password, initialized: true };
  }),
)();

for (const account of results) {
  if (account.initialized) {
    console.log(`${account.role}: ${account.email} | mot de passe temporaire: ${account.password}`);
  } else {
    console.log(`${account.role}: ${account.email} | déjà initialisé; mot de passe non réaffiché`);
  }
}

console.log('Changez les mots de passe temporaires avant tout usage réel.');
database.close();
