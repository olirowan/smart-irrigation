#!/bin/sh
gunicorn --chdir app smart-irrigation:app --timeout 1000 --workers 2 --threads 2 -b 127.0.0.1:5000