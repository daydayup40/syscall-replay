#
#
# Instruction set:
# 
# N: 0..6
# argi = @vi | <immediate>

# Declare variable type (do we need this?)
# No, we don't.
# Maybe for typechecking?
# Yes, we do.
# @v1 : uint64
# @v2 : str
# @v3 : 10

# Variable assignment:
# @v1 = 0x0
# @v2 = "Hello world\n"   # auto-allocate the necessary memory
# @v3 = 0xff 0x11 0x10  # the rest inited with zeroes
# Each variable can only be assigned once (to ease bounds checking).

# Register assignment:
# @r1 = 0x0     # register size is always 8 bytes
# @r1 = @r2     # you can assign registers to registers
# syscall instruction always implicitly assigns to r0

# Copy variable to Vi starting at index Ii from Vj starting at inde Ij, size M
# copy(@v1[10], @v2[2], 10)
# copy(@r1, @r2)    # @r2 = @r1
# copy(@v1[10], @r1)

# Call a syscall:
# syscallN(S, arg1, arg2, .., argN)
# syscall0(10)  # No idea what's that
# syscall2(64, @v2, 10)

# Check that v0 is not -1. If it is, bail out.
# check_retval

from writer import CodeWriter

import struct

class CompilerException(Exception):
  pass

class Argument(object):
  def __init__(self):
    self.arg_type = 0x0
  def emit_arg(self, where):
    where.write_type(self.arg_type)

class Immediate(Argument):
  def __init__(self, value):
    super(Immediate, self).__init__()
    self.value = value
    self.arg_type = 0x01
  def emit_arg(self, where):
    super(Immediate, self).emit_arg(where)
    where.write_long(self.value)

def make_byte_list(value):
  if type(value) == int:
    if value >= 0:
      return struct.pack("L", value)
    else:
      return struct.pack("l", value)
  if type(value) == str:
    fmt = '%ds' % (len(value) + 1)
    return struct.pack(fmt, value)
    

class Variable(Argument):
  VARIABLES = {}
  @staticmethod
  def create(number, value):
    if number in Variable.VARIABLES:
      return Variable.VARIABLES[number]
    else:
      return Variable(number, value)
  def __init__(self, number, value):
    super(Variable, self).__init__()
    if type(value) is not list:
      value = make_byte_list(value)
    self.size = len(value)
    self.value = value
    self.number = number
    self.arg_type = 0x0f
    Variable.VARIABLES[number] = self
  def check_size(self, size):
    if self.size < size:
      raise CompilerException()
  def emit_ref(self, where):
    where.write_var_ref(self.number)
  def emit_size(self, where):
    where.write_var_size(self.size)
  def emit_index(self, where, index):
    self.check_size(index)
    where.write_var_index(index)
  def emit_data(self, where):
    where.write_bytes(self.value)
  def emit_arg(self, where):
    super(Variable, self).emit_arg(where)
    self.emit_ref(where)

class Register(Argument):
  REGISTERS = {}
  def __init__(self, number):
    super(Register, self).__init__()
    self.number = number
    self.arg_type = 0x0e
    Register.REGISTERS[number] = self
  def emit_ref(self, where):
    where.write_reg_ref(self.number)
  def emit_arg(self, where):
    super(Register, self).emit_arg(where)
    self.emit_ref(where)

class Inst(object):
  def __init__(self):
    self.opcode = 0x0;
  def emit(self, where):
    where.write_opcode(self.opcode)

class InitInst(Inst):
  def __init__(self, var):
    super(InitInst, self).__init__()
    self.opcode = 0x11
    self.var = var
  def emit(self, where):
    super(InitInst, self).emit(where)
    self.var.emit_ref(where)
    self.var.emit_size(where)
    self.var.emit_data(where)

class AssignInst(Inst):
  def __init__(self, lvalue, rvalue):
    super(AssignInst, self).__init__()
    self.opcode = 0xa5
    self.lvalue, self.rvalue = lvalue, rvalue
  def emit(self, where):
    super(AssignInst, self).emit(where)
    self.lvalue.emit_arg(where)
    self.rvalue.emit_arg(where)
  

class CopyInst(Inst):
  def __init__(self, dest, dest_off, src, src_off, size):
    super(CopyInst, self).__init__()
    self.opcode = 0xc0
    self.dest, self.dest_off, self.src, self.src_off, size = dest, dest_off, src, src_off, size
  def emit(self, where):
    super(CopyInst, self).emit(where)
    dest.emit_arg(where)
    dest.emit_index(where, index)
    src.emit_arg(where)
    src.check_size(where, index + size)
    src.emit_index(where, size)

class SyscallInst(Inst):
  def __init__(self, nargs, syscall, args):
    super(SyscallInst, self).__init__()
    self.opcode = 0x5c
    self.nargs, self.syscall, self.args = nargs, syscall, args
  def emit(self, where):
    super(SyscallInst, self).emit(where)
    where.write_byte(self.nargs)
    where.write_short(self.syscall)
    for arg in self.args:
      arg.emit_arg(where)


def test_codegen():
  s = "Hello world\n"
  v1 = Variable.create(1, s)
  fd = Immediate(2)
  imm = Immediate(len(s) + 1)
  #v2 = Variable.create(2, len(s) + 1)
  i1 = InitInst(v1)
  #i2 = InitInst(v2)
  #i3 = InitInst(v3)
  call1 = SyscallInst(3, 1, [fd, v1, imm])
  reg0 = Register(0)
  reg1 = Register(1)
  reg2 = Register(2)
  assign1 = AssignInst(reg1, fd)
  assign2 = AssignInst(reg2, reg0)
  call2 = SyscallInst(3, 1, [reg1, v1, reg2])
  writer = CodeWriter('write.ssc')
  for i in [i1, call1, assign1, assign2, call2]:
    i.emit(writer)
  writer.close()

if __name__ == "__main__":
  test_codegen()
