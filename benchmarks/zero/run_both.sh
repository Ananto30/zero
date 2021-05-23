gunicorn benchmarks.zero.gateway:gateway_app --bind localhost:8000 --worker-class aiohttp.GunicornWebWorker --workers 10 &
python -m benchmarks.zero.hello_world &
wait