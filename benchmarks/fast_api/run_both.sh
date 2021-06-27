uvicorn benchmarks.fast_api.gateway_aiohttp_client:app --workers 10 --port 8000 &
uvicorn benchmarks.fast_api.fastapi_server:app --workers 10 --port 8011 &
wait