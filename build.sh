#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate

python -c "import os; print('DATABASE_URL=', os.getenv('DATABASE_URL'))"