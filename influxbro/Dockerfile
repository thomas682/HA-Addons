FROM python:3.12-alpine
RUN apk add --no-cache bash curl jq tzdata
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY config.yaml /app/addon_config.yaml
COPY CHANGELOG.md /app/CHANGELOG.md
COPY MANUAL.md /app/MANUAL.md
COPY run.sh /run.sh
RUN chmod +x /run.sh
COPY app/ /app/
EXPOSE 8099
CMD ["/run.sh"]
