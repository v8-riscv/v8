#!/usr/bin/python3

# Copyright 2020 the V8 project authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import sys
import re
import time
from collections import Counter
import argparse
from prettytable import PrettyTable

def isIntN(x, n):
    limit = (1 << (n-1))
    return -limit <= x < limit

def isUIntN(x, n):
    return (x >> n) == 0

class Instruction:

    def __init__(self, line, pc, insnHex, insn, operands, offset):
        self.line = line
        self.pc = pc
        self.insnHex = insnHex
        self.insn = insn
        self.operands = operands
        self.offset = offset

    def __repr__(self):
        return f"{self.pc:x} {self.insnHex:08x} {self.insn} {','.join(self.operands)}"

    def __is3BitReg(self, reg):
        return bool(re.match(r'^f?(s[01]|a[0-5])$', reg))

    def __checkConstraint(self, fn):
        return fn(*self.operands)

    def isConvertible(self):
        if self.insn in ['nop', 'ebreak', 'mv']:
            return True
        if self.insn in ['lw', 'flw', 'sw', 'fsw']:
            return self.__checkConstraint(lambda rd, offset, rs:
                                            rs == 'sp'
                                            and isUIntN(int(offset), 8)
                                            and (int(offset) & 0x3) == 0)
        if self.insn in ['ld', 'fld', 'sd', 'fsd']:
            return self.__checkConstraint(lambda rd, offset, rs:
                                            rs == 'sp'
                                            and isUIntN(int(offset), 9)
                                            and (int(offset) & 0x7) == 0)
        if self.insn in ['jalr', 'jr']:
            return len(self.operands) == 1
        if self.insn in ['jal', 'j']:
            return len(self.operands) == 1 \
                and self.__checkConstraint(lambda offset:
                                            isUIntN(int(offset), 12)
                                            and (int(offset) & 0x1) == 0)
        if self.insn in ['beq', 'bne']:
            return self.__checkConstraint(lambda rs1, rs2, offset:
                                            rs2 == 'zero_reg'
                                            and self.__is3BitReg(rs1) \
                                            and isIntN(int(offset), 9)
                                            and (int(offset) & 0x1) == 0)
        if self.insn in ['and', 'or', 'xor', 'sub', 'andw', 'subw']:
            return self.__checkConstraint(lambda rd, rs1, rs2:
                                            rd == rs1 \
                                            and self.__is3BitReg(rd) \
                                            and self.__is3BitReg(rs2))
        if self.insn in ['andi']:
            return self.__checkConstraint(lambda rd, rs, imm: rd == rs \
                                                        and self.__is3BitReg(rd) \
                                                        and isIntN(int(imm, 16), 6))
        if self.insn in ['li']:
            return self.__checkConstraint(lambda rd, imm: isIntN(int(imm), 6))
        if self.insn in ['lui']:
            return self.__checkConstraint(lambda rd, imm:
                                            (rd != 'zero_reg' or rd != 'sp')
                                            and isUIntN(int(imm, 16), 6))
        if self.insn in ['slli']:
            return self.__checkConstraint(lambda rd, rs, shamt:
                                            rd == rs
                                            and isUIntN(int(shamt), 6))
        if self.insn in ['srli', 'srai']:
            return self.__checkConstraint(lambda rd, rs, shamt:
                                            rd == rs
                                            and self.__is3BitReg(rd)
                                            and isUIntN(int(shamt), 6))
        if self.insn in ['add']:
            return self.__checkConstraint(lambda rd, rs1, rs2: rd == rs1)
        if self.insn in ['addi']:
            return self.__checkConstraint(lambda rd, rs, imm:
                                            # C.ADDI
                                            (rd == rs and isIntN(int(imm), 6))
                                            # C.ADDI16SP
                                            or (rd == rs and rd == 'sp'
                                                and isIntN(int(imm), 10)
                                                and (int(imm) & 0xF == 0))
                                            # C.ADDI4SPN
                                            or (self.__is3BitReg(rd)
                                                and rs == 'sp'
                                                and isUIntN(int(imm), 10)
                                                and (int(imm) & 0x3) == 0))
        if self.insn in ['addiw']:
            return self.__checkConstraint(lambda rd, rs, imm: rd == rs
                                                        and isIntN(int(imm), 6))
        if self.insn in ['sext.w']:
            return self.__checkConstraint(lambda rd, rs: rd == rs)

        return False

    def insnSize(self):
        return 32 if self.insnHex & 0x3 == 0x3 else 16

    def isShort(self):
        return self.insnSize() == 16

    # Create an Instruction from a line of the code dump, or if it
    # does not look like an instruction, return None
    # A normal instruction looks like:
    #  0x55a1aa324b38   178  00008393       mv        t2, ra
    @classmethod
    def fromLine(cls, line):
        words = line.split()
        if len(words) < 4:
            return None
        pc = None
        offset = None
        insnHex = None
        try:
            pc = int(words[0], 16)
            offset = int(words[1], 16)
            insnHex = int(words[2], 16)
        except ValueError:
            pass
        if pc is None or offset is None or insnHex is None:
            return None

        insn = words[3]
        operands = []
        for idx in range(4, len(words)):
            word = words[idx]
            parts = re.split('[\(\)]', word)
            for part in parts:
                if len(part) > 0:
                    operands.append(part.strip(','))
            if not word.endswith(','):
                # This is the last operand
                break
        return cls(line, pc, insnHex, insn, operands, offset) if insn != 'constant' else None

def printTable(lst):
    if len(lst) == 0:
        print("---- No Generated Code ----")
        return

    summary = PrettyTable(["Summary", "All Instr", "Convertible", "Ratio"])
    cnt1 = sum([x[1] for x in lst])
    cnt2 = sum([x[2] for x in lst])
    summary.add_row(["", cnt1, cnt2, "{:.2%}".format(float(cnt2) / cnt1)])
    print(summary)

    tbl = PrettyTable(["Instruction", "Total", "Convertible", "Ratio"])
    for x in lst:
        row = [x[0], x[1], x[2], "{:.2%}".format(float(x[2]) / x[1])]
        tbl.add_row(row)
    print(tbl)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        dest='verbose', help='print all convertible instructions')
    parser.add_argument('logfile', nargs=1)
    args = parser.parse_args()

    startTime = time.time()
    rawCounter = Counter()
    convertibleCounter = Counter()

    logfile = open(args.logfile[0])
    nextLine = logfile.readline()
    if args.verbose:
        print("Convertible Instructions:")
    while nextLine:
        line = nextLine
        nextLine = logfile.readline()

        words = line.split()
        if len(words) == 0:
            continue

        insn = Instruction.fromLine(line)
        if insn is not None and not insn.isShort():
            rawCounter[insn.insn] += 1
            try:
                if insn.isConvertible():
                    if args.verbose:
                        print(line, end = '')
                    convertibleCounter[insn.insn] += 1
            except BaseException:
                print("Error Line: ", line, end = '')
    logfile.close()

    result = [(x, rawCounter[x], convertibleCounter[x]) for x in convertibleCounter]
    result.sort(key=lambda x: -x[2])
    print()
    printTable(result)
    print('time cost -- {:.2f}s'.format(time.time() - startTime))
