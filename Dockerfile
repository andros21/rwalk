# Apko Chainguard Images!
# => https://github.com/chainguard-dev/apko
# => https://github.com/chainguard-images
#

# cgr.dev/chainguard/python:latest digest for deploy
# => https://github.com/chainguard-images/images/tree/main/images/python
#
ARG DIGEST=sha256:272572b87a8c7572a53aa4505387fabf93489f0199311dbb4ad4edbb9d39115a

# cgr.dev/chainguard/python:latest-dev for build
# => https://github.com/chainguard-images/images/tree/main/images/python
#
FROM cgr.dev/chainguard/python:latest-dev AS venv
WORKDIR /home/nonroot
RUN ["/usr/bin/python3", "-m" , "venv", ".venv"]
COPY requirements.txt requirements.txt
RUN [".venv/bin/pip", "install", "--no-cache-dir", "--disable-pip-version-check", "-r", "requirements.txt"]

# Run random walk simulation
#
FROM venv AS rwalker
COPY rwalker.py rwalker.py
RUN [".venv/bin/python3", "rwalker.py"]

# Dash app using cgr.dev/chainguard/python:latest
#  * Copy venv from st stage
#  * Copy simulation data results from nd stage
#
FROM cgr.dev/chainguard/python@${DIGEST}
WORKDIR /home/nonroot
COPY . .
COPY --from=venv /home/nonroot/.venv .venv
COPY --from=rwalker /home/nonroot/data /data
ENTRYPOINT [".venv/bin/gunicorn", "--bind", ":8080", "--workers", "2", "rwalk:app"]
