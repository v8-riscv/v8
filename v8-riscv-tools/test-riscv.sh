#!/bin/sh

set -e

SCRIPT=$(readlink -f "$0")
DIR=$(dirname "$SCRIPT")

while getopts ":o:" opt; do
    case "$opt" in
    o)
        outdir="$OPTARG"
        ;;
    \?)
        echo "Unknown Parameter: $OPTARG" 1>&2
        exit 1
        ;;
    :)
        echo "Error: -o needs a parameter: $0 -o out/riscv64.sim" 1>&2
        exit 1
        ;;
    esac
done

[ -z "$outdir" ] && outdir=out/riscv64.sim
shift $((OPTIND - 1))

$DIR/../tools/run-tests.py -p verbose --report --outdir="$outdir" \
    cctest \
    unittests \
    wasm-api-tests \
    wasm-js \
    mjsunit \
    intl \
    message \
    debugger \
    inspector \
    mkgrokdump \
    wasm-spec-tests \
    fuzzer
