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

echo "======================================"
echo " CHECKING COUPONS MIGRATION STATE"
echo "======================================"

python manage.py showmigrations coupons

echo "======================================"
echo " CHECKING CUSTOMIZATION MIGRATION STATE"
echo "======================================"

python manage.py showmigrations customization

echo "======================================"
echo " CHECKING ACCOUNTS MIGRATION STATE"
echo "======================================"

python manage.py showmigrations accounts

echo "======================================"
echo " RUNNING DATABASE MIGRATIONS"
echo "======================================"

python manage.py migrate --verbosity 2

echo "======================================"
echo " BUILD COMPLETED SUCCESSFULLY"
echo "======================================"