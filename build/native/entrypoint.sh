#!/bin/bash

# Run startup initialization.
CONTAINER_STARTED="/etc/container_started"
if [ ! -e $CONTAINER_STARTED ]; then
    cd $BUILD_DIR
    bash native/odc_conf.sh
    touch $CONTAINER_STARTED
    cd $WORKDIR
fi

exec "$@"
