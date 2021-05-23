sanic benchmarks.sanic.gateway.app --workers=10 --port 8000 &
sanic benchmarks.sanic.redis_reader.app --workers=10 --port 8011 &
wait