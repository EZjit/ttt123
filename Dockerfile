FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS development_build

ARG UID=1000 \
    GID=1000

SHELL ["/bin/bash", "-eo", "pipefail", "-c"]


WORKDIR /code
RUN groupadd -g "${GID}" -r web \
    && useradd -d '/code' -g web -l -r -u "${UID}" web \
    && chown web:web -R '/code'

COPY --chown=web:web ./uv.lock ./pyproject.toml /code/

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy
ENV UV_SYSTEM_PYTHON=1
# Project initialization:
ENV UV_PROJECT_ENVIRONMENT="/opt/venv"
ENV VIRTUAL_ENV=/opt/venv
# Place entry points in the environment at the front of the path
ENV PATH="/opt/venv/bin:$PATH"

RUN echo "$APP_ENV" \
    && if [ "$APP_ENV" = "production" ]; then \
    uv sync --frozen --no-dev; \
    else \
    uv sync --frozen ; \
    fi \
    && echo "uv done"
USER web


# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
# ADD . /code


# Reset the entrypoint, don't invoke `uv`
# ENTRYPOINT []

# Run the FastAPI application by default
# Uses `fastapi dev` to enable hot-reloading when the `watch` sync occurs
# Uses `--host 0.0.0.0` to allow access from outside the container

# ENTRYPOINT ["uv", "run", "app/main.py"]

FROM development_build AS production_build
COPY --chown=web:web . /code