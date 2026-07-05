#!/usr/bin/env bash
# Запускать на PythonAnywhere (Bash-консоль этого — отдельного — аккаунта),
# не локально. Тот же паттерн, что и в основном проекте (MS/deploy.sh):
# git pull + touch WSGI-файла триггерит перезагрузку веб-аппа.
#
# Использование:
#   bash deploy.sh
set -euo pipefail

WSGI_FILE="/var/www/no1an_pythonanywhere_com_wsgi.py"

cd "$(dirname "$0")"

echo "== git pull =="
git pull origin main

echo "== reload web app (touch WSGI file) =="
touch "$WSGI_FILE"

echo "Готово."
