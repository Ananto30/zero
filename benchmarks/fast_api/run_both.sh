uvicorn benchmarks.fast_api.gateway:app --workers 10 --port 8000 &
uvicorn benchmarks.fast_api.redis_reader:app --workers 10 --port 8011 &
wait