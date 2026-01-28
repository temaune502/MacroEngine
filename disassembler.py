import pickle
import os
import sys
from compiler.opcodes import OpCode
from compiler.base import Chunk, FunctionObject

class Disassembler:
    def __init__(self, output=sys.stdout):
        self.output = output

    def disassemble(self, chunk, functions=None, name="Main"):
        print(f"=== Disassembly: {name} ===", file=self.output)
        if not chunk:
            print("Empty chunk.", file=self.output)
            return

        ip = 0
        while ip < len(chunk.code):
            self.disassemble_instruction(chunk, ip)
            ip += 1
        
        if functions:
            for func_name, func_obj in functions.items():
                print(file=self.output)
                self.disassemble(func_obj.chunk, None, f"Function {func_name}")

    def disassemble_instruction(self, chunk, ip):
        op, arg = chunk.code[ip]
        op_name = op.name.ljust(15)
        
        line_prefix = f"{ip:04d}  "
        
        if op in (OpCode.PUSH_CONST, OpCode.DEFINE_GLOBAL, OpCode.GET_GLOBAL, OpCode.SET_GLOBAL):
            const_val = chunk.constants[arg]
            print(f"{line_prefix}{op_name} {arg:04d} ({const_val})", file=self.output)
        
        elif op in (OpCode.JUMP, OpCode.JUMP_IF_FALSE, OpCode.LOOP):
            print(f"{line_prefix}{op_name} {arg:04d} (target: {arg:04d})", file=self.output)
            
        elif op in (OpCode.SET_LOCAL, OpCode.GET_LOCAL):
            print(f"{line_prefix}{op_name} {arg:04d}", file=self.output)
            
        elif op == OpCode.CALL:
            print(f"{line_prefix}{op_name} {arg:04d} (args)", file=self.output)
            
        elif op in (OpCode.GET_ATTR, OpCode.SET_ATTR):
            const_val = chunk.constants[arg]
            print(f"{line_prefix}{op_name} {arg:04d} (attr: {const_val})", file=self.output)
            
        else:
            if arg is not None:
                print(f"{line_prefix}{op_name} {arg:04d}", file=self.output)
            else:
                print(f"{line_prefix}{op_name}", file=self.output)

def main():
    # Usage: python disassembler.py [cache_file] [output_file]
    cache_file = None
    output_file = None

    if len(sys.argv) >= 2:
        cache_file = sys.argv[1]
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]

    if not cache_file:
        # Try to find the latest cache file in .cache
        cache_dir = ".cache"
        if not os.path.exists(cache_dir):
            print("No cache directory found. Run main.py first.")
            return
        
        files = [os.path.join(cache_dir, f) for f in os.listdir(cache_dir) if f.endswith(".bin")]
        if not files:
            print("No cache files found. Run main.py first.")
            return
        
        # Get newest file
        cache_file = max(files, key=os.path.getmtime)
        print(f"Loading latest cache: {cache_file}")

    try:
        with open(cache_file, "rb") as f:
            data = pickle.load(f)
            chunk = data.get('chunk')
            functions = data.get('functions')
            
            if output_file:
                with open(output_file, "w", encoding="utf-8") as out:
                    dis = Disassembler(output=out)
                    dis.disassemble(chunk, functions)
                print(f"Disassembly saved to: {output_file}")
            else:
                dis = Disassembler()
                dis.disassemble(chunk, functions)
    except Exception as e:
        print(f"Error loading cache file: {e}")

if __name__ == "__main__":
    main()
