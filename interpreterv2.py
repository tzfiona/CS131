from intbase import InterpreterBase, ErrorType
from brewparse import parse_program
from intbase import ErrorType

generate_image = False

class Environment:
    def __init__(self):
        self.env = [{}]

    def fdef(self, varname):
        if self.exists(varname):
            return False
        self.env[-1][varname] = None
        return True

    def exists(self, varname):
        for i in reversed(self.env):
            if varname in i:
                return True
        return False

    def get(self, varname):
        for i in reversed(self.env):
            if varname in i:
                return i[varname]
        return None
    
    def set(self, varname, value):
        for i in reversed(self.env):
            if varname in i:
                i[varname] = value
                return True
        return False

    def pop(self):
        self.env.pop()
    def push(self):
        self.env.append({})


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
                self.__run_if(statement)
            elif kind == self.WHILE_NODE:
                self.__run_while(statement)
            elif kind == self.RETURN_NODE:
                self.__run_return(statement)
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
            returned = None
            #print(fcall_name,"FUNC IS IN DICT") ############################
            funcdef = self.funcs[fcall_name]
            #print(funcdef, "CHECKKKKK") ############################
            parameter = funcdef.get("args")

            if len(args) != len(parameter):
                super().error(ErrorType.NAME_ERROR, f"incorrect # of arguements")

            self.env.push()

            for x, y in zip(parameter, args):
                val = self.__eval_expr(y)
                self.env.fdef(x.get("name"))
                self.env.set(x.get("name"), val)
 
            for statement in funcdef.get("statements"):
                kind = statement.elem_type
                #print(statement, "-IS-", kind, "WOWOOWWOWWWO") ############################

                if kind == self.VAR_DEF_NODE:
                    self.__run_vardef(statement)
                elif kind == "=":
                    self.__run_assign(statement)
                elif kind == self.FCALL_NODE:
                    self.__run_fcall(statement)
                elif kind == self.IF_NODE:
                    returned = self.__run_if(statement)
                    if returned is not None:
                        break
                elif kind == self.WHILE_NODE:
                    returned = self.__run_while(statement)
                    if returned is not None:
                        break
                elif kind == self.RETURN_NODE:
                    returned = self.__eval_expr(statement.get("expression"))
                    break

            self.env.pop()
            return returned

        super().error(ErrorType.NAME_ERROR, "unknown function") 

    def __eval_expr(self, expr):
        kind = expr.elem_type

        if kind == self.INT_NODE or kind == self.STRING_NODE:
            return expr.get("val")
        elif kind == self.BOOL_NODE: #~~~~~~~~~~~~~~
            val = expr.get("val")
            if isinstance(val, bool):
                return val
        elif kind == self.NIL_NODE: #~~~~~~~~~~~~~~
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
                if type(op1) != type(op2):
                    return False
                return op1 == op2
            if kind == "!=":
                if op1 is None and op2 is None:
                    return False
                if type(op1) != type(op2):
                    return True
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
                    super().error(ErrorType.TYPE_ERROR, "cannot use int types")
            else:
                super().error(ErrorType.TYPE_ERROR, "cannot compare values of diff types")

            if isinstance(op1, str) and isinstance(op2, str):
                if kind == "+":
                    return op1 + op2
                else:
                    super().error(ErrorType.TYPE_ERROR, "cannot use str types")
            else:
                    super().error(ErrorType.TYPE_ERROR, "cannot use str types")
            
            if isinstance(op1, bool) and isinstance(op2, bool):
                if kind == "&&":
                    return op1 and op2
                elif kind == "||":
                    return op1 or op2
                else:
                    super().error(ErrorType.TYPE_ERROR, "cannot use on non-boolean types")
            else:
                    super().error(ErrorType.TYPE_ERROR, "cannot use bool types")
                
        elif kind == "neg": #~~~~~~~~~~~~~~~~~~~~
            op1 = self.__eval_expr(expr.get("op1"))
            if isinstance(op1, int):
                return -op1
            else:
                super().error(ErrorType.TYPE_ERROR, "cannot use on non-int types")
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
                returned = self.__run_if(stmts)
                if returned is not None:
                    return returned
            elif kind == self.WHILE_NODE:
                returned = self.__run_while(stmts)
                if returned is not None:
                    return returned
            elif kind == self.RETURN_NODE:
                return self.__run_return(stmts)
            else:
                super().error(ErrorType.NAME_ERROR, "unknown statement type")
        return None

    def __run_if(self, statement): #~~~~~~~~~~~~~~~~~~~
        condition = statement.get("condition")
        condition = self.__eval_expr(condition) 
        
        if not isinstance(condition, bool):
            super().error(
                ErrorType.TYPE_ERROR, "If condition is not a boolean. Must be a boolean.")
        
        if condition:
            final = self.__run_stmts(statement.get("statements")) 
            if final is None:
                pass
            elif final is not None:
                return final
        elif statement.get("else_statements"):
            final = self.__run_stmts(statement.get("else_statements"))
            if final is None:
                pass
            elif final is not None:
                return final
        return None

    def __run_while(self, statement): #~~~~~~~~~~~~~~~~~~~
        while True:
            condition = statement.get("condition")
            condition = self.__eval_expr(condition) 

            if not isinstance(condition, bool):
                super().error(
                    ErrorType.TYPE_ERROR, "While condition is not a boolean. Must be a boolean.")
                
            if condition:
                final = self.__run_stmts(statement.get("statements"))
                if final is None:
                    pass
                elif final is not None:
                    return final
            else:
                break
        return None

    def __run_return(self, statement): #~~~~~~~~~~~~~~~~~~~
        if statement.get("expression"):
            return self.__eval_expr(statement.get("expression"))
        return None


def main():
    interpreter = Interpreter()
    with open("./test.br", "r") as f:
        program = f.read()

    global generate_image
    generate_image = True
    interpreter.run(program)


if __name__ == "__main__":
    main()