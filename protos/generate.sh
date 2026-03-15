#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_BASE="$SCRIPT_DIR/../pydoover/models/generated"

# Map each proto file to its output subdirectory
declare -A PROTO_MAP=(
    ["device_agent.proto"]="device_agent"
    ["modbus_iface.proto"]="modbus"
    ["platform_iface.proto"]="platform"
)

for proto in "${!PROTO_MAP[@]}"; do
    subdir="${PROTO_MAP[$proto]}"
    out_dir="$OUTPUT_BASE/$subdir"

    echo "Generating $proto -> $out_dir"

    # Clean and recreate output directory
    rm -rf "$out_dir"
    mkdir -p "$out_dir"

    # Use a temp staging directory so protoc generates with the right import prefix
    staging="$SCRIPT_DIR/_staging"
    rm -rf "$staging"
    mkdir -p "$staging/$subdir"
    cp "$SCRIPT_DIR/$proto" "$staging/$subdir/"

    # Generate into staging
    uv run python -m grpc_tools.protoc \
        -I"$staging" \
        --python_out="$staging" \
        --pyi_out="$staging" \
        --grpc_python_out="$staging" \
        "$staging/$subdir/$proto"

    # Remove the copied proto
    rm "$staging/$subdir/$proto"

    # Fix imports: "from <subdir>" -> "from ."
    # see: https://stackoverflow.com/questions/16745988/sed-command-with-i-option-in-place-editing-works-fine-on-ubuntu-but-not-mac
    sed -i.bak "s/^from $subdir/from ./" "$staging/$subdir/"*.py
    rm -f "$staging/$subdir/"*.bak

    # Move generated files to final location
    mv "$staging/$subdir/"* "$out_dir/"
    touch "$out_dir/__init__.py"

    rm -rf "$staging"
done

echo "Done."
