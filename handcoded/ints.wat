(module
  (type $t0 (func (param i32)))
  (type $t1 (func))
  (import "env" "memory" (memory $0 1))
  (import "env" "print_int" (func $print_int (type $t0)))
  (table $0 0 anyfunc)
  (func $main (type $t1)
    i32.const 42
    call $print_int
    i32.const 83
    call $print_int
  )
  (export "main" (func $main))
  (data 0 (offset (i32.const 4)) "\20\27\00\00")
)
