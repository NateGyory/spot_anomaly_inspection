SHELL := /bin/bash

build_local:
	docker-compose build

export:
	docker save spot_estop_service_spot_anomaly_deploy:latest > spot_anomaly_deploy.tar

exec:
	docker exec -it spot_anomaly_deploy /bin/bash

waypoint_deploy:
	curl --location --request POST 'localhost:5000/spot_deploy' \
		 --header 'Content-Type: application/json' \
		 --data-raw '{ "waypoint_id": 123 }'
