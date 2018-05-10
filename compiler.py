import  os
import sys
cwd = os.getcwd()
sys.path.append(os.path.join(cwd, "tiger-rpython"))

from src.parser import *

# TODO: keep types in a data structure
module = '(module)'
types = '''
  (type $t0 (func (param i32)))
  (type $t1 (func))'''
imports = '''
  (import "env" "memory" (memory $0 1))
  (import "env" "print_int" (func $print_int (type $t0)))'''
exports = '''
  (export "main" (func $main))'''
data = r'''
  (data 0 (offset (i32.const 4)) "\20\27\00\00")
'''

# TODO: check if unsigned integer instructions are needed
emit = {
    IntegerValue: lambda intval: ['i32.const ' +  str(intval.value)],
    Add: lambda add: comp(add.left) + comp(add.right) + ['i32.add'],
    Subtract: lambda sub: comp(sub.left) + comp(sub.right) + ['i32.sub'],
    Multiply: lambda mul: comp(mul.left) + comp(mul.right) + ['i32.mul'],
    Divide: lambda div: comp(div.left) + comp(div.right) + ['i32.div_s'],
    Equals: lambda eq: comp(eq.left) + comp(eq.right) + ['i32.eq'],
    NotEquals: lambda ne: comp(ne.left) + comp(ne.right) + ['i32.ne'],
    LessThan: lambda lt: comp(lt.left) + comp(lt.right) + ['i32.lt_s'],
    GreaterThan: lambda gt: comp(gt.left) + comp(gt.right) + ['i32.gt_s'],
    LessThanOrEquals: lambda le: comp(le.left) + comp(le.right) + ['i32.le_s'],
    GreaterThanOrEquals: lambda ge: comp(ge.left) + comp(ge.right) + ['i32.ge_s'],
    And: lambda and_: comp(and_.left) + comp(and_.right) + ['i32.and'],
    Or: lambda or_: comp(or_.left) + comp(or_.right) + ['i32.or']
}

def comp(ast):
    code = emit[ast.__class__](ast)
    return code


if __name__ == '__main__':
    test_path = os.path.join("tests", sys.argv[1])
    with open(test_path, 'r') as tiger_file:
        tiger_source = tiger_file.read()
        ast = Parser(tiger_source).parse()
        print(ast)
        # main_body = '\n    '.join(comp(ast))
        main_body = '\n    '.join(comp(ast)) + '\n    call $print_int' # no print yet
        func_main = '\n  (func $main (type $t1)\n    ' + main_body + '\n  )'
        module = module[:-1] + types + imports + func_main + exports + data + module[-1:]
        outfile = open(test_path[:-4] + '.wat', 'w')
        outfile.write(module)
