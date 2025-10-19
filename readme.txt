all good!
i believe the elem_type for the statement node variable definition 'func' in the TA slides are incorrect 
and the right label should be 'vardef'




~ My notes ~
elem.elem_type # returns “func”
elem.get(“name”) # returns “main”
elem.get(“args”) # returns []
elem.get(“statements”) # returns [Element, Element, Element]

1. Test if main exists 
    - make sure we are getting elem_type 'program' & it has a 'functions' key in the dictionary 'self.variable_name_to_value'
    - make sure the elem_type is 'func' and it has dictionary key 'name' that has 'main'
    - if main function doesnt exist, call error provided 
2. run_func tests if the function def node has elem_type 'func'
    - for each statement element, run the run_statement function
3. run_statement
    - there are 3 types of elem_types: 'vardef', '=', 'fcall'
    - 'vardef':
        - make sure the variable is not redefined mult times
    - '=':
        - we send the 'expressions' node to do_assignment to calculate a final value 
        - send both the 'var' variable and the calcualated value to the dictionary
        - make sure the variable already exists, if not then return error message
    - 'fcall': 
        - output using the super() function provided
        - if it is any other 'name' than 'print', call error message 
        - we will take care of inputi() later because inputi() can be assigned 
4. do_assignment
    - this takes the 'var' and 'expression' to the dictionary
5. evaluate_expression
    - 'int' & 'string': 
        - both have the same 'val' key and only need to return the value
    - 'qname': 
        - is similar to previous with a 'name' key, but we need to make sure the variable is defined 
    - '+' & '-': 
        - we need to get the value for each element! we have to recursively call evaluate_expression again because 
          of the fact that those values have to be integers! this will go through the 'int' to return the value
        - i used isInstance() to check if both elements are integers in order to be added or subtracted
        - if elements are not integers, return the error message
    - 'fcall':
        - the reason why I moved this inputi() section here is because I realized inputi() can be called within
          the statement assignment node. we have to make it an option to do 'fcall' from the assignmennt node
        - we can only have 1 or no arguements I believe
        - for more then 1 arguement, return the error message