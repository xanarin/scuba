#!/bin/bash
set -e

MUSL_VERSION="1.1.14"
MUSL_RELEASE="musl-${MUSL_VERSION}"

# Provide a default value for MUSL_PATH
: ${MUSL_PATH:=/usr/local/musl}
echo "\$MUSL_PATH = $MUSL_PATH"

# CC might be set to musl-gcc, which is obviously
# a problem if we haven't installed it yet! (#97)
unset CC


# Is it already installed?
ver=$(${MUSL_PATH}/lib/libc.so 2>&1 | grep Version | awk '{ print $2 }')
if [[ $ver == "$MUSL_VERSION" ]]; then
    echo "$MUSL_RELEASE already installed!"
    exit 0
fi


# Install it
cd /tmp

echo "Downloading ${MUSL_RELEASE}..."
wget https://www.musl-libc.org/releases/${MUSL_RELEASE}.tar.gz
tar xf ${MUSL_RELEASE}.tar.gz
cd ${MUSL_RELEASE}

echo "Building ${MUSL_RELEASE}..."
./configure --prefix=${MUSL_PATH}
make

echo "Installing ${MUSL_RELEASE}..."
make install


echo "${MUSL_RELEASE} installed!"
ls -l ${MUSL_PATH}/bin/musl-gcc
