SHELL := /bin/bash

build_local:
	docker-compose build

export:
	docker save anomaly_deploy_service_docker:latest > spot_anomaly_deploy.tar

exec:
	docker exec -it spot_anomaly_deploy /bin/bash

waypoint_deploy_prod:
	curl --location --request POST '192.168.50.5:5000/spot_deploy' \
		 --header 'Content-Type: application/json' \
		 --data-raw '{ "waypoint_id": "fabled-ant-9U+9jNqo.Z+yNUDUEj2R.A==" }'

waypoint_deploy_local:
	curl --location --request POST 'localhost:5000/spot_deploy' \
		 --header 'Content-Type: application/json' \
		 --data-raw '{ "waypoint_id": "fabled-ant-9U+9jNqo.Z+yNUDUEj2R.A==" }'
