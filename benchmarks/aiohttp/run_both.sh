gunicorn benchmarks.aiohttp.gateway:gateway_app --bind localhost:8000 --worker-class aiohttp.GunicornWebWorker --workers 10 &
gunicorn benchmarks.aiohttp.asyncio_server:aiohttp_app --bind localhost:8011 --worker-class aiohttp.GunicornWebWorker --workers 10 &
wait