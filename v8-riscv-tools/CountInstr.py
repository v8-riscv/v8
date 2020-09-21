#!/usr/bin/python3

# Copyright 2020 the V8 project authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import sys
import re
import subprocess
from collections import Counter
import argparse
from prettytable import PrettyTable 

def Count(sub):
    couts = Counter()
    for line in sub.stdout:
        split = line.strip().decode('utf-8').split()
        if("0x" not in split[0]):
            continue
        if(len(split) >= 4):
            couts.update([split[2]])
    cout = couts.items()
    cout = list(cout)
    cout.sort(key=lambda x: x[1], reverse=True)

    num = 0
    for key, value in couts.items():
        num += value

    return num, cout

def ArgsInit():
    parser = argparse.ArgumentParser()
    parser.add_argument('arch1', help="The path of an architecture executable d8.")
    parser.add_argument('arch2', help="The path of an architecture executable d8.")
    parser.add_argument('d8_object', nargs='+', help="The path to the target of d8 operation")
    args, unknown = parser.parse_known_args()
    return args, unknown


def Compare(arch1, arch2):
    summary = PrettyTable(["Summary", arch1[2], arch2[2]])
    summary.add_row(["count", arch1[0], arch2[0]])
    print(summary)

    x = PrettyTable(["arch1_instr","arch1_ratio","arch1_count","arch2_instr","arch2_ratio","arch2_count"])
    for n, v in zip(arch1[1], arch2[1]):
        row = [n[0], "{:.2%}".format(float(n[1]) / arch1[0]),n[1]]
        row.extend([v[0], "{:.2%}".format(float(v[1]) / arch2[0]), v[1]])
        x.add_row(row)
    print(x)

if __name__ == "__main__":
    args, run_args = ArgsInit()
    run_args.append("--trace-sim")
    run_args.insert(0, args.arch1)
    run_args.extend(args.d8_object)
    sub = subprocess.Popen(
        run_args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    risv = (Count(sub))+tuple(["arch1"])

    run_args[0] = args.arch2
    sub = subprocess.Popen(
        run_args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    mips64el = (Count(sub))+tuple(["arhc2"])
    Compare(risv, mips64el)
    pass
