@echo off
setlocal EnableExtensions
chcp 65001 >nul
set PYTHONUTF8=1
title Demonstration - gestion des stages EIGSI
cd /d "%~dp0"

rem ======================================================================================
rem  Lancement de la demonstration (double-clic suffit).
rem  - 1er lancement : 2 a 5 minutes (installation, internet necessaire). Ensuite : quelques secondes.
rem  - Utilise sa PROPRE base (demo.sqlite3) et son propre dossier de fichiers (demo_uploads) :
rem    aucune vraie donnee n'est touchee. Pour repartir de zero : supprimer demo.sqlite3.
rem ======================================================================================

echo.
echo  === Plateforme de gestion des stages - EIGSI Casablanca : DEMONSTRATION ===
echo.

rem --- 1. Trouver Python (3.10 ou plus recent)
set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>&1 && set "PY=py -3"
if not defined PY (
  python -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>&1 && set "PY=python"
)
if not defined PY (
  echo  [ERREUR] Python 3.10 ou plus recent est introuvable sur cet ordinateur.
  echo  Installez-le depuis https://www.python.org/downloads/ en cochant "Add python.exe to PATH",
  echo  puis relancez ce fichier.
  goto :fin
)

rem --- 2. Environnement et dependances (une seule fois)
if not exist ".venv\Scripts\python.exe" (
  echo  Creation de l'environnement Python ^(une seule fois^)...
  %PY% -m venv .venv || goto :erreur
)
if not exist ".venv\.dependances_ok" (
  echo  Installation des dependances ^(une seule fois, internet necessaire^)...
  ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt || goto :erreur
  echo ok> ".venv\.dependances_ok"
)

rem --- 3. Reglages propres a la demo
set "DJANGO_DEBUG=1"
set "DATABASE_URL=sqlite:///demo.sqlite3"
set "DJANGO_MEDIA_ROOT=%CD%\demo_uploads"

rem --- 4. Base de demonstration (creee au premier lancement)
if not exist "demo.sqlite3" (
  echo  Preparation de la base de demonstration...
  ".venv\Scripts\python.exe" manage.py migrate --verbosity 0 || goto :erreur
  ".venv\Scripts\python.exe" manage.py preparer_demo || goto :erreur
  echo.
)

if defined DEMO_SANS_SERVEUR (
  echo  [Test] Preparation terminee, serveur non lance.
  goto :fin
)

rem --- 5. Serveur et navigateur
echo.
echo  ===^> La demonstration s'ouvre dans votre navigateur : http://localhost:8000/
echo  ===^> Pour l'arreter : fermez cette fenetre.
echo.
start "" /b cmd /c "timeout /t 4 /nobreak >nul & start "" http://localhost:8000/"
".venv\Scripts\python.exe" manage.py runserver 8000 --noreload
goto :fin

:erreur
echo.
echo  [ERREUR] Une etape a echoue. Lisez le message ci-dessus, ou envoyez-le a Walid.

:fin
echo.
if not defined DEMO_SANS_SERVEUR pause
