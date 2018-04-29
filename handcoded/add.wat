(module
  (type $0 (func (param i32 i32) (result i32)))
  (import "env" "memory" (memory $0 1))
  (table $0 0 anyfunc)
  (func $0 (param $lhs i32) (param $rhs i32) (result i32)
    (get_local $lhs)
    (get_local $rhs)
    (i32.add)
  )
  (export "add" (func $0))
  (data 0 (offset (i32.const 4)) "\20\27\00\00")
)
