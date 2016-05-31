"""
A exciting CRC16 implement of qChecksum using LLVM
By ZPCCZQ
"""
from __future__ import print_function

from ctypes import CFUNCTYPE, c_char_p, c_int, c_ushort

import llvmlite.binding as llvm
from llvmlite import ir

llvm_ir = """
; ModuleID = 'crc16.c'

@wCRCTalbeAbs = constant [16 x i16] [i16 0, i16 4225, i16 8450, i16 12675, i16 16900, i16 21125, i16 25350, i16 29575, i16 -31736, i16 -27511, i16 -23286, i16 -19061, i16 -14836, i16 -10611, i16 -6386, i16 -2161], align 16

; Function Attrs: nounwind uwtable
define i16 @CRC16_2(i8* %pchMsg, i32 %wDataLen) #0 {
entry:
  %wDataLen.addr = alloca i32, align 4
  %pchMsg.addr = alloca i8*, align 8
  %wCRC = alloca i16, align 2
  %i = alloca i32, align 4
  %chChar = alloca i8, align 1
  store i32 %wDataLen, i32* %wDataLen.addr, align 4
  store i8* %pchMsg, i8** %pchMsg.addr, align 8
  store i16 -1, i16* %wCRC, align 2
  store i32 0, i32* %i, align 4
  br label %for.cond

for.cond:                                         ; preds = %for.inc, %entry
  %0 = load i32, i32* %i, align 4
  %1 = load i32, i32* %wDataLen.addr, align 4
  %cmp = icmp slt i32 %0, %1
  br i1 %cmp, label %for.body, label %for.end

for.body:                                         ; preds = %for.cond
  %2 = load i8*, i8** %pchMsg.addr, align 8
  %incdec.ptr = getelementptr inbounds i8, i8* %2, i32 1
  store i8* %incdec.ptr, i8** %pchMsg.addr, align 8
  %3 = load i8, i8* %2, align 1
  store i8 %3, i8* %chChar, align 1
  %4 = load i8, i8* %chChar, align 1
  %conv = zext i8 %4 to i32
  %5 = load i16, i16* %wCRC, align 2
  %conv1 = zext i16 %5 to i32
  %xor = xor i32 %conv, %conv1
  %and = and i32 %xor, 15
  %idxprom = sext i32 %and to i64
  %arrayidx = getelementptr inbounds [16 x i16], [16 x i16]* @wCRCTalbeAbs, i64 0, i64 %idxprom
  %6 = load i16, i16* %arrayidx, align 2
  %conv2 = zext i16 %6 to i32
  %7 = load i16, i16* %wCRC, align 2
  %conv3 = zext i16 %7 to i32
  %shr = ashr i32 %conv3, 4
  %xor4 = xor i32 %conv2, %shr
  %conv5 = trunc i32 %xor4 to i16
  store i16 %conv5, i16* %wCRC, align 2
  %8 = load i8, i8* %chChar, align 1
  %conv6 = zext i8 %8 to i32
  %shr7 = ashr i32 %conv6, 4
  %9 = load i16, i16* %wCRC, align 2
  %conv8 = zext i16 %9 to i32
  %xor9 = xor i32 %shr7, %conv8
  %and10 = and i32 %xor9, 15
  %idxprom11 = sext i32 %and10 to i64
  %arrayidx12 = getelementptr inbounds [16 x i16], [16 x i16]* @wCRCTalbeAbs, i64 0, i64 %idxprom11
  %10 = load i16, i16* %arrayidx12, align 2
  %conv13 = zext i16 %10 to i32
  %11 = load i16, i16* %wCRC, align 2
  %conv14 = zext i16 %11 to i32
  %shr15 = ashr i32 %conv14, 4
  %xor16 = xor i32 %conv13, %shr15
  %conv17 = trunc i32 %xor16 to i16
  store i16 %conv17, i16* %wCRC, align 2
  br label %for.inc

for.inc:                                          ; preds = %for.body
  %12 = load i32, i32* %i, align 4
  %inc = add nsw i32 %12, 1
  store i32 %inc, i32* %i, align 4
  br label %for.cond

for.end:                                          ; preds = %for.cond
  %13 = load i16, i16* %wCRC, align 2
  %conv18 = zext i16 %13 to i32
  %neg = xor i32 %conv18, -1
  %conv19 = trunc i32 %neg to i16
  ret i16 %conv19
}
"""

# All these initializations are required for code generation!
llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()  # yes, even this one


def create_execution_engine():
    """
    Create an ExecutionEngine suitable for JIT code generation on
    the host CPU.  The engine is reusable for an arbitrary number of
    modules.
    """
    # Create a target machine representing the host
    target = llvm.Target.from_default_triple()
    target_machine = target.create_target_machine()
    # And an execution engine with an empty backing module
    backing_mod = llvm.parse_assembly("")
    engine = llvm.create_mcjit_compiler(backing_mod, target_machine)
    return engine


def compile_ir(engine, llvm_ir):
    """
    Compile the LLVM IR string with the given engine.
    The compiled module object is returned.
    """
    # Create a LLVM module object from the IR
    mod = llvm.parse_assembly(llvm_ir)
    mod.verify()
    # Optimize the module
    pmb = llvm.create_pass_manager_builder()
    pmb.opt_level = 2
    pm = llvm.create_module_pass_manager()
    pmb.populate(pm)
    pm.run(mod)
    # Now add the module and make sure it is ready for execution
    engine.add_module(mod)
    engine.finalize_object()
    return mod


engine = create_execution_engine()
mod = compile_ir(engine, llvm_ir)

# Look up the function pointer (a Python int)
func_ptr = engine.get_function_address("CRC16_2")

# Run the function via ctypes
cfunc = CFUNCTYPE(c_ushort, c_char_p, c_int)(func_ptr)
def crc16(data):
  return cfunc(data, len(data))
