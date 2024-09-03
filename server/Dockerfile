FROM python:3.12.5-alpine@sha256:c2f41e6a5a67bc39b95be3988dd19fbd05d1b82375c46d9826c592cca014d4de

EXPOSE 5000

RUN addgroup --system python \
    && adduser --system --no-create-home --ingroup python --uid 1001 python \
    && mkdir /app \
    && chown --recursive python:python /app

RUN --mount=type=cache,target=/var/cache/apk \
    apk update \
    && apk add \
     build-base \
     linux-headers \
     uwsgi-python3


WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY pyproject.toml .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r pyproject.toml

COPY ./server /app/server
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -e .

USER 1001

ENV PATH="/app/venv/bin:$PATH"
ENTRYPOINT ["uwsgi"]

CMD ["--http-socket", "0.0.0.0:5000", "-w", "server.wsgi:app", "--master", "--processes", "4", "--threads", "2"]
