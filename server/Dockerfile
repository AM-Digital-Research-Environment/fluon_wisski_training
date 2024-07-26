FROM python:3.10-slim

EXPOSE 5000

RUN addgroup --system python \
    && adduser --system --no-create-home --ingroup python --uid 1001 python \
    && mkdir /app \
    && chown --recursive python:python /app

WORKDIR /app

# RUN apk add --no-cache \
#      build-base \
#      linux-headers \
#      uwsgi-python3


# RUN python -m venv /app/venv
# # Make sure we use the virtualenv:
# ENV PATH="/app/venv/bin:$PATH"

# COPY requirements.lock ./
# RUN PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir -r requirements.lock
RUN --mount=source=dist,target=/dist PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir /dist/*.whl

COPY ./server /app/server
USER 1001

ENTRYPOINT ["uwsgi"]

CMD ["--http-socket", "0.0.0.0:5000", "-w", "server.wsgi:app", "--master", "--processes", "4", "--threads", "2"]
