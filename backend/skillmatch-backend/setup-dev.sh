#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# SkillMatch backend — one-shot dev setup for Git Bash on Windows.
#
# Builds a clean Python 3.12 virtualenv, installs the minimal requirements,
# creates a SQLite .env, and runs migrations. Bypasses `activate` entirely
# (it kept resolving to Python 3.14) by calling the venv's python directly.
#
# Usage (from this folder, in a FRESH Git Bash window):
#     bash setup-dev.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e
cd "$(dirname "$0")"

# 1. Locate the real Python 3.12 interpreter --------------------------------
PY312="/c/Users/papisansar/AppData/Local/Python/pythoncore-3.12-64/python.exe"
if [ ! -f "$PY312" ]; then
    echo "3.12 not at the expected path — asking the launcher..."
    PY312="$(py -3.12 -c 'import sys; print(sys.executable)')"
fi
echo ">> Base interpreter: $PY312"
"$PY312" --version

# 2. Recreate the virtualenv from that interpreter --------------------------
echo ">> Recreating .venv ..."
rm -rf .venv
"$PY312" -m venv .venv
VENV_PY=".venv/Scripts/python.exe"

echo ">> venv interpreter (must be 3.12.x):"
"$VENV_PY" --version

# 3. Install dependencies ---------------------------------------------------
echo ">> Upgrading pip + installing requirements-min.txt ..."
"$VENV_PY" -m pip install --upgrade pip
"$VENV_PY" -m pip install -r requirements-min.txt

# 4. Environment file (SQLite for a no-Postgres quick run) ------------------
if [ ! -f .env ]; then
    cp .env.example .env
    echo ">> Created .env from .env.example"
fi
if grep -q '^USE_SQLITE=' .env; then
    sed -i 's/^USE_SQLITE=.*/USE_SQLITE=1/' .env
else
    echo 'USE_SQLITE=1' >> .env
fi
echo ">> .env set to USE_SQLITE=1"

# 5. Database ----------------------------------------------------------------
echo ">> Applying migrations ..."
"$VENV_PY" manage.py migrate

echo ""
echo "============================================================"
echo " Setup complete."
echo " Start the server with:"
echo "     .venv/Scripts/python.exe manage.py runserver"
echo " Then open:  http://127.0.0.1:8000/api/docs"
echo "============================================================"
