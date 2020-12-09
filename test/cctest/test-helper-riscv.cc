// Copyright 2017 the V8 project authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "test/cctest/test-helper-riscv.h"

#include "src/codegen/macro-assembler.h"
#include "src/execution/isolate-inl.h"
#include "src/init/v8.h"
#include "test/cctest/cctest.h"

namespace v8 {
namespace internal {

int64_t GenAndRunTest(Func test_generator) {
  Isolate* isolate = CcTest::i_isolate();
  HandleScope scope(isolate);

  MacroAssembler assm(isolate, v8::internal::CodeObjectRequired::kYes);
  test_generator(assm);
  assm.jr(ra);

  CodeDesc desc;
  assm.GetCode(isolate, &desc);
  Handle<Code> code =
      Factory::CodeBuilder(isolate, desc, CodeKind::FOR_TESTING).Build();
  auto f = GeneratedCode<int64_t()>::FromCode(*code);
  return f.Call();
}

Handle<Code> AssembleCodeImpl(Func assemble) {
  Isolate* isolate = CcTest::i_isolate();
  MacroAssembler assm(isolate, CodeObjectRequired::kYes);

  assemble(assm);
  assm.jr(ra);

  CodeDesc desc;
  assm.GetCode(isolate, &desc);
  Handle<Code> code =
      Factory::CodeBuilder(isolate, desc, CodeKind::FOR_TESTING).Build();
  if (FLAG_print_code) {
    code->Print();
  }
  return code;
}

}  // namespace internal
}  // namespace v8