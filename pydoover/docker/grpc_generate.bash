#!/bin/bash

set -e

ORIG_DIR=$(pwd)

for dir in device_agent platform modbus; do
    echo "Running grpc_generate for $dir..."
    cd $dir/
    ./grpc_generate.bash
    cd "$ORIG_DIR"
done
