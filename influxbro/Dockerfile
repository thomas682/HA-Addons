FROM python:3.12-alpine

# Install tools used by the add-on runtime.
RUN apk add --no-cache bash curl jq tzdata

# Influx CLI is required for native InfluxDB v2 backup/restore.
# Home Assistant build system provides BUILD_ARCH (amd64/aarch64/armv7/armhf/i386).
ARG INFLUX_CLI_VERSION=2.7.5
ARG BUILD_ARCH=amd64
RUN set -eux; \
    case "$BUILD_ARCH" in \
      amd64) arch="amd64" ;; \
      aarch64) arch="arm64" ;; \
      armv7) arch="armv7" ;; \
      armhf) arch="armv7" ;; \
      i386) arch="386" ;; \
      *) echo "Unsupported BUILD_ARCH=$BUILD_ARCH" >&2; exit 1 ;; \
    esac; \
    url="https://dl.influxdata.com/influxdb/releases/influxdb2-client-${INFLUX_CLI_VERSION}-linux-${arch}.tar.gz"; \
    curl -fsSL "$url" -o /tmp/influxcli.tgz; \
    tar -xzf /tmp/influxcli.tgz -C /tmp; \
    mv "/tmp/influxdb2-client-${INFLUX_CLI_VERSION}-linux-${arch}/influx" /usr/local/bin/influx; \
    chmod +x /usr/local/bin/influx; \
    rm -rf /tmp/influxcli.tgz "/tmp/influxdb2-client-${INFLUX_CLI_VERSION}-linux-${arch}"; \
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
