FROM python:3.11-slim
WORKDIR /app
COPY app /app
RUN pip install flask influxdb-client influxdb pyyaml
CMD ["python", "app.py"]