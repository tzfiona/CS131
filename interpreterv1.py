from intbase import InterpreterBase
from brewparse import parse_program

class Interpreter(InterpreterBase):
  def __init__(self, console_output=True, inp=None, trace_output=False):
    super().__init__(console_output, inp)
  
  def run(self, program):
    ast = parse_program(program, False)
    self.variable_name_to_value = {}
    
    #main_func_node = get_main_func_node(ast)
    if ast.elem_type == "program": 
      func_def_node = ast.get("functions") 
      for i in func_def_node:
        if i.elem_type == "func":
          if i.get("name") == "main":
            main_node = i
            print("YIPPIEE its a main") ###
            self.run_func(main_node)
            break
          else:
            super().error(
              ErrorType.NAME_ERROR,
              "No main() function was found",
            )

  def run_func(self, func_node):
    print("run func starts now~") ###
    if func_node.elem_type == "func": 
      for stmt_node in func_node.get("statements"):
        self.run_statement(stmt_node)


  def run_statement(self, statement_node):
    print("run statement starts now~") ###
    

  #def do_assignment(statement_node):

  #def evaluate_expression(expression_node):

def main():
  program = """def main() {
                  var x;
                  x = 11 + 32;
                  print("The result is: ", x);
            }"""
  
  interpreter = Interpreter()
  interpreter.run(program)

if __name__ == "__main__":
  main()
  