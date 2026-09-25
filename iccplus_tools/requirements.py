from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Protocol

from .model import ProjectIndex
from .js_compat import parse_int


class StateLike(Protocol):
    activations: dict[str, int]
    points: dict[str, float]
    variables: dict[str, bool]
    words: dict[str, str]
    row_counts: dict[str, int]


@dataclass(slots=True)
class RequirementTrace:
    path: str
    type: str
    required: bool
    result: bool
    detail: str
    children: list['RequirementTrace']

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        return value


def compare(left: float, right: float, operator: str) -> bool:
    return {
        '1': left > right,
        '2': left >= right,
        '3': left == right,
        '4': left <= right,
        '5': left < right,
        '6': left != right,
    }.get(operator, False)


def selection_compare(count: int, target: int, operator: str) -> bool:
    op = operator or '1'
    if op == '1':
        return not (target > count or (target == 0 and count > 0))
    if op == '2':
        return target == count
    if op == '3':
        return not (target < count or (target == 0 and count > 0))
    if op == '4':
        return target != count
    return False


def _priority(operator: str, priority: int = 1) -> int:
    return priority * 10 + (1 if operator in {'3', '4', '5'} else 2)


@dataclass(slots=True)
class _Expr:
    left: float | '_Expr'
    operator: str
    right: float | '_Expr'
    priority: int


def _eval_expr(value: float | _Expr) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    left, right = _eval_expr(value.left), _eval_expr(value.right)
    if value.operator == '1': return left + right
    if value.operator == '2': return left - right
    if value.operator == '3': return left * right
    if value.operator == '4': return left if right == 0 else left / right
    if value.operator == '5': return left if right == 0 else left % right
    return left


def _arithmetic(initial: float, more: list[dict[str, Any]], points: dict[str, float]) -> float:
    current: float | _Expr = initial
    for item in more:
        operator = str(item.get('operator', '1'))
        raw_priority = item.get('priority', 1)
        priority = _priority(operator, int(raw_priority) if isinstance(raw_priority, (int, float)) and not isinstance(raw_priority, bool) else 1)
        if item.get('id'):
            rhs = float(points.get(str(item['id']), 0))
        else:
            rhs = float(item.get('points', 0) or 0)
        node = _Expr(current, operator, rhs, priority)
        if isinstance(current, _Expr) and priority < current.priority:
            current = _Expr(current.left, current.operator, _Expr(current.right, operator, rhs, priority), current.priority)
        else:
            current = node
    return _eval_expr(current)


class RequirementEngine:
    def __init__(self, index: ProjectIndex):
        self.index = index

    def evaluate(self, requirements: Any, state: StateLike, base_path: str = '/requirements') -> tuple[bool, list[RequirementTrace]]:
        reqs = [x for x in requirements if isinstance(x, dict)] if isinstance(requirements, list) else []
        return self._list(reqs, state, base_path, [])

    def _list(self, reqs: list[dict[str, Any]], state: StateLike, base: str, stack: list[str]) -> tuple[bool, list[RequirementTrace]]:
        met = True
        traces: list[RequirementTrace] = []
        for i, req in enumerate(reqs):
            trace = self._one(req, state, f'{base}/{i}', stack)
            traces.append(trace)
            prereq_prefix = trace.path + '/requireds/'
            direct_children = [
                c for c in trace.children
                if c.path.startswith(prereq_prefix) and '/' not in c.path[len(prereq_prefix):]
            ]
            if all(c.result for c in direct_children):
                met = met and trace.result
        return met, traces

    def _one(self, req: dict[str, Any], state: StateLike, path: str, stack: list[str]) -> RequirementTrace:
        typ = str(req.get('type', ''))
        required = req.get('required') is not False
        nested = [x for x in req.get('requireds', []) if isinstance(x, dict)] if isinstance(req.get('requireds'), list) else []
        children = [self._one(x, state, f'{path}/requireds/{i}', stack) for i, x in enumerate(nested)]
        result = False
        detail = ''

        if required:
            if typ == 'id':
                raw = str(req.get('reqId', ''))
                if '/ON#' in raw:
                    ident, n = raw.split('/ON#', 1)
                    threshold = parse_int(n)
                    count = state.activations.get(ident)
                    if threshold is not None and threshold > 0:
                        result = count is not None and count >= threshold
                        detail = f'{ident} activation count is {count if count is not None else 0}; need at least {threshold}'
                    else:
                        result = ident in state.activations
                        detail = f'{ident} is ' + ('active' if result else 'not active')
                else:
                    result = raw in state.activations
                    detail = f'{raw} is ' + ('active' if result else 'not active')
            elif typ == 'points':
                ident = str(req.get('reqId', ''))
                current = state.points.get(ident)
                target = float(req.get('reqPoints', 0) or 0)
                op = str(req.get('operator', '1') or '1')
                result = current is not None and compare(float(current), target, op)
                detail = f'{ident}={current!r} compared with {target} using operator {op}'
            elif typ == 'or':
                alts = [x for x in req.get('orRequireds', []) if isinstance(x, dict)] if isinstance(req.get('orRequireds'), list) else []
                alt_traces = [self._one(x, state, f'{path}/orRequireds/{i}', stack) for i, x in enumerate(alts)]
                children.extend(alt_traces)
                got = sum(1 for x in alt_traces if x.result)
                raw_need = req.get('orNum', 1)
                need = int(raw_need) if isinstance(raw_need, (int, float)) and not isinstance(raw_need, bool) else 1
                result = got >= need
                detail = f'{got} of {len(alts)} alternatives met; need {need}'
            elif typ == 'pointCompare':
                a, b = str(req.get('reqId', '')), str(req.get('reqId1', ''))
                left, right = state.points.get(a), state.points.get(b)
                more = [x for x in req.get('more', []) if isinstance(x, dict)] if isinstance(req.get('more'), list) else []
                computed = _arithmetic(float(right or 0), more, state.points)
                result = left is not None and right is not None and compare(float(left), computed, str(req.get('operator', '')))
                detail = f'{a}={left!r} compared with computed {computed}'
            elif typ == 'selFromGroups':
                count = 0
                # ICC Plus counts membership per requested group. If the same
                # active choice belongs to two requested groups it counts twice.
                for gid in req.get('selGroups', []) if isinstance(req.get('selGroups'), list) else []:
                    for ident in self.index.group_members(str(gid)):
                        if ident in state.activations:
                            count += 1
                target = int(req.get('selNum', 1) or 0)
                result = selection_compare(count, target, str(req.get('selFromOperators', '1')))
                detail = f'{count} selected entities across requested groups'
            elif typ == 'selFromRows':
                rows = [str(x) for x in req.get('selRows', [])] if isinstance(req.get('selRows'), list) else []
                count = sum(int(state.row_counts.get(x, 0)) for x in rows)
                target = int(req.get('selNum', 1) or 0)
                result = selection_compare(count, target, str(req.get('selFromOperators', '1')))
                detail = f'{count} selected entities across {len(rows)} rows'
            elif typ == 'selFromWhole':
                normal_rows = {x.id for x in self.index.by_kind.get('row', [])}
                count = sum(int(v) for k, v in state.row_counts.items() if k in normal_rows)
                target = int(req.get('selNum', 1) or 0)
                result = selection_compare(count, target, str(req.get('selFromOperators', '1')))
                detail = f'{count} selected entities in normal rows'
            elif typ == 'gid':
                ident = str(req.get('reqId', ''))
                if ident in stack:
                    detail = 'global requirement cycle: ' + ' -> '.join([*stack, ident])
                else:
                    global_req = self.index.one(ident, 'global_requirement')
                    if global_req:
                        result, more = self._list(global_req.value.get('requireds', []), state, global_req.path + '/requireds', [*stack, ident])
                        children.extend(more)
                        detail = f'global requirement {ident}'
                    else:
                        detail = f'global requirement {ident} not found'
            elif typ == 'word':
                ident = str(req.get('reqId', ''))
                expected = {str(x.get('req')) for x in req.get('orRequired', []) if isinstance(x, dict) and x.get('req') is not None} if isinstance(req.get('orRequired'), list) else set()
                actual = state.words.get(ident, '')
                result = actual in expected
                detail = f'{ident}={actual!r}; accepted values={sorted(expected)!r}'
            else:
                detail = f'unknown requirement type {typ!r}'
        else:
            if typ == 'id':
                raw = str(req.get('reqId', ''))
                if '/ON#' in raw:
                    ident, n = raw.split('/ON#', 1)
                    threshold = parse_int(n)
                    count = state.activations.get(ident)
                    if threshold is not None and threshold > 0:
                        result = count is None or count < threshold
                    else:
                        result = ident not in state.activations
                else:
                    result = raw not in state.activations
                detail = f'negative id requirement for {raw}'
            elif typ == 'or':
                alts = [x for x in req.get('orRequireds', []) if isinstance(x, dict)] if isinstance(req.get('orRequireds'), list) else []
                alt_traces = [self._one(x, state, f'{path}/orRequireds/{i}', stack) for i, x in enumerate(alts)]
                children.extend(alt_traces)
                got = sum(1 for x in alt_traces if x.result)
                raw_need = req.get('orNum', 1)
                need = int(raw_need) if isinstance(raw_need, (int, float)) and not isinstance(raw_need, bool) else 1
                result = got < len(alts) - need + 1
                detail = f'inverted X-of rule with {got} met of {len(alts)}'
            elif typ == 'gid':
                positive = dict(req); positive['required'] = True
                trace = self._one(positive, state, path, stack)
                children.extend(trace.children)
                result = not trace.result
                detail = 'inverted ' + trace.detail
            else:
                detail = f'ICC Plus negative semantics are not defined for {typ!r}'

        return RequirementTrace(path, typ, required, result, detail, children)
