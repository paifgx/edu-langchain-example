# Support Copilot workshop developer container: Python 3.12 + UV (no pip for project deps)
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

USER root

# Base image ships a Yarn APT source whose signing key rotated; it breaks `apt-get update`.
RUN find /etc/apt/sources.list.d -maxdepth 1 \( -name 'yarn*.list' -o -name 'yarn*.sources' \) -delete 2>/dev/null || true

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    jq \
    less \
    ripgrep \
    tree \
    && rm -rf /var/lib/apt/lists/*

# UV binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN chmod 755 /usr/local/bin/uv

USER vscode

ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1
