FROM python:3.9-slim

WORKDIR /

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN rm requirements.txt

COPY src /src
COPY entrypoint.sh .

RUN python -m src.demo_data

RUN chmod a+x entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]