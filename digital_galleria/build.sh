#!/usr/bin/env bash

set -o errexit

echo "======================================"
echo " DIGITAL GALLERIA - RENDER BUILD"
echo "======================================"

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Checking Django..."
python manage.py check

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running database migrations..."
python manage.py migrate

echo "======================================"
echo " BUILD COMPLETED SUCCESSFULLY"
echo "======================================"