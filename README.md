# tado-influxdb
A little helper script to get measurements from Tado to InfluxDB.

## Config
Before running the script you must create a config.py (see config.py.example
for an example). The script will not work properly otherwise.

## Warning
Please be aware that this script is work in progress, does no error handling
and will probably crash ;-) I will fix this soon...ish!

## Running on Docker / Kubernetes
This repo includes a Dockerfile (builds to cbeneke/tado-influxdb:latest) and a
Kubernetes Deployment yaml. If you want to run on Kubernetes, change the
CHANGEME options in the Deployment and configure your influx-service in the
tado-influx-config configmap.
