# syntax=docker/dockerfile:1
FROM python:3.13-alpine

WORKDIR /app

COPY requirements.txt ./

RUN apk add curl ca-certificates
RUN pip install -r requirements.txt && rm requirements.txt

COPY main.py ota pictures ./

CMD ["python3", "main.py"]
