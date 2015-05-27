#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

typedef unsigned long long u64;
typedef unsigned short u16;
typedef unsigned char u8;

// Both variables and registers.
#define kNumVariables 1024
void *g_variables[kNumVariables];
u64 g_registers[kNumVariables];
u8 *g_program = NULL;
u8 *g_pc = NULL;
int g_program_size = 0;
#ifndef DEBUG
#define DEBUG 1
#endif

void interpretation_error(char *message) {
  printf("Error at byte %d (%02X): %s\n", g_pc - g_program, (u8)*g_pc, message);
  exit(1);
}

void generic_error(char *message) {
  printf("Generic error: %s\n", message);
  exit(1);
}

void read_program(char *fname) {
  FILE *f = fopen(fname, "rb");
  if (!f) {
    generic_error("error opening file");
  }
  fseek(f, 0L, SEEK_END);
  g_program_size = ftell(f);
  fseek(f, 0L, SEEK_SET);
  if (g_program) free(g_program);
  g_program = (u8 *)malloc(g_program_size);
  fread(g_program, 1, g_program_size, f);
  fclose(f);
  if (DEBUG) printf("Read %d bytes from %s\n", g_program_size, fname);
}


u8 *advance(int size) {
  u8 *result = g_pc;
  if (DEBUG > 1) printf("g_pc: %p, g_program: %p\n", g_pc, g_program);
  if (DEBUG > 1) printf("advancing for %d bytes\n", size);
  if ((g_pc - g_program + size) <= g_program_size) {
    g_pc += size;
    return result;
  } else {
    interpretation_error("program truncated");
  }
}


u64 read_u64() {
  u64 res = *(u64 *)g_pc;
  advance(sizeof(u64));
  return res;
}

u16 read_short() {
  u16 res = *(u16*)g_pc;
  advance(sizeof(u16));
  return res;
}

u8 read_byte() {
  u8 res = *g_pc;
  advance(sizeof(u8));
  return res;
}

void check_var_id(u16 var) {
  if (var >= kNumVariables) {
    interpretation_error("variable number out of bounds");
  }
}

void check_reg_id(u16 reg) {
  if (reg >= kNumVariables) {
    interpretation_error("register number out of bounds");
  }
}

void read_arg(u64 *where) {
  u8 type = read_byte();
  u16 var;
  switch (type) {
    case 0x01:  // immediate 64-bit value
      *(u64 *)where = read_u64();
      break;
    case 0x0e:  // register
      var = read_short();
      check_reg_id(var);
      *where = g_registers[var];
      break;
    case 0x0f:  // variable
      var = read_short();
      check_var_id(var);
      *where = (u64)g_variables[var];
      break;
    default:
      interpretation_error("incorrect argument type");
  }
}

void interpret_initinst() {
  u16 var = read_short();
  u16 size = read_short();
  check_var_id(var);
  if (g_variables[var]) {
    interpretation_error("double initialization");
  } else {
    g_variables[var] = malloc(size);
    u8 *old_pc = advance(size);
    memcpy(g_variables[var], old_pc, size);
    //advance(size);
  }
  if (DEBUG) printf("V%d : %d\n", var, size);
}

void interpret_copyinst() {
  interpretation_error("unimplemented interpret_copyinst");
}

void call_syscall(int unused_nargs, int nr_syscall, u64 args[6]) {
  if (DEBUG) {
    printf("syscall(%d, %p, %p, %p, %p, %p, %p)\n",
           nr_syscall, args[0], args[1], args[2], args[3], args[4], args[5]);
  }
  int result = (u64)syscall(nr_syscall,
                       args[0], args[1], args[2], args[3], args[4], args[5]);
  g_registers[0] = result;
  if (DEBUG) printf("syscall returned %d\n", result);
}

void interpret_syscallinst() {
  u8 nargs = read_byte();
  short nr_syscall = read_short();
  if (DEBUG) printf("syscall %d with %d arguments\n", nr_syscall, nargs);
  int i;
  u64 args[6];
  if (nargs > 6) {
    interpretation_error("too many syscall args");
  }
  for (i = 0; i < nargs; i++) {
    read_arg(&(args[i]));
    if (DEBUG) printf("args[%d] = %p\n", i, args[i]);
  }
  call_syscall(nargs, nr_syscall, args);
}

void interpret_assigninst() {
  u8 type = read_byte();
  if (type != 0x0e) {
    interpretation_error("lvalue is not a register");
  }
  u16 reg = read_short();
  check_reg_id(reg);
  if (DEBUG) printf("assigning to R%d: ", reg);
  read_arg(&(g_registers[reg]));
  if (DEBUG) printf("%d\n", g_registers[reg]);
}

void interpret_program() {
  g_pc = g_program;
  while (g_pc - g_program < g_program_size) {
    u8 opcode = read_byte();
    switch(opcode) {
      case 0x11:
        interpret_initinst();
        break;
      case 0xc0:
        interpret_copyinst();
        break;
      case 0xa5:
        interpret_assigninst();
        break;
      case 0x5c:
        interpret_syscallinst();
        break;
      default:
        interpretation_error("incorrect opcode");
    }
  }
}

int main(int argc, char **argv) {
  char default_filename[] = "write.ssc";
  char *filename = default_filename;
  if (argc > 1) {
    filename = argv[1];
  }
  read_program(filename);
  interpret_program();
  
  return 0;
}
