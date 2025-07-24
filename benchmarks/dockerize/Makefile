SHELL := /bin/bash
benchmark-aiohttp:
			   cd aiohttp && ( \
			   docker-compose up -d --build gateway server redis; \
			   sleep 2; \
			   docker-compose up wrk-hello >> ../history/benchmark-aiohttp__$(shell date +%Y-%m-%d).log 2>&1; \
			   docker-compose up wrk-order >> ../history/benchmark-aiohttp__$(shell date +%Y-%m-%d).log 2>&1; \
			   docker-compose down; \
			   )

benchmark-blacksheep:
			   cd blacksheep && ( \
			   docker-compose up -d --build gateway server redis; \
			   sleep 2; \
			   docker-compose up wrk-hello >> ../history/benchmark-blacksheep__$(shell date +%Y-%m-%d).log 2>&1; \
			   docker-compose up wrk-order >> ../history/benchmark-blacksheep__$(shell date +%Y-%m-%d).log 2>&1; \
			   docker-compose down; \
			   )

benchmark-aiozmq:
			   cd aiozmq && ( \
			   docker-compose up -d --build gateway server redis; \
			   sleep 2; \
			   docker-compose up wrk-hello >> ../history/benchmark-aiozmq__$(shell date +%Y-%m-%d).log 2>&1; \
			   docker-compose up wrk-order >> ../history/benchmark-aiozmq__$(shell date +%Y-%m-%d).log 2>&1; \
			   docker-compose down; \
			   )

benchmark-fastapi:
			   cd fast_api && ( \
			   docker-compose up -d --build gateway server redis; \
			   sleep 2; \
			   docker-compose up wrk-hello >> ../history/benchmark-fastapi__$(shell date +%Y-%m-%d).log 2>&1; \
			   docker-compose up wrk-order >> ../history/benchmark-fastapi__$(shell date +%Y-%m-%d).log 2>&1; \
			   docker-compose down; \
			   )

benchmark-sanic:
			   cd sanic && ( \
			   docker-compose up -d --build gateway server redis; \
			   sleep 2; \
			   docker-compose up wrk-hello >> ../history/benchmark-sanic__$(shell date +%Y-%m-%d).log 2>&1; \
			   docker-compose up wrk-order >> ../history/benchmark-sanic__$(shell date +%Y-%m-%d).log 2>&1; \
			   docker-compose down; \
			   )

benchmark-zero:
			   cd zero && ( \
			   docker-compose up -d --build gateway server redis; \
			   sleep 2; \
			   docker-compose up wrk-hello >> ../history/benchmark-zero__$(shell date +%Y-%m-%d).log 2>&1; \
			   docker-compose up wrk-order >> ../history/benchmark-zero__$(shell date +%Y-%m-%d).log 2>&1; \
			   docker-compose up wrk-hello-async >> ../history/benchmark-zero__$(shell date +%Y-%m-%d).log 2>&1; \
			   docker-compose up wrk-order-async >> ../history/benchmark-zero__$(shell date +%Y-%m-%d).log 2>&1; \
			   docker-compose down; \
			   )

benchmark-all:
			   $(MAKE) benchmark-aiohttp
			   $(MAKE) benchmark-blacksheep
			   $(MAKE) benchmark-aiozmq
			   $(MAKE) benchmark-fastapi
			   $(MAKE) benchmark-sanic
			   $(MAKE) benchmark-zero