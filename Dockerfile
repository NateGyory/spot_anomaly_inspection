FROM python:3.7

COPY docker-requirements.txt .
RUN python3 -m pip install -r docker-requirements.txt

COPY . /app
WORKDIR /app

ENTRYPOINT ["python3", "/app/scripts/estop.py"]

