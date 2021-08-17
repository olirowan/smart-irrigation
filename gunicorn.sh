#!/bin/sh
gunicorn --chdir app smart-irrigation:app -w 4 --threads 2 -b 0.0.0.0:5000