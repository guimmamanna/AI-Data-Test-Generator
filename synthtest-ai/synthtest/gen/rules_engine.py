from __future__ import annotations

from typing import Dict, List, Tuple

from synthtest.schema.canonical import RuleSpec
from synthtest.util.safe_expr import SafeExprError, evaluate


class RuleViolation(Exception):
    pass


def evaluate_rules(rules: List[RuleSpec], context: Dict[str, Dict[str, object]]) -> List[str]:
    violations: List[str] = []
    for rule in rules:
        if _safe_eval(rule.if_expr, context):
            for constraint in rule.then:
                if not _safe_eval(constraint, context):
                    violations.append(constraint)
    return violations


def _safe_eval(expr: str, context: Dict[str, Dict[str, object]]) -> bool:
    try:
        return bool(evaluate(expr, context))
    except SafeExprError:
        return False
