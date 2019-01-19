# tiger-wat

`tiger-wat` is a Tiger to WebAssembly compiler. The main component is a backend
that generates WebAssembly text. The backend relies on ASTs produced by
[tiger-rpython](https://github.com/abrown/tiger-rpython) and uses the [WebAssembly reference
interpreter](https://github.com/WebAssembly/spec/tree/master/interpreter) to
validate the output and convert it to the binary format.

Only a small subset of Tiger language is currently implemented, including
integers, variables, binary expressions, functions, sequences, let expressions,
while expressions, for expressions, and if expressions.

`tiger-wat` includes a testbench application. The testbench server compiles test
cases and serves them to a web client. The client runs the tests and compares
actual and expected results.

## Setup

1. Clone the repository with the `--recursive` flag 

2. Clone the WebAssembly spec, compile the interpreter, and place the `wasm`
   binary on your `PATH`

4. Run `npm install` in the `testbench` directory
   
## Use

Run the testbench with `node server.js`. 

The compiler can also be used without the testbench to compile at the command
line. For example, `python3 compiler.py int.tig` will compile the `int.tig`
test. Use `compile.bash` to compile all of the tests.

