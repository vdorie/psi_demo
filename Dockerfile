# syntax=docker/dockerfile:1
FROM debian:sid-slim

RUN \
  apt-get -y update && \
  apt-get -y install \
    # install suggested build environment for pyenv
    # https://github.com/pyenv/pyenv/wiki#suggested-build-environment
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    curl \
    git \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
    # bazel requirements
    # https://bazel.build/versions/6.5.0/install/compile-source#bootstrap-unix-overview
    build-essential \
    openjdk-11-jdk \
    zip \
    unzip \
    # server folder monitoring
    inotify-tools

# Install pyenv so we can use 3.10 - OpenMined PSI doesn't install
# with python3.12
ENV HOME="/root"
WORKDIR ${HOME}
ENV PYENV_ROOT="${HOME}/.pyenv"
ENV PATH="${PYENV_ROOT}/shims:${PYENV_ROOT}/bin:${PATH}"
ENV PYTHON_VERSION=3.10.14
RUN \
    curl https://pyenv.run | bash && \
    pyenv init - && \
    pyenv install ${PYTHON_VERSION} && \
    # for logging in locally, setup pyenv
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc && \
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc && \
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc && \
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.profile && \
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.profile && \
    echo 'eval "$(pyenv init -)"' >> ~/.profile && \
    # actually set python version
    pyenv global 3.10.14 && \
    pip install --upgrade pip


# Install bazel; doing this by compiling from source since I'm on arm
# using a linux base and they don't have builds for that.
# Need version Bazel 6.x for PSI, incompatible with 7.x
ENV BAZEL_VERSION=6.5.0
RUN \
  curl -L -O https://github.com/bazelbuild/bazel/releases/download/${BAZEL_VERSION}/bazel-${BAZEL_VERSION}-dist.zip && \
  unzip bazel-${BAZEL_VERSION}-dist.zip -d bazel-src && \
  cd bazel-src && \
  env EXTRA_BAZEL_ARGS="--tool_java_runtime_version=local_jdk" bash ./compile.sh && \
  mv output/bazel /usr/local/bin

WORKDIR /app

# clone PSI from git
RUN \
  mkdir PSI && \
  cd PSI && \
  git init && \
  git remote add origin https://github.com/OpenMined/PSI.git && \
  # most recent commit as of 09/17/2024
  git fetch --depth 1 origin b6948f2124ef91e7808dfcfad6acdc050c0536e3 && \
  git checkout FETCH_HEAD

WORKDIR /app/PSI

# copy over some files that for some reason are broken
COPY PSI/private_set_intersection/cpp/datastructure/golomb.cpp private_set_intersection/cpp/datastructure
COPY PSI/private_set_intersection/deps.bzl private_set_intersection

# actually build PSI
RUN \
  # build
  bazel build -c opt //private_set_intersection/python:wheel && \  
  # turn into an installable
  pip install --no-cache-dir packaging && \
  python private_set_intersection/python/rename.py && \
  # install package
  pip install --no-cache-dir $(ls -1 ./bazel-bin/private_set_intersection/python/*.whl)


# Install package dependencies for PSI demo scripts

RUN \
  pip install --no-cache-dir \
    cryptography


# Make directories and copy in the demo scripts
RUN mkdir -p /app/agency_a /app/agency_b /app/server

COPY agency_a.py /app/agency_a
COPY agency_b.py /app/agency_b

ENTRYPOINT [ "/bin/bash", "-l", "-c" ]

CMD [ "/bin/bash" ]
