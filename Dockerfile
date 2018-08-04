FROM python:3-alpine

COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt

COPY tado-influxdb.py /app/tado-influxdb.py
RUN chmod +x /app/tado-influxdb.py

ENTRYPOINT /app/tado-influxdb.py
