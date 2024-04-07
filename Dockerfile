FROM ghcr.io/sdr-enthusiasts/docker-baseimage:rtlsdr

ENV NO_SDRPLAY_API="true"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

COPY satdump.patch /tmp/satdump.patch

# hadolint ignore=DL3008,SC2086,DL4006,SC2039
RUN set -x && \
    TEMP_PACKAGES=() && \
    KEPT_PACKAGES=() && \
    TEMP_PACKAGES+=() && \
    # temp
    TEMP_PACKAGES+=(build-essential) && \
    TEMP_PACKAGES+=(cmake) && \
    TEMP_PACKAGES+=(pkg-config) && \
    TEMP_PACKAGES+=(git) && \
    TEMP_PACKAGES+=(libtiff-dev) && \
    TEMP_PACKAGES+=(libjemalloc-dev) && \
    TEMP_PACKAGES+=(libusb-1.0-0-dev) && \
    # keep
    KEPT_PACKAGES+=(libusb-1.0-0) && \
    KEPT_PACKAGES+=(libtiff6) && \
    KEPT_PACKAGES+=(python3) && \
    KEPT_PACKAGES+=(python3-prctl) && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    "${KEPT_PACKAGES[@]}" \
    "${TEMP_PACKAGES[@]}" && \
    # deploy libmiri
    git clone https://github.com/ericek111/libmirisdr-5.git /src/libmirisdr-5 && \
    pushd /src/libmirisdr-5 && \
    mkdir build && \
    pushd build && \
    cmake .. && \
    make && \
    make install && \
    popd && popd && \
    # build libairspy
    git clone https://github.com/airspy/airspyhf.git /src/airspyhf && \
    pushd /src/airspyhf && \
    mkdir -p /src/airspyhf/build && \
    pushd /src/airspyhf/build && \
    cmake ../ -DCMAKE_BUILD_TYPE=Release -DINSTALL_UDEV_RULES=ON && \
    make && \
    make install && \
    ldconfig && \
    popd && popd && \
    # deploy airspyone host
    git clone https://github.com/airspy/airspyone_host.git /src/airspyone_host && \
    pushd /src/airspyone_host && \
    mkdir -p /src/airspyone_host/build && \
    pushd /src/airspyone_host/build && \
    cmake ../ -DINSTALL_UDEV_RULES=ON && \
    make && \
    make install && \
    ldconfig && \
    popd && popd && \
    # deplot satdump
    git clone https://github.com/altillimity/satdump.git /src/satdump && \
    pushd /src/satdump && \
    git apply /tmp/satdump.patch && \
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
    rm -rf /src/* /tmp/* /var/lib/apt/lists/* && \
    mkdir -p /opt && \
    pushd /opt && \
    curl --location --output /opt/citycodes.csv https://raw.githubusercontent.com/rpatel3001/Airports/main/citycodes.csv && \
    curl --location --output /opt/airports.csv https://raw.githubusercontent.com/rpatel3001/Airports/main/airports.csv && \
    popd

COPY rootfs /
