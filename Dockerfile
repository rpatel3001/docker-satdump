FROM ghcr.io/sdr-enthusiasts/docker-baseimage:rtlsdr

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# hadolint ignore=DL3008,SC2086,DL4006,SC2039
RUN set -x && \
    TEMP_PACKAGES=() && \
    KEPT_PACKAGES=() && \
    TEMP_PACKAGES+=() && \
    # temp
    TEMP_PACKAGES+=(git) && \
    TEMP_PACKAGES+=(libtiff-dev) && \
    TEMP_PACKAGES+=(libjemalloc-dev) && \
    # keep
    KEPT_PACKAGES+=(libtiff6) && \
    KEPT_PACKAGES+=(python3) && \
    KEPT_PACKAGES+=(python3-prctl) && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    "${KEPT_PACKAGES[@]}" \
    "${TEMP_PACKAGES[@]}" && \
    git clone https://github.com/altillimity/satdump.git /src/satdump && \
    pushd /src/satdump && \
    sed -i '/zenity/d' packages.runner && \
    xargs -a /src/satdump/packages.builder apt install --no-install-recommends -qy && \
    xargs -a /src/satdump/packages.runner apt install -qy && \
    mkdir build && \
    pushd build && \
    cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_GUI=OFF -DBUILD_ZIQ=OFF .. && \
    make -j`nproc` && \
    make install && \
    popd && popd && \
    xargs -a /src/satdump/packages.builder apt purge -qy && \
    # Clean up
    apt-get remove -y "${TEMP_PACKAGES[@]}" && \
    apt-get autoremove -y && \
    rm -rf /src/* /tmp/* /var/lib/apt/lists/*

COPY rootfs /
