from __future__ import annotations

import ast
from typing import Any, Dict


ALLOWED_BOOL_OPS = (ast.And, ast.Or)
ALLOWED_CMPS = (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE)
ALLOWED_UNARY = (ast.Not,)


class SafeExprError(ValueError):
    pass


def evaluate(expr: str, context: Dict[str, Any]) -> Any:
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise SafeExprError(str(exc)) from exc
    return _eval_node(tree.body, context)


def _eval_node(node: ast.AST, context: Dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return _resolve_name(node.id, context)
    if isinstance(node, ast.Attribute):
        base = _eval_node(node.value, context)
        if isinstance(base, dict):
            return base.get(node.attr)
        return getattr(base, node.attr, None)
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ALLOWED_BOOL_OPS):
        values = [_eval_node(v, context) for v in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        return any(values)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ALLOWED_UNARY):
        operand = _eval_node(node.operand, context)
        return not operand
    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, context)
        result = True
        for op, comparator in zip(node.ops, node.comparators):
            right = _eval_node(comparator, context)
            if not _compare(op, left, right):
                result = False
                break
            left = right
        return result
    raise SafeExprError(f"Unsupported expression node: {type(node).__name__}")


def _compare(op: ast.cmpop, left: Any, right: Any) -> bool:
    if isinstance(op, ast.Eq):
        return left == right
    if isinstance(op, ast.NotEq):
        return left != right
    if isinstance(op, ast.Lt):
        return left < right
    if isinstance(op, ast.LtE):
        return left <= right
    if isinstance(op, ast.Gt):
        return left > right
    if isinstance(op, ast.GtE):
        return left >= right
    raise SafeExprError(f"Unsupported comparator: {type(op).__name__}")


def _resolve_name(name: str, context: Dict[str, Any]) -> Any:
    if name in context:
        return context[name]
    raise SafeExprError(f"Unknown name: {name}")
