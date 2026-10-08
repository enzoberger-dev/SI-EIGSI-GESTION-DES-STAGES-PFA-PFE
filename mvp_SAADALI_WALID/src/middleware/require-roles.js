function requireRoles(...allowedRoles) {
  return (req, res, next) => {
    if (!req.session.user) {
      return res.redirect('/login');
    }

    if (!allowedRoles.includes(req.session.user.role)) {
      return res.status(403).send(
        '<!doctype html><html lang="fr"><meta charset="utf-8"><title>Accès refusé</title>' +
          '<body><main><h1>Accès refusé</h1><p>Votre compte ne permet pas d’ouvrir cette page.</p>' +
          '<a href="/espace">Retour à mon espace</a></main></body></html>',
      );
    }

    return next();
  };
}

module.exports = requireRoles;
