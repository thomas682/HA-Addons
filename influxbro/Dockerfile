FROM python:3.12-alpine
RUN apk add --no-cache bash curl jq
WORKDIR /app
RUN pip install --no-cache-dir flask influxdb-client influxdb PyYAML
COPY run.sh /run.sh
RUN chmod +x /run.sh
COPY app/ /app/
EXPOSE 8099
CMD ["/run.sh"]
