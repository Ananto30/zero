SHELL := /bin/bash

benchmark-zero-zmq:
		rm -rf ./zero/zero && \
		cp -r ../../zero ./zero/zero && \
		cd zero && ( \
		docker compose -f zmq__compose.yaml up -d --build gateway server redis; \
		sleep 2; \
		docker compose -f zmq__compose.yaml up wrk-hello; \
		docker compose -f zmq__compose.yaml up wrk-order; \
		docker compose -f zmq__compose.yaml up wrk-hello-async; \
		docker compose -f zmq__compose.yaml up wrk-order-async; \
		docker compose -f zmq__compose.yaml down; \
		)

benchmark-zero-zmq-down:
		cd zero && docker compose -f zmq__compose.yaml down


benchmark-zero-tcp:
		rm -rf ./zero/zero && \
		cp -r ../../zero ./zero/zero && \
		cd zero && ( \
		docker compose -f tcp__compose.yaml up -d --build gateway server redis; \
		sleep 2; \
		docker compose -f tcp__compose.yaml up wrk-hello; \
		docker compose -f tcp__compose.yaml up wrk-order; \
		docker compose -f tcp__compose.yaml up wrk-hello-async; \
		docker compose -f tcp__compose.yaml up wrk-order-async; \
		docker compose -f tcp__compose.yaml down; \
		)

benchmark-zero-tcp-down:
		cd zero && docker compose -f tcp__compose.yaml down