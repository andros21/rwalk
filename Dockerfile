ARG BASE_IMAGE=slim-bullseye
ARG PYTHON_VERSION=3.9

FROM python:${PYTHON_VERSION}-${BASE_IMAGE}

RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt .
RUN python -m pip install -r requirements.txt

COPY . .

EXPOSE 8080

# run rwalker, save results and start rwalk dash app
CMD python rwalker.py && gunicorn --bind :8080 --workers 2 rwalk:app
