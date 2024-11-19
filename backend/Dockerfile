FROM python:3.10-slim

WORKDIR /app

# Use netcat-openbsd as the package for netcat
RUN apt-get update && apt-get install -y libmagic1 curl ffmpeg postgresql-client netcat-openbsd && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

COPY poetry.lock pyproject.toml ./
COPY /src ./src

RUN poetry install

COPY /alembic ./alembic
COPY .env ./.env
COPY init_db.py ./init_db.py
COPY alembic.ini ./alembic.ini

EXPOSE 8123

CMD ["poetry", "run", "start"]