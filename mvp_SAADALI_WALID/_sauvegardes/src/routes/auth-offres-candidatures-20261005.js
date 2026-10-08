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

    const passwordIsValid = verifyPassword(password, user && user.password_hash);
    if (!user || !activeRoles.includes(user.role) || !passwordIsValid) {
      return res.redirect('/login?error=invalid');
    }

    await new Promise((resolve, reject) => {
      req.session.regenerate((error) => (error ? reject(error) : resolve()));
    });

    req.session.user = {
      id: user.id_utilisateur,
      firstName: user.prenom,
      lastName: user.nom,
      email: user.email,
      role: user.role,
    };

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
