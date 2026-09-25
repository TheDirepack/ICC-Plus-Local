from __future__ import annotations

import ast
import math
import re
from typing import Mapping

_TOKEN = re.compile(r'\{([^{}]+)\}')
_ALLOWED = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.USub, ast.UAdd, ast.FloorDiv)


def evaluate(text: str, points: Mapping[str, float]) -> float:
    replaced = _TOKEN.sub(lambda m: str(float(points[m.group(1)])), text)
    tree = ast.parse(replaced, mode='eval')
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED):
            raise ValueError(f'unsupported expression node: {type(node).__name__}')
        if isinstance(node, ast.Pow) and isinstance(getattr(node, 'right', None), ast.Constant):
            if abs(float(node.right.value)) > 12:
                raise ValueError('exponent too large')
    value = eval(compile(tree, '<iccplus-expression>', 'eval'), {'__builtins__': {}}, {})
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('expression is not finite')
    return result
