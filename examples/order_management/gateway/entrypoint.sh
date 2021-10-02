#!/bin/sh

gunicorn src.main:app --bind 0.0.0.0:8000 --worker-class aiohttp.worker.GunicornWebWorker --workers 8 --log-level  info