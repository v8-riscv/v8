#!/usr/bin/python3

# Copyright 2020 the V8 project authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import sys
import re
import subprocess
from collections import Counter
import argparse


def count(sub):
    couts = []
    for line in sub.stdout.readlines():
        split = line.strip().decode('utf-8').split()
        if("0x" not in split[0]):
            continue
        if(len(split) >= 4):
            couts.append(split[2])
    cout = Counter(couts).items()
    cout = list(cout)
    cout.sort(key=lambda x: x[1], reverse=True)
    
    return len(couts), cout

def init():
    parser = argparse.ArgumentParser()
    parser.add_argument('arch1', help="The path of an architecture executable d8.")
    parser.add_argument('arch2', help="The path of an architecture executable d8.")
    parser.add_argument('d8_object', nargs='+', help="The path to the target of d8 operation")
    args, unknown = parser.parse_known_args()
    return args, unknown


def compare(arch1, arch2):
    print("\t{}\t\t\t\t{}\n".format(arch1[2], arch2[2]))
    print("total:\t{}\t\t\t\t{}\t\t\tmore: {:.2%}\n".format(
        arch1[0], arch2[0], float(arch1[0] - arch2[0]) / arch2[0]))
    print("\tinstr\tratio\tcount\t",end=' ')
    print("\tinstr\tratio\tcount")
    print("------------------------------------------------------------------------")
    for n, v in zip(arch1[1], arch2[1]):
        print("\t{}\t{:.2%}\t{}\t".format(n[0], float(n[1]) / arch1[0],n[1]),end=' ')
        print("\t{}\t{:.2%}\t{}".format(v[0], float(v[1]) / arch2[0], n[1]))


if __name__ == "__main__":
    args, run_args = init()
    run_args.append("--trace-sim")
    run_args.insert(0, args.arch1)
    run_args.extend(args.d8_object)
    print(args,run_args)
    sub = subprocess.Popen(
        run_args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    risv = (count(sub))+tuple(["arch1"])

    run_args[0] = args.arch2
    sub = subprocess.Popen(
        run_args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    mips64el = (count(sub))+tuple(["arhc2"])
    compare(risv, mips64el)
    pass
