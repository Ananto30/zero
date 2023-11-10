SHELL := /bin/bash

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

benchmark-zero-sync:
		rm -rf ./zero/zero && \
		cp -r ../../zero ./zero/zero && \
		cd zero && ( \
		python zero_server.py & \
		sleep 2; \
		python zero_sync_client.py; \
		kill -9 $(shell ps aux | grep '[p]ython zero_server.py' | awk '{print $$2}'); \
		)