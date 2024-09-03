FROM tensorflow/tensorflow:2.15.0 AS nctx-builder

RUN --mount=type=cache,sharing=locked,target=/var/cache/apt <<EOF
apt update
apt install -y --no-install-recommends \
	build-essential \
	cmake \
	libboost-graph-dev \
	libboost-python-dev
rm -rf /var/lib/apt/lists/*
ln -sf /usr/bin/python3.11 /usr/bin/python3
ln -sf /usr/bin/python3.11 /usr/bin/python
EOF
RUN --mount=type=cache,target=/root/.cache/pip pip install scikit-build

COPY ./py3nctx /build/py3nctx
WORKDIR /build/py3nctx

RUN --mount=type=cache,target=/root/.cache/pip rm -rf ./_skbuild \
	&& python setup.py bdist_wheel

RUN mkdir -p /build/boost-libs \
	&& cp /usr/lib/x86_64-linux-gnu/libboost*.so* /build/boost-libs

# use TF image here because provisioning KGAT requires tf2_update
FROM tensorflow/tensorflow:2.15.0 AS builder

WORKDIR /app
COPY ./Makefile /app/
COPY ./kgat /app/kgat
COPY ./kgat_pytorch /app/kgat_pytorch
COPY ./patches /app/patches

RUN make kgat kgat_pytorch

FROM tensorflow/tensorflow:2.15.0

RUN --mount=type=cache,sharing=locked,target=/var/cache/apt <<EOF
set -ex
apt-get update
apt-get install -y --no-install-recommends \
    busybox-static \
    gawk
rm -rf /var/lib/apt/lists/*
mkdir -p /var/spool/cron/crontabs
EOF

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.lock,target=/app/requirements.lock \
    pip install --no-cache -r /app/requirements.lock

RUN --mount=from=nctx-builder,source=/build/py3nctx/dist,target=/app/dist PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir /app/dist/*.whl
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache torch --index-url https://download.pytorch.org/whl/cpu
COPY --from=builder /app/kgat /app/kgat
COPY --from=builder /app/kgat_pytorch /app/kgat_pytorch
COPY --from=nctx-builder /build/boost-libs /app/boost-libs/

# Set the LD_LIBRARY_PATH to include the copied Boost libraries
ENV LD_LIBRARY_PATH=/app/boost-libs

# Optionally, you can add this directory permanently in ldconfig (optional)
RUN echo "/app/boost-libs" > /etc/ld.so.conf.d/boost.conf && ldconfig

RUN mkdir -p /app/kgat_pytorch/datasets/pretrain \
    && mkdir -p /app/kgat_pytorch/trained_model/KGAT \
    && ln -s /app/shared/pretrain/wisski /app/kgat/Model/pretrain/ \
    && ln -s /app/shared/pretrain/wisski /app/kgat_pytorch/datasets/pretrain/ \
    && ln -s /app/shared/datasets/wisski /app/kgat/Data/ \
    && ln -s /app/shared/model/wisski/ /app/kgat_pytorch/trained_model/KGAT/

COPY <<EOF /var/spool/cron/crontabs/root
##   CRONTAB HINTS AND TIPS
##
##
##   Entry              Description     Equivalent To
##   @yearly (or @annually)     Run once a year at midnight in the morning of January 1         0 0 1 1 *
##   @monthly   Run once a month at midnight in the morning of the first of the month   0 0 1 * *
##   @weekly    Run once a week at midnight in the morning of Sunday    0 0 * * 0
##   @daily             Run once a day at midnight      0 0 * * *
##   @hourly    Run once an hour at the beginning of the hour   0 * * * *
##   @reboot    Run at startup  @reboot
##
##   *    *    *    *    *  command to be executed
##   ┬    ┬    ┬    ┬    ┬
##   │    │    │    │    │
##   │    │    │    │    │
##   │    │    │    │    └───── day of week (0 - 7) (0 or 7 are Sunday, or use names)
##   │    │    │    └────────── month (1 - 12)
##   │    │    └─────────────── day of month (1 - 31)
##   │    └──────────────────── hour (0 - 23)
##   └───────────────────────── min (0 - 59)
##
##
##
##   The following example will run each 10 minutes
##   */10 * * * * /usr/bin/somedirectory/somecommand

##   Disable E-mail notifications
MAILTO=""

##   Set where to look for executable files
PATH=/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/sbin:/usr/local/bin:$PATH

## Ok, we are ready to go. Put your schedules below :-)
##
## Run training routines daily at 3:01 am
1 3 * * * /app/run.sh
EOF

COPY ./.env /app/.env
COPY ./cron.sh /app/
COPY ./run.sh /app

RUN chmod +x /app/run.sh
RUN chmod +x /app/cron.sh

ENTRYPOINT ["/app/cron.sh"]
