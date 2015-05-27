import struct

class BaseWriter(object):
  def __init__(self, filename):
    self.ofile = file(filename, 'wb')
  def write_bytes(self, b):
    self.ofile.write(b)
  def write_byte(self, b):
    self.ofile.write(struct.pack('B', b))
  def write_short(self, s):
    self.ofile.write(struct.pack('H', s))
  def write_long(self, l):
    if l < 0:
      self.ofile.write(struct.pack('l', l))
    else:
      self.ofile.write(struct.pack('L', l))
  def close(self):
    self.ofile.close()

class CodeWriter(BaseWriter):
  def __init__(self, filename):
    super(CodeWriter, self).__init__(filename)
  def write_opcode(self, opcode):
    self.write_byte(opcode)
  def write_var_ref(self, ref):
    self.write_short(ref)
  def write_reg_ref(self, ref):
    self.write_short(ref)
  def write_var_size(self, size):
    self.write_short(size)
  def write_var_index(self, index):
    self.write_short(index)
  def write_type(self, thetype):
    self.write_byte(thetype)

