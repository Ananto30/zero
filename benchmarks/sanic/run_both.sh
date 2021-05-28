sanic benchmarks.sanic.gateway.app --workers=10 --port 8000 &
sanic benchmarks.sanic.sanic_server.app --workers=10 --port 8011 &
wait