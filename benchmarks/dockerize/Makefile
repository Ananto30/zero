SHELL := /bin/bash
benchmark-aiohttp:
		cd aiohttp && ( \
		docker-compose up -d gateway server redis; \
		sleep 2; \
		docker-compose up wrk-hello; \
		docker-compose up wrk-order; \
		docker-compose down; \
		)

benchmark-aiozmq:
		cd aiozmq && ( \
		docker-compose up -d gateway server redis; \
		sleep 2; \
		docker-compose up wrk-hello; \
		docker-compose up wrk-order; \
		docker-compose down; \
		)

benchmark-fastapi:
		cd fast_api && ( \
		docker-compose up -d gateway server redis; \
		sleep 2; \
		docker-compose up wrk-hello; \
		docker-compose up wrk-order; \
		docker-compose down; \
		)

benchmark-sanic:
		cd sanic && ( \
		docker-compose up -d gateway server redis; \
		sleep 2; \
		docker-compose up wrk-hello; \
		docker-compose up wrk-order; \
		docker-compose down; \
		)

benchmark-zero:
		rm -rf ./zero/zero && \
		cp -r ../../zero ./zero/zero && \
		cd zero && ( \
		docker-compose up -d --build gateway server redis; \
		sleep 2; \
		docker-compose up wrk-hello; \
		docker-compose up wrk-order; \
		docker-compose up wrk-hello-async; \
		docker-compose up wrk-order-async; \
		docker-compose down; \
		)