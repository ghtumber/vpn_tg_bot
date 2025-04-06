FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

RUN mkdir bot

ADD . /bot

WORKDIR /bot

#RUN rm -R .venv

RUN uv sync

CMD ["uv", "run", "main.py"]