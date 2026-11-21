# Build from the selected source distribution; no local plans or original attempts.
FROM python@sha256:83f339c1be6340ae1096010fdccf6552ac932d8f410d45d206014916bdf37e48

ENV PYTHONDONTWRITEBYTECODE=1 UV_PYTHON_DOWNLOADS=never
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 openssh-server rsync curl patch ca-certificates && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/el/tools && /opt/el/tools/bin/pip install --no-cache-dir uv==0.11.28
COPY pyproject.toml README.md /opt/el/source/
COPY configs/accelerated-compute/worker /opt/el/source/configs/accelerated-compute/worker/
RUN UV_PROJECT_ENVIRONMENT=/opt/el/worker /opt/el/tools/bin/uv sync --no-cache --locked --no-dev --no-install-package empirical-lawhood --project /opt/el/source/configs/accelerated-compute/worker
# Resolve CUDA wheel libraries without changing Python packages or relying on
# an unrecorded shell loader setting. The host supplies its actual CUDA driver.
RUN find /opt/el/worker/lib/python3.11/site-packages/nvidia -type d -name lib > /etc/ld.so.conf.d/el-cuda.conf && echo /opt/el/worker/lib/python3.11/site-packages/cutensor/lib >> /etc/ld.so.conf.d/el-cuda.conf && ldconfig
WORKDIR /opt/el
