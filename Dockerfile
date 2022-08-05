# Distroless Container Images
# => https://github.com/GoogleContainerTools/distroless
#

# Build a virtualenv using the appropriate Debian release:
#   * Install python3-venv for the built-in Python3 venv module (not installed by default)
#   * Install gcc libpython3-dev to compile C Python modules
#   * In the virtualenv: Update pip setuputils and wheel to support building new packages
#
FROM debian:11-slim AS build
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes python3-venv gcc libpython3-dev && \
    python3 -m venv /venv && \
    /venv/bin/pip install --upgrade pip setuptools wheel

# Build the virtualenv as a separate step
#
FROM build AS build-venv
COPY requirements.txt /requirements.txt
RUN /venv/bin/pip install --disable-pip-version-check -r /requirements.txt

# Run random walk simulation
#
FROM build-venv AS rwalker
COPY rwalker.py /app/rwalker.py
RUN /venv/bin/python3 /app/rwalker.py

# Dash app on distroless image:
#   * Copy the virtualenv into it /venv
#   * Copy simulation data results into /data
#
FROM gcr.io/distroless/python3-debian11:nonroot
COPY --from=build-venv /venv /venv
COPY --from=rwalker /app/data /data
COPY . /app
WORKDIR /app
ENTRYPOINT ["/venv/bin/gunicorn", "--bind", ":8080", "--workers", "2", "rwalk:app"]
