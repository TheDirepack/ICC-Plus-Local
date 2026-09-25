from __future__ import annotations

from typing import Any

from .model import ProjectIndex


def dependency_graph(project: dict[str, Any]) -> dict[str, Any]:
    idx = ProjectIndex(project)
    graph: dict[str, Any] = {}
    for ent in idx.selectables(include_backpack=False):
        deps = {'requires_ids': [], 'excludes_ids': [], 'point_checks': [], 'groups': [], 'rows': [], 'global_requirements': [], 'words': []}
        _walk(ent.value.get('requireds', []), deps)
        graph[ent.id] = deps
    return graph


def _walk(value: Any, deps: dict[str, list[Any]]) -> None:
    if not isinstance(value, list): return
    for req in value:
        if not isinstance(req, dict): continue
        typ = str(req.get('type', '')); positive = req.get('required') is not False
        if typ == 'id':
            ident = str(req.get('reqId', '')).split('/ON#', 1)[0]
            if ident: deps['requires_ids' if positive else 'excludes_ids'].append(ident)
        elif typ in {'points', 'pointCompare'}:
            deps['point_checks'].append({'type': typ, 'required': positive, 'reqId': req.get('reqId'), 'reqId1': req.get('reqId1'), 'operator': req.get('operator'), 'reqPoints': req.get('reqPoints')})
        elif typ == 'selFromGroups': deps['groups'].extend(str(x) for x in req.get('selGroups', []) if isinstance(x, str))
        elif typ == 'selFromRows': deps['rows'].extend(str(x) for x in req.get('selRows', []) if isinstance(x, str))
        elif typ == 'gid': deps['global_requirements'].append(str(req.get('reqId', '')))
        elif typ == 'word': deps['words'].append(str(req.get('reqId', '')))
        _walk(req.get('requireds'), deps); _walk(req.get('orRequireds'), deps)
    for k in ('requires_ids','excludes_ids','groups','rows','global_requirements','words'):
        deps[k] = list(dict.fromkeys(x for x in deps[k] if x))


def direct_conflicts(project: dict[str, Any]) -> list[dict[str, str]]:
    graph = dependency_graph(project); out: list[dict[str, str]] = []
    ids = set(graph)
    for choice, deps in graph.items():
        for other in deps['excludes_ids']:
            if other in ids:
                out.append({'choice': choice, 'conflicts_with': other, 'basis': 'negative id requirement'})
    return out
