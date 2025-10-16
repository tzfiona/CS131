from intbase import InterpreterBase
from brewparse import parse_program


class Interpreter(InterpreterBase):
  def __init__(self, console_output=True, inp=None, trace_output=False):
    super().__init__(console_output, inp)
  

  def run(self, program):
    ast = parse_program(program, False)
    self.variable_name_to_value = {}
    if ast.elem_type == "program": 
      func_def_node = ast.get("functions") 
      for i in func_def_node:
        if i.elem_type == "func":
          if i.get("name") == "main":
            main_node = i
            print("YIPPIEE its a main~~~~~~~~~~~~~~~~~~~~~~~") ###
            self.run_func(main_node)
          else:
            super().error(
              ErrorType.NAME_ERROR,
              "No main() function was found",
            )


  def run_func(self, func_node):
    print("run func starts now~~~~~~~~~~~~~~~~~~~~~~~") ###
    if func_node.elem_type == "func": 
      for stmt_node in func_node.get("statements"):
        self.run_statement(stmt_node)


  def run_statement(self, statement_node):
    print("run statement starts now~~~~~~~~~~~~~~~~~~~~~~~") ###

    if statement_node.elem_type == "vardef": 
      for i in statement_node.get("name"):
        self.variable_name_to_value[i] = None
        print("saves var", i, "to dict") ###

    elif statement_node.elem_type == "=": 
      a = statement_node.get("var")
      exp_node = statement_node.get("expression")
      b = self.do_assignment(statement_node)
      self.variable_name_to_value[a] = b
      print("saves", b, "to", a) ###

    elif statement_node.elem_type == "fcall": #FIXXXXXXX
      if statement_node.get("name") == "print":
        print_statement = []
        for k in statement_node.get("args"):
          statement_item = self.evaluate_expression(k)
          print_statement.append(statement_item)
        print(*print_statement)     


  def do_assignment(self, statement_node):
    print("do assigment starting now~~~~~~~~~~~~~~~~~~~~~~~") ###
    target_var_name = statement_node.get("var")
    if target_var_name not in self.variable_name_to_value:
      print("Undefined variable:", target_var_name)
    source_node = statement_node.get("expression")
    resulting_value = self.evaluate_expression(source_node)
    self.variable_name_to_value[target_var_name] = resulting_value
    return resulting_value


  def evaluate_expression(self, expression_node):
    print("eval expression starting now~~~~~~~~~~~~~~~~~~~~~~~") ###
    if (expression_node.elem_type == "int") or (expression_node.elem_type == "string"):
      return expression_node.get("val")
    
    elif expression_node.elem_type == "qname":
      name = expression_node.get("name")
      return self.variable_name_to_value.get(name)
    
    elif (expression_node.elem_type == "+") or (expression_node.elem_type == "-"): 
      op1 = self.evaluate_expression(expression_node.get("op1")) #must use self.evaluate_expression to recursivly find the value instead of just the child node
      op2 = self.evaluate_expression(expression_node.get("op2"))
      print("op1 and op2:", op1, op2) ###
      if expression_node.elem_type == "+":
        print("op1 + op2 =", op1 + op2) ###
        return op1 + op2
      elif expression_node.elem_type == "-":
        print("op1 - op2 =", op1 - op2) ###
        return op1 - op2


def main():
  program = """def main() {
                  var x;
                  x = 11 + 32;
                  print("The result is:", x);
            }"""
  
  interpreter = Interpreter()
  interpreter.run(program)

if __name__ == "__main__":
  main()
  