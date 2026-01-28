from enum import Enum, auto

class OpCode(Enum):
    PUSH_CONST = auto()   # Push constant from pool
    PUSH_TRUE = auto()
    PUSH_FALSE = auto()
    
    # Variable access
    DEFINE_GLOBAL = auto()
    GET_GLOBAL = auto()
    SET_GLOBAL = auto()
    GET_LOCAL = auto()
    SET_LOCAL = auto()
    GET_ATTR = auto()     # For mouse.x, key.type etc
    SET_ATTR = auto()
    
    # Binary Ops
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    EQUAL = auto()
    NOT_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    
    # Unary Ops
    NEGATE = auto()
    NOT = auto()
    
    # Control Flow
    JUMP = auto()         # Jump forward
    JUMP_IF_FALSE = auto()# Jump if top is false
    JUMP_IF_TRUE = auto() # Jump if top is true
    LOOP = auto()         # Jump backward
    
    # Functions
    CALL = auto()
    RETURN = auto()
    
    # Stack management
    POP = auto()

    # Lists and Iteration
    BUILD_LIST = auto()   # Build list from N elements on stack
    BUILD_MAP = auto()    # Build dict from N*2 elements on stack (key, val, key, val...)
    GET_ITER = auto()     # Get iterator from object
    FOR_ITER = auto()     # Get next item from iterator or jump to end
    INDEX_GET = auto()    # obj[index]
    INDEX_SET = auto()    # obj[index] = val

    # Optimized Opcodes
    CALL_KW = auto()      # Call with keyword arguments
    JUMP_IF_FALSE_POP = auto() # Jump and pop if false
    JUMP_IF_TRUE_POP = auto()  # Jump and pop if true
    INC_GLOBAL = auto()        # x = x + 1 (optimized)
    ADD_GLOBAL = auto()        # x = x + y (optimized)
    SET_ATTR_FAST = auto()     # obj.attr = val (optimized)
    RETURN_NONE = auto()       # Return None (optimized)
    SET_LOCAL_POP = auto()     # Set local and pop
    SET_GLOBAL_POP = auto()    # Set global and pop
    SET_ATTR_POP = auto()      # Set attr and pop
    YIELD = auto()             # Suspend execution until next tick
