# tiger-wat

`tiger-wat` is a Tiger to WebAssembly compiler. The principal component is a
backend that generates WebAssembly text. The backend relies on ASTs produced by
`tiger-rpython` and uses the WebAssembly spec interpreter to validate the output
and convert it to the binary format. `tiger-wat` is written in Python 3.

Only a small subset of Tiger language is currently implemented, including
integers, variables, binary expressions, functions, let expressions, while
expressions, for expressions, and if expressions.

## Installation

1. Clone the repository using the `--recursive` flag to clone `tiger-rpython` as
   well

2. Download the [WebAssembly spec](https://github.com/WebAssembly/spec), compile
the interpreter, and place the `wasm` binary in `/usr/bin/` or some equivalent
directory.

3. If you plan on using the testbench web application, install
   [node](https://nodejs.org/en/download/) 8. In the `testbench` directory, run
   `npm install` to install dependencies and `node server.js` to run the server.
   
## Use

The compiler can be used without the testing environment for a single file in
the `tests` directory. For example, `python compiler.py int.tig`. All tests can
be compiled using the script `compile.bash`.

The testbench application runs on `localhost:8080` and has been tested in
Firefox, Chrome, and Edge.



