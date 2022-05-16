FROM python:3.7

COPY docker-requirements.txt .
RUN python3 -m pip install -r docker-requirements.txt

COPY . /app
WORKDIR /app

#ARG flask_app=
#ARG flask_env=
#ARG spot_user=
#ARG spot_password=
#ARG timeout=
#ARG hostname=
#
#ENV FLASK_APP=${flask_app}
#ENV FLASK_ENV=${flask_env}
#ENV SPOT_USER=${spot_user}
#ENV SPOT_PASSWORD=${spot_password}
#ENV TIMEOUT=${timeout}
#ENV HOSTNAME=${hostname}

ENTRYPOINT ["python3", "/app/scripts/server.py"]
