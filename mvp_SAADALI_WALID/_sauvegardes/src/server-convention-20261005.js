const express = require('express');
const path = require('node:path');
const session = require('express-session');
const homeRouter = require('./routes/home');
const demoRouter = require('./routes/demo');
const authRouter = require('./routes/auth');
const workspacesRouter = require('./routes/workspaces');
const stagesRouter = require('./routes/stages');
const offersRouter = require('./routes/offers');

const app = express();
const port = process.env.PORT || 3000;

app.use(express.urlencoded({ extended: false }));
app.use(
  session({
    secret: process.env.SESSION_SECRET || 'local-development-secret-change-before-deployment',
    resave: false,
    saveUninitialized: false,
    cookie: {
      httpOnly: true,
      sameSite: 'lax',
      secure: false,
    },
  }),
);
app.use(express.static(path.join(__dirname, '..', 'public')));
app.use(authRouter);
app.use(workspacesRouter);
app.use(stagesRouter);
app.use(offersRouter);
app.use(homeRouter);
app.use(demoRouter);

if (require.main === module) {
  app.listen(port, '127.0.0.1', () => {
    console.log(`Application prête : http://localhost:${port}`);
  });
}

module.exports = app;
