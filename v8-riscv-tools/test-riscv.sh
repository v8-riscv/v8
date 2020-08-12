#!/bin/sh

SCRIPT=$(readlink -f "$0")
DIR=$(dirname "$SCRIPT")

$DIR/../tools/run-tests.py -p verbose --report --outdir=out/riscv64.sim cctest
$DIR/../tools/run-tests.py -p verbose --report --outdir=out/riscv64.sim unittests
$DIR/../tools/run-tests.py -p verbose --report --outdir=out/riscv64.sim wasm-api-tests wasm-js
$DIR/../tools/run-tests.py -p verbose --report --outdir=out/riscv64.sim mjsunit
$DIR/../tools/run-tests.py -p verbose --report --outdir=out/riscv64.sim intl message debugger inspector mkgrokdump
