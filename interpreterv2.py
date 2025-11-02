from intbase import InterpreterBase, ErrorType
from brewparse import parse_program
from intbase import ErrorType

generate_image = False


class Environment:
    def __init__(self):
        self.env = {}

    # define new variable at function scope
    def fdef(self, varname):
        if self.exists(varname):
            return False
        self.env[varname] = None
        return True

    def exists(self, varname):
        return varname in self.env

    def get(self, varname):
        if varname in self.env:
            return self.env[varname]
        return None

    def set(self, varname, value):
        if not self.exists(varname):
            return False
        self.env[varname] = value
        return True


class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)

        self.funcs = {}  # {name:element,}
        self.env = Environment()
        self.ops = {"-", "+"}

    def run(self, program):
        ast = parse_program(program, generate_image)

        for func in ast.get("functions"):
            self.funcs[func.get("name")] = func

        if "main" not in self.funcs:
            super().error(ErrorType.NAME_ERROR, "main function not found")

        for statement in self.funcs["main"].get("statements"): # @func def node here
            kind = statement.elem_type

            if kind == self.VAR_DEF_NODE:
                self.__run_vardef(statement)
            elif kind == "=":
                self.__run_assign(statement)
            elif kind == self.FCALL_NODE:
                self.__run_fcall(statement)
            elif kind == self.IF_NODE:
                #print("YAYYYY its IF") ################
                self.__run_if(statement)
            elif kind == self.WHILE_NODE:
                #print("YAYYYY its WHILE") ################
                self.__run_while(statement)
            elif kind == self.RETURN_NODE:
                print("YAYYYY its RETURN") ################
                #self.__run_return(statement)
            else:
                super().error(ErrorType.NAME_ERROR, "unknown kind detected") #idk if this we required

    def __run_vardef(self, statement):
        name = statement.get("name")

        if not self.env.fdef(name):
            super().error(ErrorType.NAME_ERROR, "variable already defined")

    def __run_assign(self, statement):
        name = statement.get("var")

        value = self.__eval_expr(statement.get("expression"))
        if not self.env.set(name, value):
            super().error(ErrorType.NAME_ERROR, "variable not defined")

    def __run_fcall(self, statement):
        fcall_name, args = statement.get("name"), statement.get("args")

        if fcall_name == "inputi":
            if len(args) > 1:
                super().error(ErrorType.NAME_ERROR, "too many arguments for inputi")

            if args:
                super().output(str(self.__eval_expr(args[0])))

            return int(super().get_input())

        if fcall_name == "print":
            out = ""

            for arg in args:
                out += str(self.__eval_expr(arg))

            super().output(out)

            return 0  # undefined behavior
        
        if fcall_name == "inputs":
            if len(args) > 1:
                super().error(ErrorType.NAME_ERROR, "too many arguments for inputs")

            if args:
                super().output(str(self.__eval_expr(args[0])))

            return str(super().get_input())





        if fcall_name in self.funcs:
            #print(fcall_name,"FUNC IS IN DICT") ############################
            funcdef = self.funcs[fcall_name]
            #print(funcdef, "CHECKKKKK") ############################

            prev_env = self.env
            self.env = Environment() #create new env since we're going into a new func

            for statement in funcdef.get("statements"):
              kind = statement.elem_type
              #print(statement, "-IS-", kind, "WOWOOWWOWWWO") ############################

              if kind == self.VAR_DEF_NODE:
                self.__run_vardef(statement)
              elif kind == "=":
                self.__run_assign(statement)
              elif kind == self.FCALL_NODE:
                returned = self.__run_fcall(statement)
              elif kind == "return":
                returned = self.__eval_expr(statement.get("expression"))
                break
              
              self.env = prev_env
              return returned
        
        super().error(
                    ErrorType.NAME_ERROR,
                    f"Function {fcall_name} was not found",
                        )
        #super().error(ErrorType.NAME_ERROR, "unknown function") given error message

    def __eval_expr(self, expr):
        kind = expr.elem_type

        if kind == self.INT_NODE or kind == self.STRING_NODE:
            return expr.get("val")
        elif kind == self.BOOL_NODE: #~~~~~~~~~~~~~~
            val = expr.get("val")
            if isinstance(val, bool):
                return val
        elif kind == "NIL_NODE": #~~~~~~~~~~~~~~
            return None

        elif kind == self.QUALIFIED_NAME_NODE:
            var_name = expr.get("name")

            value = self.env.get(var_name)
            if value is None:
                super().error(ErrorType.NAME_ERROR, "variable not defined")
            return value
        
        elif kind in {"+", "-", "*", "/", "==", "!=", "<", "<=", ">", ">=", "&&", "||"}: #~~~~~~~~~~~~~~~~~~~~
            op1 = self.__eval_expr(expr.get("op1"))
            op2 = self.__eval_expr(expr.get("op2"))

            if kind == "==":
                if op1 is None and op2 is None:
                    return True
                return op1 == op2
            if kind == "!=":
                if op1 is None and op2 is None:
                    return False
                return op1 != op2
            
            if isinstance(op1, int) and isinstance(op2, int):
                if kind == "+":
                    return op1 + op2
                elif kind == "-":
                    return op1 - op2
                elif kind == "*":
                    return op1 * op2
                elif kind == "/":
                    return op1 // op2
                elif kind == "<":
                    return op1 < op2
                elif kind == ">":
                    return op1 > op2
                elif kind == "<=":
                    return op1 <= op2
                elif kind == ">=":
                    return op1 >= op2
            else:
                super().error(ErrorType.TYPE_ERROR, "cannot compare values of diff types")
            
            if isinstance(op1, bool) and isinstance(op2, bool):
                if kind == "&&":
                    return op1 and op2
                elif kind == "||":
                    return op1 or op2
            else:
                print("we need bool") ################################
                
        elif kind == "neg": #~~~~~~~~~~~~~~~~~~~~
            op1 = self.__eval_expr(expr.get("op1"))
            if isinstance(op1, int):
                return -op1
            else:
                print("we need int") ################################

        elif kind == "!": #~~~~~~~~~~~~~~~~~~~~
            op1 = self.__eval_expr(expr.get("op1"))
            if isinstance(op1, bool):
                return not op1
            else:
                super().error(ErrorType.TYPE_ERROR, "cannot use on non-boolean types")


        elif kind == self.FCALL_NODE:
            return self.__run_fcall(expr)

        elif kind in self.ops:
            l, r = self.__eval_expr(expr.get("op1")), self.__eval_expr(expr.get("op2"))

            if isinstance(l, str) or isinstance(r, str):
                super().error(
                    ErrorType.TYPE_ERROR, "invalid operand types for arithmetic"
                )

            if kind == "-":
                return l - r

            elif kind == "+":
                return l + r

    def __run_stmts(self, statements): #~~~~~~~~~~~~~~~~~~~~
        for stmts in statements:
            kind = stmts.elem_type

            if kind == self.VAR_DEF_NODE:
                self.__run_vardef(stmts)
            elif kind == "=":
                self.__run_assign(stmts)
            elif kind == self.FCALL_NODE:
                self.__run_fcall(stmts)
            elif kind == self.IF_NODE:
                self.__run_if(stmts)
            elif kind == self.WHILE_NODE:
                pass  # add later
            elif kind == self.RETURN_NODE:
                pass  # add later
            else:
                super().error(ErrorType.NAME_ERROR, "unknown statement type")

    def __run_if(self, statement): #~~~~~~~~~~~~~~~~~~~
        # Expression must be boolean, else ERROR
        condition = statement.get("condition")
        #print(condition, ": this is the condition") ########################
        condition = self.__eval_expr(condition) 
        #print(condition, ": this is the condition type") ########################
        
        if not isinstance(condition, bool):
            super().error(
                ErrorType.TYPE_ERROR, "If condition is not a boolean. Must be a boolean.")
        
        if condition:
            self.__run_stmts(statement.get("statements"))
        elif statement.get("else_statements"):
            self.__run_stmts(statement.get("else_statements"))


    def __run_while(self, statement): #~~~~~~~~~~~~~~~~~~~
        # Expression must be boolean, else ERROR
        while True:
            condition = statement.get("condition")
            #print(condition, ": this is the condition") ########################
            condition = self.__eval_expr(condition) 
            #print(condition, ": this is the condition type") ########################

            if not isinstance(condition, bool):
                super().error(
                    ErrorType.TYPE_ERROR, "While condition is not a boolean. Must be a boolean.")
                
            if condition:
                self.__run_stmts(statement.get("statements"))
            else:
                break


    #def __run_return(self, statement): #~~~~~~~~~~~~~~~~~~~
        # Must exit function
        # If there is a statement to return, must return by value





def main():
    '''
    program = """
                    def hi() {
                      print("hii");
                    }

                    def main() {
                      hi();
                    }
    """
  
    interpreter = Interpreter()
    interpreter.run(program)
    '''

    interpreter = Interpreter()

    # The code below is meant to help you test your interpreter on your own Brewin programs.
    # To run this main function, create a file test.br in the same directory and put Brewin code in it.
    with open("./test.br", "r") as f:
        program = f.read()

    global generate_image
    generate_image = True
    interpreter.run(program)


if __name__ == "__main__":
    main()