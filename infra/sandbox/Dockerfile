FROM python:3.12-slim

RUN pip install --no-cache-dir \
    pytest \
    email-validator \
    fastapi \
    httpx \
    pydantic

RUN useradd -m sandboxuser
WORKDIR /app
USER sandboxuser