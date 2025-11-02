


I changed "if type(op1) == int and type(op2) == int:" to "if isinstance(op1, int) and isinstance(op2, int):" 
format because I realized the former would take a lot more time. The former needs python to look up the type
of each variable and then compare it so it takes long than isinstance. 