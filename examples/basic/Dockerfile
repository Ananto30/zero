FROM python:3.9-slim

WORKDIR /

COPY ./examples/basic/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

COPY ./zero /zero
COPY ./examples/basic/server.py /src/server.py

COPY ./examples/basic/entrypoint.sh /entrypoint.sh
RUN chmod a+x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
