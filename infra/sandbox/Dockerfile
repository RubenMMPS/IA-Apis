FROM python:3.12-slim

RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    email-validator \
    fastapi \
    httpx \
    pydantic \
    sqlalchemy \
    aiosqlite \
    "bcrypt<4.1" \
    passlib[bcrypt] \
    pyjwt \
    python-multipart \
    pydantic-settings

RUN useradd -m sandboxuser
WORKDIR /app
USER sandboxuser