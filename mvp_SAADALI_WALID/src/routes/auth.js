const crypto = require('node:crypto');
const express = require('express');
const path = require('node:path');
const database = require('../db/database');
const { verifyPassword } = require('../auth/passwords');
const requireAuth = require('../middleware/require-auth');

const router = express.Router();
const activeRoles = ['ETUDIANT', 'ENCADRANT', 'SERVICE_STAGES', 'RESPONSABLE'];

router.get('/login', (req, res) => {
  if (req.session.user) {
    return res.redirect('/espace');
  }

  return res.sendFile(path.join(__dirname, '..', 'views', 'login.html'));
});

router.post('/login', async (req, res, next) => {
  const email = typeof req.body.email === 'string' ? req.body.email.trim().toLowerCase() : '';
  const password = typeof req.body.password === 'string' ? req.body.password : '';

  if (!email || !password || password.length > 256) {
    return res.redirect('/login?error=invalid');
  }

  try {
    const user = database
      .prepare(
        `SELECT id_utilisateur, prenom, nom, email, role, password_hash
         FROM UTILISATEUR
         WHERE email = ?`,
      )
      .get(email);

    let sessionUser = null;
    if (user && activeRoles.includes(user.role) && verifyPassword(password, user.password_hash)) {
      sessionUser = {
        id: user.id_utilisateur,
        firstName: user.prenom,
        lastName: user.nom,
        email: user.email,
        role: user.role,
      };
    } else if (!user) {
      const enterpriseAccount = database
        .prepare(
          `SELECT C.id_compte, C.id_entreprise, C.prenom, C.nom, C.email, C.password_hash
           FROM COMPTE_ENTREPRISE C
           WHERE C.email = ?`,
        )
        .get(email);

      if (enterpriseAccount && verifyPassword(password, enterpriseAccount.password_hash)) {
        sessionUser = {
          id: enterpriseAccount.id_compte,
          firstName: enterpriseAccount.prenom,
          lastName: enterpriseAccount.nom,
          email: enterpriseAccount.email,
          role: 'ENTREPRISE',
          companyId: enterpriseAccount.id_entreprise,
        };
      }
    }

    if (!sessionUser) {
      return res.redirect('/login?error=invalid');
    }

    await new Promise((resolve, reject) => {
      req.session.regenerate((error) => (error ? reject(error) : resolve()));
    });

    req.session.user = sessionUser;

    return res.redirect('/espace');
  } catch (error) {
    return next(error);
  }
});

router.post('/logout', requireAuth, (req, res, next) => {
  req.session.destroy((error) => {
    if (error) {
      return next(error);
    }

    res.clearCookie('connect.sid', { httpOnly: true, sameSite: 'lax' });
    return res.redirect('/login?logout=1');
  });
});

module.exports = router;
