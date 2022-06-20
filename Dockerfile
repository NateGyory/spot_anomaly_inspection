FROM python:3.7

RUN apt update -y && \
    apt install -y vim

COPY docker-requirements.txt .
RUN python3 -m pip install -r docker-requirements.txt

COPY . /app
WORKDIR /app/scripts
