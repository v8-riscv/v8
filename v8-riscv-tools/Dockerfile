# ==============================================================================
# First stage build (compile V8)
# ==============================================================================

FROM ubuntu:bionic as v8-base

ARG repo=v8-riscv/v8
ENV GITHUB_REPOSITORY=$repo
ARG sha_or_branch=riscv64
ENV GITHUB_SHA=$sha_or_branch

RUN apt-get update && apt-get upgrade -yqq

RUN DEBIAN_FRONTEND=noninteractive \
    apt-get -yqq install git \
                         curl \
                         python \
                         lsb-release \
                         pkg-config \
                         tzdata \
                         sudo

RUN git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git

ENV PATH="/depot_tools:${PATH}"

RUN fetch v8

RUN (cd /v8 && ./build/install-build-deps.sh --no-prompt --no-arm)


FROM v8-base as v8-riscv

RUN (cd /v8 && \
    git remote add riscv https://github.com/${GITHUB_REPOSITORY} && \
    git fetch riscv && \
    git checkout ${GITHUB_SHA})

RUN (cd /v8 && gclient sync --with_branch_heads --with_tags)
RUN cp /v8/patches/build.patch /v8/build/
RUN (cd /v8/build && git apply build.patch)
RUN (cd /v8 && \
    gn gen out/riscv64.sim --args='is_component_build=false is_debug=true target_cpu="x64" v8_target_cpu="riscv64" use_goma=false goma_dir="None"' && \
    ninja -C out/riscv64.sim -j8)


FROM v8-riscv as v8-test

WORKDIR /v8
ENTRYPOINT ["./v8-riscv-tools/test-riscv.sh"]
