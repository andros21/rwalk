# Apko Chainguard Images!
# => https://github.com/chainguard-dev/apko
# => https://github.com/chainguard-images
#

# Build a virtualenv using apko python-latest-dev image
# => https://github.com/chainguard-images/images/tree/main/images/python
#
ARG DIGEST=sha256:af051248511b7ee7e76d514f60d8cb7b0b0f5f926e7b464b548a5cf742c73789
FROM cgr.dev/chainguard/python@${DIGEST} AS venv
WORKDIR /home/nonroot
RUN ["/usr/bin/python3", "-m" , "venv", ".venv"]
COPY requirements.txt requirements.txt
RUN [".venv/bin/pip", "install", "--disable-pip-version-check", "-r", "requirements.txt"]

# Run random walk simulation
#
FROM venv AS rwalker
COPY rwalker.py rwalker.py
RUN [".venv/bin/python3", "rwalker.py"]

# Dash app on apko python-latest-dev
#   * Copy simulation data results into data
#
FROM venv
COPY . .
COPY --from=rwalker /home/nonroot/data data
ENTRYPOINT [".venv/bin/gunicorn", "--bind", ":8080", "--workers", "2", "rwalk:app"]
