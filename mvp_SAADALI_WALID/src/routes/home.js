const express = require('express');

const router = express.Router();

router.get('/', (_req, res) => {
  if (_req.session.user) {
    return res.redirect('/espace');
  }

  return res.redirect('/login');
});

module.exports = router;
