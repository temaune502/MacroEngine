from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.compiler import Compiler
from compiler.analyzer import StaticAnalyzer
from runtime.vm.vm import VM
import os

def test_file(file_path):
    print(f"Testing {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    
    try:
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast_tree = parser.parse()
        
        print("Analyzing AST...")
        analyzer = StaticAnalyzer(builtins=['print', 'ui', 'sleep'])
        if not analyzer.analyze(ast_tree):
            print("Static analysis failed!")
            return
            
        print("Compiling...")
        compiler = Compiler()
        chunk = compiler.compile(ast_tree)
        
        print("Running...")
        vm = VM()
        vm.globals['print'] = print
        vm.globals['ui'] = type('UI', (), {'show': lambda: print("UI Show"), 'set_text': lambda *a: print("UI Set Text:", *a)})
        vm.globals['sleep'] = lambda n: print(f"Sleep {n}")
        vm.globals['None'] = None
        vm.globals['true'] = True
        vm.globals['false'] = False
        
        vm.run(chunk, compiler.functions)
        
        if 'on_init' in compiler.functions:
            print("Calling on_init...")
            vm.call_function('on_init')
            
        if 'on_s1' in compiler.functions:
            print("Calling on_s1...")
            vm.call_function('on_s1')
            
        print("Success!")
    except Exception as e:
        from runtime.vm import VMRuntimeError
        if isinstance(e, VMRuntimeError) and e.line:
            print(f"Runtime Error: L{e.line}: {e.message}")
        else:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()



if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = r"c:\Users\temaune\Desktop\ML\examples\тести\макрос_всі_фішки.tml"
    
    if os.path.exists(path):
        test_file(path)
    else:
        print(f"File not found: {path}")
