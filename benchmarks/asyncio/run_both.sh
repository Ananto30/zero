gunicorn benchmarks.asyncio.gateway:gateway_app --bind localhost:8000 --worker-class aiohttp.GunicornWebWorker --workers 10 &
gunicorn benchmarks.asyncio.redis_reader:redis_app --bind localhost:8011 --worker-class aiohttp.GunicornWebWorker --workers 10 &
wait