#!/bin/bash

set -e

# https://stackoverflow.com/questions/62818183/protobuf-grpc-relative-import-path-discrepancy-in-python
# https://github.com/grpc/grpc/issues/9575

# ORIG_DIR=$(pwd)
rm -rf grpc_stubs/
mkdir -p grpc_stubs/
cp *.proto grpc_stubs/
touch grpc_stubs/__init__.py
uv run python -m grpc_tools.protoc -I. --python_out=./ --pyi_out=./ --grpc_python_out=./ ./grpc_stubs/*.proto
rm grpc_stubs/*.proto

# see: https://stackoverflow.com/questions/16745988/sed-command-with-i-option-in-place-editing-works-fine-on-ubuntu-but-not-mac
sed -i.bak 's/^from grpc_stubs/from ./' grpc_stubs/*.py
rm grpc_stubs/*.bak
# cd $ORIG_DIR