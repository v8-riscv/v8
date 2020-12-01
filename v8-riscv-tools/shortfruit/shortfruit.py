#!/usr/bin/env python3

from random import choice, choices, expovariate, randint, randrange, shuffle, uniform
import configparser
import os
import re
import string
import subprocess
import sys
from prettytable import PrettyTable

PATH_TO_V8_RISCV = '../../out/mips64el_debug/d8'
PATH_TO_V8_MIPS = '../../out/riscv64.sim/d8'

def georand(lmb):
    # roughly geometrically distributed
    return int(expovariate(lmb))

def random_id():
    return ''.join(choices(
        string.ascii_uppercase +
        string.ascii_lowercase +
        string.digits, k=8))

def filter_asm(asm):
    in_instr_block = False

    for line in asm.splitlines():
        if line.startswith('Instructions'):
            in_instr_block = True
            continue
        
        if not in_instr_block:
            continue
        # remove comments
        # m = re.match(r'^([^#]*)#(.*)$', line)
        # if m:
        #     line = m.group(1)

        line = line.strip()

        if in_instr_block and len(line) == 0:
            return

        if not line.startswith('0x') and not line.startswith('--'):
            continue

        yield line

def instr_cost(line):
    # TODO: more specific cost estimation for riscv & mips
    return 1

    parts = re.split('[ \t,]', line)
    instr = parts[0]
    cost_load_store = 2
    cost_fpu_load_store = cost_load_store
    cost_alu = 1
    cost_fpu = 1
    cost_branch = 3
    cost_mul = cost_branch
    cost_div = 8    # TODO: clang generates long instr. sequences instead of div
    cost_call = 20  # TODO: builtins
    cost_ret = 2
    cost_ebreak = 0 # should be unreachable if no undef. behavior is generated

    if instr == 'li':
        imm = int(parts[-1])
        if imm >= -2048 and imm < 2048: # addi
            return cost_alu
        elif (imm & 0xFFF) == 0:        # lui
            return cost_alu
        else:                           # lui + addi
            return cost_alu * 2

    return {
        'add': cost_alu,
        'addi': cost_alu,
        'addiw': cost_alu,
        'addw': cost_alu,
        'and': cost_alu,
        'andi': cost_alu,
        'beq': cost_branch,
        'beqz': cost_branch,
        'bge': cost_branch,
        'bgeu': cost_branch,
        'bgez': cost_branch,
        'bgt': cost_branch,
        'bgtu': cost_branch,
        'bgtz': cost_branch,
        'ble': cost_branch,
        'bleu': cost_branch,
        'blez': cost_branch,
        'blt': cost_branch,
        'bltu': cost_branch,
        'bltz': cost_branch,
        'bne': cost_branch,
        'bnez': cost_branch,
        'call': cost_call,
        'div': cost_div,
        'divu': cost_div,
        'divuw': cost_div,
        'divw': cost_div,
        'ebreak': cost_ebreak,
        'fadd.d': cost_fpu,
        'fadd.s': cost_fpu,
        'fcvt.d.l': cost_fpu,
        'fcvt.d.lu': cost_fpu,
        'fcvt.d.s': cost_fpu,
        'fcvt.d.w': cost_fpu,
        'fcvt.d.wu': cost_fpu,
        'fcvt.l.d': cost_fpu,
        'fcvt.l.s': cost_fpu,
        'fcvt.lu.d': cost_fpu,
        'fcvt.lu.s': cost_fpu,
        'fcvt.s.d': cost_fpu,
        'fcvt.s.l': cost_fpu,
        'fcvt.s.lu': cost_fpu,
        'fcvt.s.w': cost_fpu,
        'fcvt.s.wu': cost_fpu,
        'fcvt.w.d': cost_fpu,
        'fcvt.w.s': cost_fpu,
        'fcvt.wu.d': cost_fpu,
        'fcvt.wu.s': cost_fpu,
        'fdiv.d': cost_fpu,
        'fdiv.s': cost_fpu,
        'feq.d': cost_fpu,
        'feq.s': cost_fpu,
        'fge.d': cost_fpu,
        'fge.s': cost_fpu,
        'fgt.d': cost_fpu,
        'fgt.s': cost_fpu,
        'fld': cost_fpu_load_store,
        'fle.d': cost_fpu,
        'fle.s': cost_fpu,
        'flt.d': cost_fpu,
        'flt.s': cost_fpu,
        'flw': cost_fpu_load_store,
        'fmadd.d': cost_fpu,
        'fmadd.s': cost_fpu,
        'fmul.d': cost_fpu,
        'fmul.s': cost_fpu,
        'fmv.d': cost_fpu,
        'fmv.d.x': cost_fpu,
        'fmv.s': cost_fpu,
        'fmv.s.x': cost_fpu,
        'fmv.w.x': cost_fpu,
        'fmv.x.s': cost_fpu,
        'fneg.d': cost_fpu,
        'fneg.s': cost_fpu,
        #'fnmsub.s': cost_fpu, # not found yet
        'fnmsub.d': cost_fpu,
        'fsd': cost_fpu_load_store,
        'fsub.d': cost_fpu,
        'fsub.s': cost_fpu,
        'fsw': cost_fpu_load_store,
        'j': cost_branch,
        'jr': cost_branch,
        'lb': cost_load_store,
        'lbu': cost_load_store,
        'ld': cost_load_store,
        'lh': cost_load_store,
        'lhu': cost_load_store,
        'lui': cost_alu,
        'lw': cost_load_store,
        'lwu': cost_load_store,
        'mul': cost_mul,
        'mulh': cost_mul,
        'mulhu': cost_mul,
        'mulw': cost_mul,
        'mv': cost_alu,
        'neg': cost_alu,
        'negw': cost_alu,
        'nop': cost_alu,
        'not': cost_alu,
        'or': cost_alu,
        'ori': cost_alu,
        'rem': cost_div,
        'remu': cost_div,
        'remuw': cost_div,
        'remw': cost_div,
        'ret': cost_ret,
        'sb': cost_load_store,
        'sd': cost_load_store,
        'seqz': cost_alu,
        'sext': cost_alu,
        'sext.w': cost_alu,
        'sgt': cost_alu,
        'sgtu': cost_alu,
        'sgtz': cost_alu,
        'sh': cost_load_store,
        'sll': cost_alu,
        'slli': cost_alu,
        'slliw': cost_alu,
        'sllw': cost_alu,
        'slt': cost_alu,
        'slti': cost_alu,
        'sltiu': cost_alu,
        'sltu': cost_alu,
        'snez': cost_alu,
        'sra': cost_alu,
        'srai': cost_alu,
        'sraiw': cost_alu,
        'sraw': cost_alu,
        'srl': cost_alu,
        'srli': cost_alu,
        'srliw': cost_alu,
        'srlw': cost_alu,
        'sub': cost_alu,
        'subw': cost_alu,
        'sw': cost_load_store,
        'xor': cost_alu,
        'xori': cost_alu,
    }[instr]

def compile(arch, filename):
    if arch == 'riscv':
        prog = PATH_TO_V8_RISCV
    elif arch == 'mips':
        prog = PATH_TO_V8_MIPS
    else:
        assert False, 'unsupported arch'

    opts = [
        '--allow-natives-syntax',
        '--print-code',
        '--code-comments',
        filename
    ]

    res = subprocess.check_output([prog] + opts).decode('utf-8')
    return res

def get_cost(asm):
    bb_cost = {}
    cur_bb = ''
    for line in filter_asm(asm):
        if line.startswith('--'):
            cur_bb = line
            bb_cost[cur_bb] = 0
            continue

        cost = instr_cost(line)
        bb_cost[cur_bb] += cost
    return bb_cost

class Context:
    def __init__(self):
        self.var_counter = 0
        self.vars = []

    def gen_var(self, loop_counter = False):
        if not loop_counter:
            v = f'v{self.var_counter}'
            self.vars.append(v)
        else:
            v = f'i{self.var_counter}'
        self.var_counter = self.var_counter + 1
        return v

    def gen_vars(self, num):
        return [self.gen_var() for _ in range(num)]

    def rand_var(self):
        return choice(self.vars)

    def copy(self):
        ctx = Context()
        ctx.var_counter = self.var_counter
        ctx.vars = self.vars.copy()
        return ctx

def gen_type():
    return choice([
        'char', 'short', 'int', 'long', 'long long',
        'float', 'double'
    ])

def gen_type_integer():
    signed = choice(['signed', 'unsigned'])
    ty = choice(['char', 'short', 'int', 'long', 'long long'])
    return f'{signed} {ty}'

def gen_cast_integer():
    # return f'({gen_type_integer()})'
    return f''

def gen_expr_literal_int_zero():
    return 0

def gen_expr_literal_int_12_bit():
    return randrange(-2048, 2048)

def gen_expr_literal_int_20_bit_up():
    return randrange(0, 2**20) << 12

def gen_expr_literal_int_32_bit():
    return randrange(-2**31, 2**31)

def gen_expr_literal_int_64_bit():
    return randrange(-2**63, 2**63)

def gen_expr_literal_float():
    return uniform(-1_000_000, 1_000_000)

def gen_expr_literal(ctx = None):
    v = choice([
        gen_expr_literal_int_zero,
        gen_expr_literal_int_12_bit,
        gen_expr_literal_int_20_bit_up,
        gen_expr_literal_int_32_bit,
        gen_expr_literal_int_64_bit,
        gen_expr_literal_float,
    ])()
    return v

def gen_expr_var(ctx):
    return ctx.rand_var()

def gen_expr_unary(ctx):
    a = ctx.rand_var()
    op = choice(['-', '~', '!', '++', '--'])
    cast = ''
    if op == '~':
        # must be applied to an integer operand
        cast = gen_cast_integer()
    return f'{op}{cast}{a}'

def gen_expr_binary(ctx):
    a = ctx.rand_var()
    b = ctx.rand_var()
    ops = [
        '^', '&', '|', '<<', '>>',
        '+', '-',
        '*', '/', '%',
        '==', '!=',
        '<', '<=', '>', '>=',
        '&&', '||'
    ]
    op = choice(ops)
    cast1 = ''
    cast2 = ''
    if op in ['^', '&', '|', '%', '<<', '>>']:
        # must be applied to integer operands
        cast1 = gen_cast_integer()
        cast2 = gen_cast_integer()
    return f'{cast1}{a} {op} {cast2}{b}'

def gen_expr_ternary(ctx):
    a = ctx.rand_var()
    b = ctx.rand_var()
    c = ctx.rand_var()
    return f'{a} ? {b} : {c}'

def gen_expr(ctx):
    return choice([
        gen_expr_var,
        gen_expr_literal,
        gen_expr_unary,
        gen_expr_binary,
        gen_expr_ternary,
    ])(ctx)

def gen_stmt_decl(ctx):
    # t = gen_type()
    e = gen_expr(ctx)
    v = ctx.gen_var()
    # s = f'{t} {v} = {e};'
    s = f'var {v} = {e};'
    return s

def gen_stmt_assign(ctx):
    # avoid assigning to loop counters
    while True:
        v = ctx.rand_var()
        if v[0] != 'i':
            break
    e = gen_expr(ctx)
    return f'{v} = {e};'

def gen_stmt_loop(ctx):
    loop_ctx = ctx.copy()
    # t = gen_type_integer()
    i = loop_ctx.gen_var(loop_counter = True)
    end = randrange(1, 127)
    return (
        f'for(var {i} = 0; {i} < {end}; ++{i}) {{\n'
        f'{gen_block(loop_ctx, randint(1, 10) < 5)}'
        f'}}'
    )

def gen_stmt(ctx, no_loop=False):
    stmts = [
        gen_stmt_decl,
        gen_stmt_assign,
        gen_stmt_loop,
    ]
    if (no_loop):
        stmts.pop()
    stmt = choice(stmts)(ctx)
    return f'{stmt}\n'

def gen_block(ctx, no_loop=False):
    block = ''
    for i in range(min(5, georand(0.5))):
        block = block + gen_stmt(ctx, no_loop)
    return block

def gen_func_args(ctx, n=-1):
    if (n == -1):
        n = georand(0.2) + 1
    args = [v for v in ctx.gen_vars(n)]
    return ', '.join(args)

def gen_func_paras(n):
    paras = [str(gen_expr_literal()) for _ in range(n)]
    return ', '.join(paras)

def gen_func(ctx, num_args):
    return (
        f'function test({gen_func_args(ctx, num_args)}) {{\n'
        f'{gen_block(ctx)}'
        f'return {ctx.rand_var()};\n'
        f'}}'
    )

def gen_global(ctx):
    g = ctx.gen_var()
    return f'var {g} = {gen_expr_literal()};'

def gen_globals(ctx):
    globals = ''
    for i in range(georand(1.0)):
        g = gen_global(ctx)
        globals = f'{globals}{g}\n'
    return globals

def gen_unit(ctx):
    # for now, one function with some parameter and access to some globals
    n = georand(0.2) + 1
    assert n != -1
    paras = gen_func_paras(n)

    unit = gen_globals(ctx)
    unit = f'{unit}{gen_func(ctx, n)}\n'
    unit = f'{unit}%PrepareFunctionForOptimization(test);\n'
    unit = f'{unit}test({paras});\n'
    unit = f'{unit}%OptimizeFunctionOnNextCall(test);\n'
    unit = f'{unit}test({paras});\n'
    return unit

def gen_test(filename):
    with open(filename, 'w') as f:
        ctx = Context()
        print(gen_unit(ctx), file=f)

def compare_bb_cost(c1, c2):
    total_diff = 0
    for bb in c1:
        # print(bb, c1[bb] - c2[bb])
        total_diff += max(c1[bb] - c2[bb], 0)
    return total_diff

def print_cost_table(cost_riscv, cost_mips, f=sys.stdout):
    x = PrettyTable(["Basic Block","RISCV64 cost","MIPS64 cost", "Difference"])
    x._max_width = {"Basic Block" : 30}
    for bb in cost_riscv:
        diff = cost_riscv[bb] - cost_mips[bb]
        bb_prefix = bb[3:-3]
        x.add_row([bb_prefix, cost_riscv[bb], cost_mips[bb], diff])
    print(x, file=f)


def test_file(filename, arch, abi):
    asm_gcc = compile('gcc', arch, abi, filename)
    c1 = get_cost(asm_gcc)
    asm_clang = compile('clang', arch, abi, filename)
    c2 = get_cost(asm_clang)
    return c1, c2, asm_gcc, asm_clang

def read_file(fn):
    with open(fn) as f:
        return f.read()

def write_config(filename, cost1, cost2):
    config = configparser.ConfigParser()
    config.add_section('scenario')
    config['scenario']['filename'] = filename
    config['scenario']['run command'] = ' '.join([
        PATH_TO_V8_RISCV,
        '--allow-natives-syntax',
        '--print-code',
        '--code-comments',
        filename])
    with open('scenario.ini', 'w') as f:
        config.write(f)
    return config

def write_result(f, config, asm_riscv, asm_mips):
    config.write(f)
    filename = config['scenario']['filename']
    print(f'### Source:\n{read_file(filename)}', file=f)
    print(f'\n### V8 RISCV64:\n{asm_riscv}', file=f)
    print(f'\n### V8 MIPS64:\n{asm_mips}', file=f)

def run_test(filename):
    asm1 = compile('riscv', filename)
    c1 = get_cost(asm1)
    asm2 = compile('mips', filename)
    c2 = get_cost(asm2)
    return c1, c2, asm1, asm2

def reduce_case(filename):
    subprocess.check_output(['creduce', 'test.py', filename])

def main():
    cnt = 0
    while True:
        id = random_id()
        source_file = f'case-{id}.js'
        case_file = f'case-{id}.txt'
        gen_test(source_file)
        passed = False

        cnt += 1
        print(f"test case {cnt} : {source_file}")

        cost_riscv, cost_mips, asm_riscv, asm_mips = run_test(source_file)
        if compare_bb_cost(cost_riscv, cost_mips) > 0:
            print_cost_table(cost_riscv, cost_mips)
            passed = True
            config = write_config(source_file, cost_riscv, cost_mips)

            # print('reducing')
            # reduce_case(source_file)
            # c1, c2, asm1, asm2 = run_test(source_file, arch, abi)

            # write_result(sys.stdout, config, asm_riscv, asm_mips)
            print_cost_table(cost_riscv, cost_mips, open(case_file, 'w'))
            write_result(open(case_file, 'a'), config, asm_riscv, asm_mips)
            break

        if not passed:
            os.remove(source_file)
        # break

if __name__ == '__main__':
    main()
