"""
graph_ops.py — In-memory graph operations using NetworkX (replaces Neo4j)
"""

import networkx as nx

_graph: nx.DiGraph = nx.DiGraph()
_risk_scores: dict = {}
_categories: dict = {}


def _infer_category(name: str) -> str:
    lower = name.lower()
    if any(k in lower for k in ["auth", "login", "sso", "oauth"]): return "Security"
    if any(k in lower for k in ["pay", "billing", "refund", "invoice"]): return "Financial"
    if any(k in lower for k in ["order", "booking", "reservation", "checkout"]): return "Commerce"
    if any(k in lower for k in ["gps", "track", "location", "map"]): return "Location"
    if any(k in lower for k in ["notif", "email", "sms", "push", "alert"]): return "Messaging"
    if any(k in lower for k in ["review", "rating", "feedback"]): return "Social"
    if any(k in lower for k in ["insurance", "verify", "vet", "kyc", "compliance"]): return "Compliance"
    if any(k in lower for k in ["user", "profile", "account"]): return "Identity"
    if any(k in lower for k in ["api", "gateway", "service", "infra"]): return "Infrastructure"
    return "Core"


def clear_graph():
    global _graph, _risk_scores, _categories
    _graph = nx.DiGraph()
    _risk_scores = {}
    _categories = {}


def store_components(components: list[str], risk_scores: dict):
    for name in components:
        score = risk_scores.get(name, 30)
        category = _infer_category(name)
        _graph.add_node(name, risk_score=score, category=category)
        _risk_scores[name] = score
        _categories[name] = category


def store_dependencies(deps: list[dict]):
    # Edge A -> B means: A DEPENDS_ON B (if B fails, A fails)
    for dep in deps:
        src, tgt = dep.get("source"), dep.get("target")
        if src and tgt and src in _graph and tgt in _graph:
            _graph.add_edge(src, tgt)


def get_blast_radius(failed_node: str) -> dict:
    """
    Find all nodes that depend on failed_node (directly or transitively).
    Edge A -> B means A depends on B. So ancestors of failed_node are affected.
    nx.ancestors(G, node) returns all nodes that have a directed path TO node.
    """
    if failed_node not in _graph:
        return {
            "failed_node": failed_node,
            "affected_nodes": [failed_node],
            "affected_count": 0,
            "max_depth": 0,
            "own_dependencies": [],
            "total_components": _graph.number_of_nodes(),
            "blast_percentage": 0,
        }

    # All nodes that (directly or transitively) depend on failed_node
    affected_nodes = list(nx.ancestors(_graph, failed_node))

    # Max cascade depth: longest shortest-path from any affected node to failed_node
    max_depth = 0
    for node in affected_nodes:
        try:
            length = nx.shortest_path_length(_graph, node, failed_node)
            if length > max_depth:
                max_depth = length
        except nx.NetworkXNoPath:
            pass

    # The failed node's own direct dependencies (what it relies on)
    own_deps = list(_graph.successors(failed_node))

    total = _graph.number_of_nodes()
    return {
        "failed_node": failed_node,
        "affected_nodes": [failed_node] + affected_nodes,
        "affected_count": len(affected_nodes),
        "max_depth": max_depth,
        "own_dependencies": own_deps,
        "total_components": total,
        "blast_percentage": round((len(affected_nodes) / max(total - 1, 1)) * 100),
    }


def get_all_nodes_edges() -> tuple[list, list]:
    nodes = [
        {
            "name": n,
            "risk_score": _graph.nodes[n].get("risk_score", 0),
            "category": _graph.nodes[n].get("category", "Core"),
        }
        for n in _graph.nodes()
    ]
    edges = [{"source": u, "target": v} for u, v in _graph.edges()]
    return nodes, edges


def get_critical_nodes() -> list[str]:
    """
    Critical nodes = nodes that many others depend on.
    In our graph (A->B = A depends on B), B is critical when many A's point to it.
    = nodes with high in-degree (many dependents).
    """
    in_deg = dict(_graph.in_degree())
    critical = [(n, d) for n, d in in_deg.items() if d >= 2]
    critical.sort(key=lambda x: x[1], reverse=True)
    return [n for n, _ in critical[:5]]


def get_node_risk_score(name: str) -> int:
    return _risk_scores.get(name, 0)
