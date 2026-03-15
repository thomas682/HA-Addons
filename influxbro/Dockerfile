FROM python:3.12-alpine

# Install tools used by the add-on runtime.
RUN apk add --no-cache bash curl jq tzdata

# Influx CLI is required for native InfluxDB v2 backup/restore.
# Home Assistant build system provides BUILD_ARCH (amd64/aarch64/armv7/armhf/i386).
ARG INFLUX_CLI_VERSION=2.7.5
ARG BUILD_ARCH=amd64
ENV INFLUXBRO_BUILD_ARCH=$BUILD_ARCH
RUN set -eux; \
    case "$BUILD_ARCH" in \
      amd64) arch="amd64" ;; \
      aarch64) arch="arm64" ;; \
      *) echo "Influx CLI not available for BUILD_ARCH=$BUILD_ARCH; skipping install"; exit 0 ;; \
    esac; \
    url="https://dl.influxdata.com/influxdb/releases/influxdb2-client-${INFLUX_CLI_VERSION}-linux-${arch}.tar.gz"; \
    curl -fsSL "$url" -o /tmp/influxcli.tgz; \
    tar -xzf /tmp/influxcli.tgz -C /tmp; \
    mv /tmp/influx /usr/local/bin/influx; \
    chmod +x /usr/local/bin/influx; \
    rm -f /tmp/influxcli.tgz; \
    influx version
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
