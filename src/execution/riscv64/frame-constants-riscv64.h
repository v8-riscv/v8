// Copyright 2011 the V8 project authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#ifndef V8_EXECUTION_RISCV_FRAME_CONSTANTS_RISCV_H_
#define V8_EXECUTION_RISCV_FRAME_CONSTANTS_RISCV_H_

#include "src/base/bits.h"
#include "src/base/macros.h"
#include "src/execution/frame-constants.h"

namespace v8 {
namespace internal {

class EntryFrameConstants : public AllStatic {
 public:
  // This is the offset to where JSEntry pushes the current value of
  // Isolate::c_entry_fp onto the stack.
  static constexpr int kCallerFPOffset =
      -(StandardFrameConstants::kFixedFrameSizeFromFp + kPointerSize);
};

class WasmCompileLazyFrameConstants : public TypedFrameConstants {
 public:
  static constexpr int kNumberOfSavedGpParamRegs = 7;
  static constexpr int kNumberOfSavedFpParamRegs = 7;

  // FP-relative.
  static constexpr int kWasmInstanceOffset = TYPED_FRAME_PUSHED_VALUE_OFFSET(7);
  static constexpr int kFixedFrameSizeFromFp =
      TypedFrameConstants::kFixedFrameSizeFromFp +
      kNumberOfSavedGpParamRegs * kPointerSize +
      kNumberOfSavedFpParamRegs * kDoubleSize;
};

// Frame constructed by the {WasmDebugBreak} builtin.
// After pushing the frame type marker, the builtin pushes all Liftoff cache
// registers (see liftoff-assembler-defs.h).
class WasmDebugBreakFrameConstants : public TypedFrameConstants {
 public:
  // constexpr RegList kLiftoffAssemblerGpCacheRegs =
  //    Register::ListOf(a0, a1, a2, a3, a4, a5, a6, a7, t0, t1, t2, s7);
  static constexpr uint32_t kPushedGpRegs = 1 << 5 |   // t0
                                            1 << 6 |   // t1
                                            1 << 7 |   // t2
                                            1 << 10 |  // a0
                                            1 << 11 |  // a1
                                            1 << 12 |  // a2
                                            1 << 13 |  // a3
                                            1 << 14 |  // a4
                                            1 << 15 |  // a5
                                            1 << 16 |  // a6
                                            1 << 17 |  // a7
                                            1 << 23;   // s7

  //   constexpr RegList kLiftoffAssemblerFpCacheRegs = DoubleRegister::ListOf(
  //       ft0, ft1, ft2, ft3, ft4, ft5, ft6, ft7, fa0, fa1, fa2, fa3, fa4, fa5,
  //       fa6, fa7, ft8, ft9, ft10, ft11);
  static constexpr uint32_t kPushedFpRegs = 1 << 0 |   // ft0
                                            1 << 1 |   // ft1
                                            1 << 2 |   // ft2
                                            1 << 3 |   // ft3
                                            1 << 4 |   // ft4
                                            1 << 5 |   // ft5
                                            1 << 6 |   // ft6
                                            1 << 7 |   // ft7
                                            1 << 10 |  // fa0
                                            1 << 11 |  // fa1
                                            1 << 12 |  // fa2
                                            1 << 13 |  // fa3
                                            1 << 14 |  // fa4
                                            1 << 15 |  // fa5
                                            1 << 16 |  // fa6
                                            1 << 17 |  // fa7
                                            1 << 28 |  // ft8
                                            1 << 29 |  // ft9
                                            1 << 30 |  // ft10
                                            1 << 31;   // ft11

  static constexpr int kNumPushedGpRegisters =
      base::bits::CountPopulation(kPushedGpRegs);
  static constexpr int kNumPushedFpRegisters =
      base::bits::CountPopulation(kPushedFpRegs);

  static constexpr int kLastPushedGpRegisterOffset =
      -kFixedFrameSizeFromFp - kNumPushedGpRegisters * kSystemPointerSize;
  static constexpr int kLastPushedFpRegisterOffset =
      kLastPushedGpRegisterOffset - kNumPushedFpRegisters * kDoubleSize;

  // Offsets are fp-relative.
  static int GetPushedGpRegisterOffset(int reg_code) {
    DCHECK_NE(0, kPushedGpRegs & (1 << reg_code));
    uint32_t lower_regs = kPushedGpRegs & ((uint32_t{1} << reg_code) - 1);
    return kLastPushedGpRegisterOffset +
           base::bits::CountPopulation(lower_regs) * kSystemPointerSize;
  }

  static int GetPushedFpRegisterOffset(int reg_code) {
    DCHECK_NE(0, kPushedFpRegs & (1 << reg_code));
    uint32_t lower_regs = kPushedFpRegs & ((uint32_t{1} << reg_code) - 1);
    return kLastPushedFpRegisterOffset +
           base::bits::CountPopulation(lower_regs) * kDoubleSize;
  }
};

}  // namespace internal
}  // namespace v8

#endif  // V8_EXECUTION_RISCV_FRAME_CONSTANTS_RISCV_H_
