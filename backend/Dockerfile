# TODO: ongoing work
FROM python:3.11-slim AS python-base


WORKDIR /app
RUN apt-get update && apt-get install -y build-essential

# 'production' stage
FROM python-base AS production
COPY backend/pyproject.toml backend/poetry.lock /app/
ENV GIT_PYTHON_REFRESH=quiet

COPY backend/app /app/app

EXPOSE 8000
WORKDIR /app


CMD ["uv", "run", "python", "-m", "app.src.main"]
