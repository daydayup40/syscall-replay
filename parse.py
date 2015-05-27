SUPPORTED_SYSCALLS = [
  'open', 'close', 'read', 'write',
]

class Atom:
  ATOM_TYPES = ['int', 'string']
  def __init__(self, repr_string):
    if 

def get_atom(arg):
  if isinstance
  

class Syscall:
  def __init__(self, name, args):
    self.name = name
    self.args = []
    for arg in args:
      arg = get_atom(arg)
      self.args.append(arg)
      if arg.is_interesting:
        self.is_interesting = True
