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
  // FIXME(RISCV): How is it decided which registers should be pushed?
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
  // FIXME(RISCV): How is it decided which registers should be pushed?
  static constexpr uint32_t kPushedFpRegs = 1 << 8 |   // fs0
                                            1 << 9 |   // fs1
                                            1 << 18 |  // fs2
                                            1 << 19 |  // fs3
                                            1 << 20 |  // fs4
                                            1 << 21 |  // fs5
                                            1 << 22 |  // fs6
                                            1 << 23 |  // fs7
                                            1 << 24 |  // fs8
                                            1 << 25 |  // fs9
                                            1 << 26 |  // fs10
                                            1 << 27;   // fs11

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
