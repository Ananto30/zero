SHELL := /bin/bash

benchmark-zero:
		rm -rf ./zero/zero && \
		cp -r ../../zero ./zero/zero && \
		cd zero && ( \
		docker-compose up -d --build gateway server redis; \
		sleep 2; \
		docker-compose up wrk-hello; \
		# docker-compose up wrk-order; \
		docker-compose up wrk-hello-async; \
		# docker-compose up wrk-order-async; \
		docker-compose down; \
		)