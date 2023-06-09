SHELL := /bin/bash

server:
	@rm -rf ./zero
	@cp -r ../../zero ./zero
	@mprof run -M -T 1 -o mprofile_server.dat python -m src.server

client:
	@rm -rf ./zero
	@cp -r ../../zero ./zero
	@mprof run -M -T 1 -o mprofile_client.dat python -m src.client

async-client:
	@rm -rf ./zero
	@cp -r ../../zero ./zero
	@mprof run -M -T 1 -o mprofile_async_client.dat python -m src.async_client

kill:
	@lsof -i :5555 | awk '{print $$2}' | tail -n 1 | xargs kill -9

plot-server:
	@mprof plot mprofile_server.dat

plot-client:
	@mprof plot mprofile_client.dat

plot-async-client:
	@mprof plot mprofile_async_client.dat