FROM debian:12-slim AS package-builder

RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes python3-venv gcc libpython3-dev && \
    python3 -m venv /venv && \
    /venv/bin/pip install --upgrade pip setuptools wheel

WORKDIR /build
COPY requirements.txt .
RUN /venv/bin/pip install --disable-pip-version-check -r requirements.txt --target /packages

FROM debian:12-slim as user-builder
RUN useradd -m -u 1000 appuser
WORKDIR /app
RUN mkdir -p /app/statics/uploads && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

FROM gcr.io/distroless/python3-debian12:nonroot as web-service

ENV XDG_CACHE_HOME=/tmp/.cache
ENV PYTHONUSERBASE=/tmp
ENV PYTHONPATH=/packages

COPY --from=user-builder /etc/passwd /etc/passwd
COPY --from=user-builder /etc/group /etc/group
COPY --from=user-builder --chown=1000:1000 /app /app

COPY --from=package-builder /packages /packages

COPY --chown=1000:1000 . /app

WORKDIR /app
USER 1000:1000

EXPOSE 10000
CMD ["standalone.py"]
