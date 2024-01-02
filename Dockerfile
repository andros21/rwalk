# Apko Chainguard Images!
# => https://github.com/chainguard-dev/apko
# => https://github.com/chainguard-images
#

# cgr.dev/chainguard/python:latest-dev for build
# => https://github.com/chainguard-images/images/tree/main/images/python
#
FROM cgr.dev/chainguard/python:latest-dev AS venv
WORKDIR /home/nonroot
RUN ["/usr/bin/python3", "-m" , "venv", ".venv"]
COPY requirements.txt requirements.txt
RUN [".venv/bin/pip", "install", "--no-cache-dir", "--disable-pip-version-check", "--require-hashes", "-r", "requirements.txt"]
# Run random walk simulation
COPY rwalker.py rwalker.py
RUN [".venv/bin/python3", "rwalker.py"]

# cgr.dev/chainguard/python:latest digest for deploy
# => https://github.com/chainguard-images/images/tree/main/images/python
#  * Copy venv from st stage
#  * Copy simulation data results from nd stage
#
FROM cgr.dev/chainguard/python:latest@sha256:be8106b35d26afee7e4c81efc80cda19e60a3b20bc759f2f71e799eea3d3eaf6
WORKDIR /home/nonroot
COPY . .
COPY --from=venv /home/nonroot/.venv .venv
COPY --from=venv /home/nonroot/data /data
EXPOSE 8080
ENTRYPOINT [".venv/bin/gunicorn", "--bind", ":8080", "--workers", "2", "rwalk:app"]
