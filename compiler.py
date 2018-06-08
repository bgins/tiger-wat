import  os
import sys
import time
cwd = os.getcwd()
sys.path.append(os.path.join(cwd, "tiger-rpython"))

from src.parser import *


def die(err, outpath):
    """Die with a compilation error

    Write and print the error.
    """
    err_message = 'Compilation error: ' + err
    print(err_message)
    outfile = open(outpath + '.err', 'w')
    outfile.write(err_message)
    outfile.close()
    sys.exit()

def set_int_return(env):
    """Set integer return type"""
    env['return_type'] = 'i32'
    return env


# Variables

def variable_declaration(var, env):
    """Declare a variable

    Determine the type and assign it the next index as a label.
    Add the variable and rhs expression to the stack code.

    In the environment, a variable is stored at the matching index in a
    list of locals. This is used throughout the compiler to retrieve the
    appropriate label. Access to names is from the back of the list to
    effectively provide shadowing (see lvalue).
    """
    locals = [l[0] for l in env['locals']]
    if var.type is None and var.exp.__class__ is IntegerValue:
        type_ = 'i32'
    elif var.type.name == 'int':
        type_ = 'i32'
    else:
        type_ = 'string'

    index = len(env['locals'])

    env['locals'].append( (var.name, type_) )
    set_local = ['set_local $' + str(index)]

    expr = comp(var.exp, env)[0]
    env['return_type'] = None

    return (expr + set_local, env)


def assign(assn, env):
    """Assign a local

    More will be needed here to handle strings.
    """
    locals = [l[0] for l in env['locals']]
    if locals and assn.lvalue.name in locals:
        label = locals.index(assn.lvalue.name)
        expr = comp(assn.expression, env)[0]
        env['return_type'] = None
        return (expr + ['set_local $' + str(label)], env)
    else:
        die('variable ' + assn.lvalue.name + ' is not declared', env['outpath'])


def lvalue(lval, env):
    """Evaluate an lval

    Find all matching names in locals and select the last occurrence, which shadows the others.
    Add stack code to get the local value.
    """
    locals = [l[0] for l in env['locals']]
    if locals and lval.name in locals:
        labels = [i for i, x in enumerate(locals) if x == lval.name]
        label = labels[-1]
        type_ = env['locals'][label][1]
        env['return_type'] = type_
        return (['get_local $' + str(label)], env)
    else:
        die('variable ' + lval.name + ' is not declared', env['outpath'])


# Types

def type_id(typeid, env):
    """Retrieve type from TypeId node

    Strings will need to be handled here as well.
    """
    if typeid.name == 'int':
        return ('i32', env)
    else:
        return ('', env)


# Functions

def function_declaration(func, env):
    """Declare a function

    Build up list of params as a list of tuples [(name, type)] and return_type as a string.
    Add the function to environment.
    Generate stack code for params, result, body, and local declarations.
    Append function to declarations in environment.

    Does not add immediately add any stack code to main since function declarations
    are in a different section of the module.
    """
    params = []
    for i in range(0, len(func.parameters)):
        params.append( (func.parameters[i].name, comp(func.parameters[i].type, env)[0]) )
    return_type = comp(func.return_type, env)[0]

    env['funcs'][func.name] = { 'params': params, 'return_type': return_type }

    param_string = ''
    for i in range(0, len(params)):
        param_string += '(param $' + str(i) + ' ' + params[i][1] + ') '

    if return_type:
        result_string = '(result ' + return_type + ')\n    '
    else:
        result_string = ''

    body_env = env.copy()
    body_env['locals'] = params.copy()
    body, body_env = comp(func.body, body_env)

    locals_string = ''
    for index in range(len(params), len(body_env['locals'])):
        type_ = body_env['locals'][index][1]
        locals_string += ('(local $' + str(index) + ' ' + type_ + ')\n    ')

    body_string = '\n    '.join(body)

    env['func_decls'] += ('\n  (func $' + func.name + ' ' + param_string + result_string + locals_string + body_string + ')')

    return ([], env)


def function_call(fc, env):
    """Call a function

    Check if call is to the built-in print function.
    If not, check if the function is defined and check the number of args and their types (ints only for now).
    Generate code if everything checks out.
    """
    if fc.name == 'print':
        func_body = comp(fc.arguments[0], env)[0]
        env['return_type'] = None
        return (func_body + ['call $print'], env)
    else:
        fnames = list(env['funcs'])

        if fnames and fc.name in fnames:
            func = env['funcs'][fc.name]
            params = func['params']
            return_type = func['return_type']
            if len(fc.arguments) < len(params):
                die('call to ' + fc.name + ' does not have enough arguments', env['outpath'])
            elif len(fc.arguments) > len(params):
                die('call to ' + fc.name + ' has too many arguments', env['outpath'])
            else:
                args = []
                for param, arg in zip(params, fc.arguments):
                    arg, arg_env = comp(arg, env)
                    if param[1] == arg_env['return_type']:
                        args.extend(arg)
                    else:
                        die('type of argument to ' + param[0] + ' is ' + arg_env['return_type'] + ', but the parameter has type ' + param[1], env['outpath'])
            env['return_type'] = return_type
            return (args + ['call $' + fc.name ], env)
        else:
            die('function ' + fc.name + ' is not declared', env['outpath'])


# Blocks

def sequence(expressions, env):
    """Compile each expression in a sequence

    Update environment with as we go.
    """
    if expressions:
        code, next_env = comp(expressions[0], env)
        env['return_type'] = next_env['return_type']
        return (code + sequence(expressions[1:], next_env)[0], env)
    else:
        return ([], env)


def let(let, env):
    """Compile let expression

    Compile each declaration in the let block.
    Compile each expression in the in block.
    Check return type and generate block string.
    Add indentation for nice looking code.
    Add let locals to environment, but blot out their names to put them out of scope.
    Update function declarations and return type in the environment.

    Note that this last step is needed so that all wat locals are declared before the
    body of function and maintain their index. In the stack code, they are in a single
    scope, but we only access them from the let environment.
    """
    initial_env_len = len(env['locals'])
    let_env = env.copy()

    decls_code = []
    for decl in let.declarations:
        decl_body, let_env = comp(decl, let_env)
        if (decl_body != []):
            decls_code.extend(decl_body)

    in_code = []
    for expr in let.expressions:
        expr_body, let_env = comp(expr, let_env)
        in_code.extend(expr_body)

    if let_env['return_type'] == 'i32':
       block_string = 'block (result i32)'
    else:
       block_string = 'block'

    let_body = ['  ' + op for op in decls_code + in_code]

    env['locals'] = let_env['locals']
    for index in range(initial_env_len, len(let_env['locals'])):
        env['locals'][index] = ('', env['locals'][index][1])

    env['func_decls'] += let_env['func_decls']
    env['return_type'] = let_env['return_type']

    return ([block_string] + let_body + ['end'], env)


# Structured control flow

def for_(for_, env):
    """Compile for expression

    Add loop variable and set its initial value.
    Add termination value as a local.
    Compile body and add stack code for condition, increment and body.
    Add indentation for nice looking code.
    Check that body does not return a value.

    Note that `br_if 0` checks stack for result from condition. If 1 (true),
    we branch to zero blocks out, i.e. the top of the loop. Otherwise, we continue
    and exit the loop.
    """
    i_index = len(env['locals'])
    env['locals'].append( (for_.var, 'i32') )
    init = comp(for_.start, env)[0] + ['set_local $' + str(i_index)]

    t_index = len(env['locals'])
    env['locals'].append( (for_.var + '_t', 'i32') )
    termination = comp(for_.end, env)[0] + ['set_local $' + str(t_index)]

    for_body = comp(for_.body, env)[0]

    increment = ['get_local $' + str(i_index), 'i32.const 1', 'i32.add', 'set_local $' + str(i_index)]
    condition = ['get_local $' + str(i_index), 'get_local $' + str(t_index), 'i32.le_s', 'br_if 0']

    loop_init = ['  ' + op for op in init + termination]
    loop_body = ['    ' + op for op in for_body + increment + condition]

    if env['return_type'] is not None:
        die('expression in for cannot return a value', env['outpath'])

    return (['block'] + loop_init + ['  loop'] + loop_body + ['  end', 'end'], env)


def while_(while_, env):
    """Compile while expression

    Compile condition and body, and add stack code for both.
    Add indentation for nice looking code.
    Check that body does not return a value.

    Note that `br_if 1` checks the stack for the result from condition and branches one
    block out if 1 (true), which jumps to the end of the enclosing block and terminates the loop.
    """
    condition = ['i32.const 1'] + comp(while_.condition, env)[0] + ['i32.sub', 'br_if 1']
    while_body = comp(while_.body, env)[0]
    loop_body = ['    ' + op for op in condition + while_body + ['br 0']]

    if env['return_type'] is not None:
        die('expression in while cannot return a value', env['outpath'])

    return (['block', '  loop'] + loop_body + ['  end', 'end'], env)


def if_(if_, env):
    """Compile if expression

    Compile condition, if_true arm, and if_false arm (if we have one).
    Check that types are the same and generate if string.
    Add indentation for nice looking code.
    Add condition and bodies to the stack code.

    Strings will need to be handled here as well.
    """
    condition = comp(if_.condition, env)[0]

    body_if_true, if_env = comp(if_.body_if_true, env)
    true_return_type = if_env['return_type']

    if if_.body_if_false:
        body_if_false, if_env = comp(if_.body_if_false, env)
        false_return_type = if_env['return_type']
    else:
        body_if_false = ['nop']
        false_return_type = None

    if true_return_type == 'i32' and false_return_type == 'i32':
        if_string = 'if (result i32)'
    elif true_return_type == None and false_return_type == None:
        if_string = 'if'
    else:
        die('arms of an if-then-else expression must have the same type', env['outpath'])

    true_body = ['  ' + op for op in body_if_true]
    false_body = ['  ' + op for op in body_if_false]

    return(condition + [if_string] + true_body + ['else'] + false_body + ['end'], env)


# Compilation

emit = {
    IntegerValue: lambda intval, env: (['i32.const ' +  str(intval.integer)], set_int_return(env)),
    # StringValue: lambda strval, env: ([''], env),
    Add: lambda add, env: (comp(add.left, env)[0] + comp(add.right, env)[0] + ['i32.add'], set_int_return(env)),
    Subtract: lambda sub, env: (comp(sub.left, env)[0] + comp(sub.right, env)[0] + ['i32.sub'], set_int_return(env)),
    Multiply: lambda mul, env: (comp(mul.left, env)[0] + comp(mul.right, env)[0] + ['i32.mul'], set_int_return(env)),
    Divide: lambda div, env: (comp(div.left, env)[0] + comp(div.right, env)[0] + ['i32.div_s'], set_int_return(env)),
    Equals: lambda eq, env: (comp(eq.left, env)[0] + comp(eq.right, env)[0] + ['i32.eq'], set_int_return(env)),
    NotEquals: lambda ne, env: (comp(ne.left, env)[0] + comp(ne.right, env)[0] + ['i32.ne'], set_int_return(env)),
    LessThan: lambda lt, env: (comp(lt.left, env)[0] + comp(lt.right, env)[0] + ['i32.lt_s'], set_int_return(env)),
    GreaterThan: lambda gt, env: (comp(gt.left, env)[0] + comp(gt.right, env)[0] + ['i32.gt_s'], set_int_return(env)),
    LessThanOrEquals: lambda le, env: (comp(le.left, env)[0] + comp(le.right, env)[0] + ['i32.le_s'], set_int_return(env)),
    GreaterThanOrEquals: lambda ge, env: (comp(ge.left, env)[0] + comp(ge.right, env)[0] + ['i32.ge_s'], set_int_return(env)),
    And: lambda and_, env: (comp(and_.left, env)[0] + comp(and_.right, env)[0] + ['i32.and'], set_int_return(env)),
    Or: lambda or_, env: (comp(or_.left, env)[0] + comp(or_.right, env)[0] + ['i32.or'], set_int_return(env)),
    VariableDeclaration: lambda var, env: variable_declaration(var, env),
    Assign: lambda assn, env: assign(assn, env),
    LValue: lambda lval, env: lvalue(lval, env),
    TypeId: lambda typeid, env: type_id(typeid, env),
    FunctionDeclaration: lambda func, env: function_declaration(func, env),
    FunctionCall: lambda fc, env: function_call(fc, env),
    Sequence: lambda seq, env: sequence(seq.expressions, env),
    Let: lambda l, env: let(l, env),
    For: lambda f, env: for_(f, env),
    While: lambda w, env: while_(w, env),
    If: lambda i, env: if_(i, env)
}


def comp(ast, env):
    """Generate code from AST nodes updating the environment as we go"""
    (code, next_env) = emit[ast.__class__](ast, env)
    return (code, next_env)


module = '(module)'
memory = '''
  (import "env" "memory" (memory $0 1))'''
imports = '''
  (import "env" "print" (func $print (param i32)))'''
exports = '''
  (export "main" (func $main))'''
data = r'''
  (data 0 (offset (i32.const 4)) "\20\27\00\00")
'''


def compile_main(ast, outpath):
    """Compile main function and assemble module

    This is the entry point for the program called from JavaScript.
    Module level code such function declarations and imports are collected at this level,
    and the stack code is assembled including imports, exports, and memory.
    More sections are available in the spec and may be added as needed.
    """
    env = {
        'outpath': outpath,
        'func_decls': '',
        'funcs': {},
        'locals': [],
        'return_type': None,
        'memory': False
    }
    main_body, main_env = comp(ast, env)

    locals_string = ''
    for index in range(0, len(main_env['locals'])):
        locals_string += '(local $' + str(index) + ' ' + main_env['locals'][index][1] + ')\n    '

    main_body_string = '\n    '.join(main_body)

    func_main = '\n  (func $main\n    ' + locals_string + main_body_string + ')'

    if env['memory']:
        return module[:-1] + memory + imports + env['func_decls'] + func_main + exports + data + module[-1:]
    else:
        return module[:-1] + imports + env['func_decls'] + func_main + exports + module[-1:]


if __name__ == '__main__':
    """Read source and start compilation

    Write resulting module to .wat file.
    Track compilation time.
    """
    testpath = os.path.join("tests", sys.argv[1])
    with open(testpath, 'r') as tiger_file:
        start_time = time.time()

        tiger_source = tiger_file.read()
        ast = Parser(tiger_source).parse()
        outpath = testpath[:-4]

        print(ast)
        module = compile_main(ast, outpath)

        outfile = open(outpath + '.wat', 'w')
        outfile.write(module)
        outfile.close()

        elapsed_time = format((time.time() - start_time)*1000.0, '#.2g')
        print(str(elapsed_time) + "ms")
