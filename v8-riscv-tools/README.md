# V8 RISC-V Tools

This directory is for tools developed specifically for the development of the RISC-V backend. This directory will ultimately not be upstreamed.

## analyze.py

This is a simple tool to parse debug output from the RISC-V assembler and
simulator to generate information useful for debugging.

Current features:
* Call stack

To use the tool, first execute your test with the flags `--print-all-code` and
`--trace-sim`, dumping the output to a file. Then execute this tool, passing
it that dump file and it will generate the call stack to stdout.
```bash
$ cctest --print-all-code -trace-sim test-interpreter-intrinsics/Call &> out
$ analyze.py out
```

The full usage information can be printed using `--help`:
```
usage: analyze.py [-h] [--inline] [--target TARGET] [--print-host-calls]
                  [--fp]
                  logfile

positional arguments:
  logfile

optional arguments:
  -h, --help          show this help message and exit
  --inline            Print comments inline with trace
  --target TARGET     Specify the target architecture
  --print-host-calls  Print info about calls to host functions
  --fp                Print floating point arguments and return values
```
