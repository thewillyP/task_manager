FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim@sha256:f106758c361464e22aa1946c1338ae94de22ec784943494f26485d345dac2d85
ENV UV_COMPILE_BYTECODE=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    openssh-server \
    apt-utils \
    bash \
    build-essential \
    ca-certificates \
    curl \
    wget \
    git \
    nano \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Node js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && apt-get install -y nodejs

RUN mkdir /var/run/sshd

WORKDIR /workspace

COPY . .

RUN chmod +x ./entrypoint.sh

RUN uv pip install --system --no-cache -r ./backend/requirements.txt

RUN cd ./frontend && npm install && npm run build

ENTRYPOINT ["/workspace/entrypoint.sh"]
CMD []
