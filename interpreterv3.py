from intbase import InterpreterBase, ErrorType
from brewparse import parse_program
import enum


class Type(enum.Enum):
    NIL = 0
    INT = 1
    STRING = 2
    BOOL = 3
    OBJECT = 4
    VOID = 5


class Value:
    def __init__(self, t=None, v=None):
        if t is None:
            self.t = Type.NIL
            self.v = None
        else:
            self.t = t
            self.v = v


class Environment:
    def __init__(self):
        self.env = []

    def enter_block(self):
        self.env[-1].append({})

    def exit_block(self):
        self.env[-1].pop()

    def enter_func(self):
        self.env.append([{}])

    def exit_func(self):
        self.env.pop()

    # define new variable at function scope
    def fdef(self, varname):
        if self.exists_in_func(varname):
            return False
        top_env = self.env[-1]
        top_env[0][varname] = Value()
        return True

    #define new variable at block scope
    def bdef(self, varname):
        if self.exists_in_func(varname):
            return False
        top_env = self.env[-1]
        top_env[-1][varname] = Value()
        return True
    
    #check if exists in current function scope
    def exists_in_func(self, varname):
        for block in self.env[-1]:
            if varname in block:
                return True
        return False

    def exists(self, varname): #check if exists in current scope
        for block in self.env[-1]:
            if varname in block:
                return True
        return False

    def get(self, varname):
        top_env = self.env[-1]
        for block in top_env:
            if varname in block:
                return block[varname]
        return None

    def set(self, varname, value):
        if not self.exists(varname):
            return False
        top_env = self.env[-1]
        for block in top_env:
            if varname in block:
                block[varname] = value
        return True


class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)
        self.funcs = {}
        self.env = Environment()
        self.bops = {"+", "-", "*", "/", "==", "!=", ">", ">=", "<", "<=", "||", "&&"}

    def run(self, program):
        ast = parse_program(program)
        self.__create_function_table(ast)
        self.__run_fcall(self.__get_function("main"))

    def __create_function_table(self, ast):
        self.funcs = {}
        self.func_types = {}

        for func in ast.get("functions"):
            func_name_types = self.name_types(func.get("name"), is_function=True)
            #print(func_name, "-----") 
            
            param_types = []
            for i in func.get("args"):
                param_name_types = self.name_types(i.get("name"), is_function=False)
                param_types.append(param_name_types)
            
            signatures = (func.get("name"), tuple(param_types))
            if signatures in self.funcs:
                super().error(ErrorType.NAME_ERROR, "two+ functions are found with the same name+type signature")

            self.funcs[signatures] = func
            self.func_types[signatures] = func_name_types
            self.funcs[(func.get("name"), len(func.get("args")))] = func
            #print(func) 

    def __get_function(self, name, num_params=0):
        if (name, num_params) not in self.funcs:
            super().error(ErrorType.NAME_ERROR, "function not found")
        return self.funcs[(name, num_params)]

    def __run_vardef(self, statement):
        name = statement.get("name")
        if not self.env.fdef(name):
            super().error(ErrorType.NAME_ERROR, "variable already defined")

        variable_type = self.name_types(name, is_function=False)
        #print("~test~", name, "=====", variable_type) 

        if variable_type == Type.INT:
            default_value = Value(Type.INT, 0)
        elif variable_type == Type.STRING:
            default_value = Value(Type.STRING, "")
        elif variable_type == Type.BOOL:
            default_value = Value(Type.BOOL, False)
        elif variable_type == Type.OBJECT:
            default_value = Value(Type.NIL, None) # nil?
        else:
            super().error(ErrorType.TYPE_ERROR, "invalid variable type")
        
        #print("~test~", name, "=====", default_value) 

        self.env.set(name, default_value)

    def __run_bvardef(self, statement):
        name = statement.get("name")
        if not self.env.bdef(name):
            super().error(ErrorType.NAME_ERROR, "variable already defined")
        
        variable_type = self.name_types(name, is_function=False)
        #print("~test~", name, "=====", variable_type) 

        if variable_type == Type.INT:
            default_value = Value(Type.INT, 0)
        elif variable_type == Type.STRING:
            default_value = Value(Type.STRING, "")
        elif variable_type == Type.BOOL:
            default_value = Value(Type.BOOL, False)
        elif variable_type == Type.OBJECT:
            default_value = Value(Type.NIL, None) # nil?
        else:
            super().error(ErrorType.TYPE_ERROR, "invalid variable type")
        
        #print("~test~", name, "=====", default_value) 

        self.env.set(name, default_value)

    def __run_assign(self, statement): 
        name = statement.get("var")
        value = self.__eval_expr(statement.get("expression"))

        if value.t == Type.VOID:
            super().error(ErrorType.TYPE_ERROR, "cannot assign void to var")

        #print("~confirm~ the name is:", name)
        #print("~confirm~ the value is:", value)

        if name in self.ref_params:
            #print("YESSS: (", name, ") is in:", self.ref_params) 
            main_env, real = self.ref_params[name]
            #print("~confirm~ the real variable is:", real)
            #print("~confirm~ main_env:", main_env)

            for block in main_env[-2]:
                #print("~confirm~ checking block:", block.keys())
                if real in block:
                    #print("YAYY")
                    block[real] = value 
                    return
                
        if not self.env.set(name, value) and "." not in name: 
            print("HERE NOW") 
            super().error(ErrorType.NAME_ERROR, "variable not defined")

        if "." in name:
            #print("THERE IS . IN NAME")
            self.__object_assign(name, value)
            return 

    def __handle_input(self, fcall_name, args):
        """Handle inputi and inputs function calls"""
        if len(args) > 1:
            super().error(ErrorType.NAME_ERROR, "too many arguments for input function")

        if args:
            self.__handle_print(args)

        res = super().get_input()

        return (
            Value(Type.INT, int(res))
            if fcall_name == "inputi"
            else Value(Type.STRING, res)
        )

    def __handle_print(self, args):
        """Handle print function calls"""
        out = ""

        for arg in args:
            c_out = self.__eval_expr(arg)
            if c_out.t == Type.BOOL:
                out += str(c_out.v).lower()
            else:
                out += str(c_out.v)

        super().output(out)

        return Value(Type.VOID, None)

    def __run_fcall(self, func_call_ast):
        fcall_name, args = func_call_ast.get("name"), func_call_ast.get("args")
        #print("~confirm~ the function call_name is:", fcall_name) 
        #print("~confirm~ the args is:", args) 

        if fcall_name == "inputi" or fcall_name == "inputs":
            return self.__handle_input(fcall_name, args)

        if fcall_name == "print":
            return self.__handle_print(args)

        func_def = self.__get_function(fcall_name, len(args))

        formal_args = func_def.get("args") #[a.get("name") for a in func_def.get("args")]
        #print("~confirm~ the formal_args is:",formal_args) 
        
        #actual_args = [self.__eval_expr(a) for a in args]
        #print("~confirm~ the actual_args is:",actual_args) 

        expected_return_type = self.name_types(fcall_name, is_function=True) 
        print("~confirm~ expected return type of:", fcall_name, "is:", expected_return_type)

        self.ref_params = {}
        old_ref_params = self.ref_params.copy()
        new_ref_params = {}

        param_info = []

        for formal, actual in zip(formal_args, args):
            #print()
            #print("~confirm~ formal:",formal)
            #print("~confirm~ actual:",actual)

            formal_name = formal.get("name")
            #print("~confirm~ formal_name is:", formal_name)
            is_ref = formal.get("ref")
            #print("~confirm~ is_ref:", is_ref)
            #print()

            if is_ref:
                #print("its ref!")
                var_name = actual.get("name")
                #print("~confirm~ var_name is:",var_name)

                new_ref_params[formal_name] = (self.env.env, var_name) 
                param_info.append((formal_name, True, var_name))
                #print("~confirm~ param_info is:", param_info)
            else:
                #print("its not ref")
                actual_val = self.__eval_expr(actual)
                #print("~confirm~ actual_value is:", actual_value)
                if actual_val.t == Type.VOID:
                    super().error(ErrorType.TYPE_ERROR, "no passing void")
                param_info.append((formal_name, False, actual_val))
                #print("~confirm~ param_info is:", param_info)

        self.env.enter_func()
        self.ref_params = new_ref_params

        for formal_name, is_ref, value in param_info:
            if is_ref:
                pass
            else:
                self.env.fdef(formal_name)
                self.env.set(formal_name, value)

        res, returned = self.__run_statements(func_def.get("statements"), expected_return_type)

        if not returned:
            res = self.__default_value(expected_return_type) 

        self.ref_params = old_ref_params
        self.env.exit_func()

        return res

    def __run_if(self, statement, expected_return_type):
        cond = self.__eval_expr(statement.get("condition"))

        if cond.t != Type.BOOL:
            super().error(ErrorType.TYPE_ERROR, "condition must be boolean")

        self.env.enter_block()

        res, ret = None, False

        if cond.v:
            res, ret = self.__run_statements(statement.get("statements"),expected_return_type)
        elif statement.get("else_statements"):
            res, ret = self.__run_statements(statement.get("else_statements"), expected_return_type)

        self.env.exit_block()

        return res, ret

    def __run_while(self, statement):
        res, ret = Value(), False

        while True:
            cond = self.__eval_expr(statement.get("condition"))

            if cond.t != Type.BOOL:
                super().error(ErrorType.TYPE_ERROR, "condition must be boolean")

            if not cond.v:
                break

            self.env.enter_block()
            res, ret = self.__run_statements(statement.get("statements"))
            self.env.exit_block()
            if ret:
                break

        return res, ret

    def __run_return(self, statement, expected_return_type):
        expr = statement.get("expression")
        #print("~confirm~ expr is:", expr)

        if expr: 
            return_type = self.__eval_expr(expr)
            #print("~confirm~ the return type is:", return_type.t)

            if expected_return_type == Type.VOID and expr is not None:
                super().error(ErrorType.TYPE_ERROR, "void func cannot return anything!!")

            if return_type.t != expected_return_type:
                print("ERRORRRRR", return_type.t, "DOESNT EQUAL", expected_return_type)
                super().error(ErrorType.TYPE_ERROR, "return type doesnt match expected type")

            return (return_type, True)
        elif expr == None:
            #print("HERE")
            default_is = self.__default_value(expected_return_type)
            print("expr default is:",default_is.v)
            return (default_is, True)
        

    def __run_statements(self, statements, expected_return_type):
        res, ret = Value(), False

        for statement in statements:
            kind = statement.elem_type

            if kind == self.VAR_DEF_NODE:
                self.__run_vardef(statement)
            elif kind == "bvardef": 
                self.__run_bvardef(statement)
            elif kind == "=":
                self.__run_assign(statement)
            elif kind == self.FCALL_NODE:
                self.__run_fcall(statement)
            elif kind == self.IF_NODE:
                res, ret = self.__run_if(statement, expected_return_type)
                if ret:
                    break
            elif kind == self.WHILE_NODE:
                res, ret = self.__run_while(statement)
                if ret:
                    break
            elif kind == self.RETURN_NODE:
                res, ret = self.__run_return(statement, expected_return_type)
                break

        return res, ret

    def __eval_binary_op(self, kind, vl, vr):
        """Evaluate binary operations"""
        tl, tr = vl.t, vr.t
        vl_val, vr_val = vl.v, vr.v

        if kind == "==":
            return Value(Type.BOOL, tl == tr and vl_val == vr_val)
        if kind == "!=":
            return Value(Type.BOOL, not (tl == tr and vl_val == vr_val))

        if tl == Type.STRING and tr == Type.STRING:
            if kind == "+":
                return Value(Type.STRING, vl_val + vr_val)

        if tl == Type.INT and tr == Type.INT:
            if kind == "+":
                return Value(Type.INT, vl_val + vr_val)
            if kind == "-":
                return Value(Type.INT, vl_val - vr_val)
            if kind == "*":
                return Value(Type.INT, vl_val * vr_val)
            if kind == "/":
                return Value(Type.INT, vl_val // vr_val)
            if kind == "<":
                return Value(Type.BOOL, vl_val < vr_val)
            if kind == "<=":
                return Value(Type.BOOL, vl_val <= vr_val)
            if kind == ">":
                return Value(Type.BOOL, vl_val > vr_val)
            if kind == ">=":
                return Value(Type.BOOL, vl_val >= vr_val)

        if tl == Type.BOOL and tr == Type.BOOL:
            if kind == "&&":
                return Value(Type.BOOL, vl_val and vr_val)
            if kind == "||":
                return Value(Type.BOOL, vl_val or vr_val)

        super().error(ErrorType.TYPE_ERROR, "invalid binary operation")

    def __eval_expr(self, expr):
        kind = expr.elem_type

        if kind == self.INT_NODE:
            return Value(Type.INT, expr.get("val"))

        if kind == self.STRING_NODE:
            return Value(Type.STRING, expr.get("val"))

        if kind == self.BOOL_NODE:
            return Value(Type.BOOL, expr.get("val"))

        if kind == self.NIL_NODE:
            return Value(Type.NIL, None)
        
        if kind == "@": 
            return Value(Type.OBJECT, {})

        if kind == self.QUALIFIED_NAME_NODE:
            var_name = expr.get("name")
            #print("~confirm~ var_name is:", var_name)

            if var_name in self.ref_params:
                og_env, real = self.ref_params[var_name]
                return og_env.get(real) 
            
            if "." in var_name:
                return self.__object_read(var_name)

            if not self.env.exists(var_name):
                super().error(ErrorType.NAME_ERROR, "variable not defined")
            return self.env.get(var_name)

        if kind == self.FCALL_NODE:
            return self.__run_fcall(expr)

        if kind in self.bops:
            l, r = self.__eval_expr(expr.get("op1")), self.__eval_expr(expr.get("op2"))
            return self.__eval_binary_op(kind, l, r)

        if kind == self.NEG_NODE:
            o = self.__eval_expr(expr.get("op1"))
            if o.t == Type.INT:
                return Value(Type.INT, -o.v)

            super().error(ErrorType.TYPE_ERROR, "cannot negate non-integer")

        if kind == self.NOT_NODE:
            o = self.__eval_expr(expr.get("op1"))
            if o.t == Type.BOOL:
                return Value(Type.BOOL, not o.v)

            super().error(ErrorType.TYPE_ERROR, "cannot apply NOT to non-boolean")

        if kind == self.CONVERT_NODE:
            return self.__conversion(expr) 

        raise Exception("should not get here!")

    def name_types(self, name, is_function=False): 
        if name == "main":
            return Type.VOID
    
        if name[-1] == "i":
            return Type.INT
        elif name[-1] == "s":
            return Type.STRING
        elif name[-1] == "b":
            return Type.BOOL
        elif name[-1] == "o":
            return Type.OBJECT
        elif name[-1] == "v":
            if is_function:
                return Type.VOID
            if not is_function:
                super().error(ErrorType.TYPE_ERROR, "has to be function to have void type")
        else:
            if is_function:
                super().error(ErrorType.TYPE_ERROR, "function's name doesn't end w a valid type letter (i/s/b/o/v)")
            if not is_function:
                super().error(ErrorType.TYPE_ERROR, "parameter's name doesn't end w a valid type letter (i/s/b/o)")
        
        if not name:
            print("there is no name")
            super().error(ErrorType.TYPE_ERROR, "no name")

    def __conversion(self, convert):
        type = convert.get('to_type')
        value = self.__eval_expr(convert.get("expr"))
        #print(type) ###
        #rint(value) ###

        if type == "int":
            if value.t == Type.INT:
                return value
            elif value.t == Type.STRING:
                if value.v.isdigit():
                    return Value(Type.INT, int(value.v))
                else:
                    super().error(ErrorType.TYPE_ERROR, "invalid parses")
            elif value.t == Type.BOOL:
                return Value(Type.INT, int(value.v))
            else:
                super().error(ErrorType.TYPE_ERROR, "no obj -> int")
        elif type == "str":
            if value.t == Type.STRING:
                return value
            elif value.t == Type.INT:
                return Value(Type.STRING, str(value.v))
            elif value.t == Type.BOOL:
                if value.v:
                    return Value(Type.STRING, "true")
                else:
                    return Value(Type.STRING, "false")
            else:
                super().error(ErrorType.TYPE_ERROR, "no obj -> str")
        elif type == "bool":
            if value.t == Type.BOOL:
                return value
            elif value.t == Type.INT:
                if value.v != 0:
                    return Value(Type.BOOL, True)
                else:
                    return Value(Type.BOOL, False)
            elif value.t == Type.STRING:
                if value.v != "":
                    return Value(Type.BOOL, True)
                else:
                    return Value(Type.BOOL, False)
            else:
                super().error(ErrorType.TYPE_ERROR, "no obj -> bool")

    def __default_value(self, var_type):
        if var_type == Type.INT:
            return Value(Type.INT, 0)
        elif var_type == Type.STRING:
            return Value(Type.STRING, "")
        elif var_type == Type.BOOL:
            return Value(Type.BOOL, False)
        elif var_type == Type.OBJECT:
            return Value(Type.NIL, None)
        elif var_type == Type.VOID:
            return Value(Type.NIL, None)
        else:
            super().error(ErrorType.TYPE_ERROR, "idk type")

    def __object_assign(self, path, value):
        print()
        print("-in handle dotted assign now-")

        obj_section = path.split(".")
        print("parts:", obj_section)
        print("VALUE IS:", value.v)

        curr = self.env.get(obj_section[0])

        for i in range(1, len(obj_section) - 1): # dont use parts[:1] bc its str, same thing in obj_read
            if not self.env.exists(obj_section[0]):
                super().error(ErrorType.NAME_ERROR, "doesnt exist")
            if curr.t != Type.OBJECT:
                super().error(ErrorType.TYPE_ERROR, "base item is not an object")
            elif obj_section[i] not in curr.v:
                super().error(ErrorType.NAME_ERROR, "requested field DNE") 
            else:
                pass

            curr = curr.v[obj_section[i]]
        
        curr.v[obj_section[-1]] = value


    def __object_read(self, path):
        print()
        print("-in eval dotted read now-")

        obj_section = path.split(".")
        print("parts:", obj_section)

        curr = self.env.get(obj_section[0])

        for i in range(1, len(obj_section)):
            if not self.env.exists(obj_section[0]):
                super().error(ErrorType.NAME_ERROR, "doesnt exist")
            if curr.t != Type.OBJECT and i == obj_section[-1]:
                print(i, "is the last item in parts")
                pass
            if curr.t == Type.NIL:
                super().error(ErrorType.FAULT_ERROR, "dereferenced through a nil object reference") 
            elif obj_section[i] not in curr.v:
                super().error(ErrorType.NAME_ERROR, "requested field DNE") 
            else:
                pass

            if curr.t == Type.OBJECT:
                #print("it is obj confirmed")
                pass
            else:
                super().error(ErrorType.TYPE_ERROR, "base item is not an object")
            
            curr = curr.v[obj_section[i]]

        return curr


def main():
    interpreter = Interpreter()

    # To test your own Brewin program, place it in `test.br` and run this main function.
    with open("./test.br", "r") as f:
        program = f.read()

    interpreter.run(program)


if __name__ == "__main__":
    main()