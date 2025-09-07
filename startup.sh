#!/bin/bash
cd /home/site/wwwroot
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 120 src.main:app