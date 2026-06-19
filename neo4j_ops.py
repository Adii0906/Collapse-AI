"""
neo4j_ops.py — All Neo4j interactions for System Collapse AI
"""

from neo4j import GraphDatabase

from config import get_neo4j_config


# ── Connection ────────────────────────────────────────────────────────────────
def _get_driver():
    uri, user, password = get_neo4j_config()
    return GraphDatabase.driver(uri, auth=(user, password))


def _run(query: str, params: dict = None):
    driver = _get_driver()
    try:
        with driver.session() as session:
            result = session.run(query, params or {})
            return result.data()
    finally:
        driver.close()


# ── Schema setup ──────────────────────────────────────────────────────────────
# Node: (:Component {name: str, risk_score: int, category: str})
# Rel:  (:Component)-[:DEPENDS_ON]->(:Component)
# DEPENDS_ON means: source fails → target may be impacted

SCHEMA_QUERIES = [
    "CREATE CONSTRAINT component_name IF NOT EXISTS FOR (c:Component) REQUIRE c.name IS UNIQUE",
    "CREATE INDEX component_risk IF NOT EXISTS FOR (c:Component) ON (c.risk_score)",
]


def setup_schema():
    for q in SCHEMA_QUERIES:
        try:
            _run(q)
        except Exception:
            pass  # Constraints may already exist


# ── CRUD ──────────────────────────────────────────────────────────────────────
def clear_graph():
    _run("MATCH (c:Component) DETACH DELETE c")


def store_components(components: list[str], risk_scores: dict):
    setup_schema()
    for name in components:
        score = risk_scores.get(name, 30)
        category = _infer_category(name)
        _run(
            """
            MERGE (c:Component {name: $name})
            SET c.risk_score = $score,
                c.category = $category,
                c.created_at = timestamp()
            """,
            {"name": name, "score": score, "category": category},
        )


def store_dependencies(deps: list[dict]):
    """
    deps: [{"source": "Orders", "target": "Payments"}, ...]
    Means: Orders DEPENDS_ON Payments
    So if Payments fails → Orders is affected (reverse traversal)
    """
    for dep in deps:
        _run(
            """
            MATCH (a:Component {name: $source})
            MATCH (b:Component {name: $target})
            MERGE (a)-[:DEPENDS_ON]->(b)
            """,
            {"source": dep["source"], "target": dep["target"]},
        )


# ── Blast Radius — Core Neo4j reasoning ──────────────────────────────────────
def get_blast_radius(failed_node: str) -> dict:
    """
    Use Neo4j variable-length path traversal to find:
    1. All nodes that DEPEND ON the failed node (direct + transitive)
       i.e., nodes that will break because they depend on the failed system
    2. Maximum depth of the failure cascade
    
    Cypher pattern:
      (dependent)-[:DEPENDS_ON*1..]->(failed)
      = nodes that require the failed node, so they are affected
    """
    # Direct and transitive dependents (nodes that rely on the failed node)
    affected_query = """
    MATCH path = (dependent:Component)-[:DEPENDS_ON*1..]->(failed:Component {name: $name})
    WHERE dependent.name <> $name
    WITH dependent, length(path) AS depth
    ORDER BY depth ASC
    RETURN COLLECT(DISTINCT dependent.name) AS affected_nodes,
           MAX(depth) AS max_depth
    """
    result = _run(affected_query, {"name": failed_node})
    affected_nodes = result[0]["affected_nodes"] if result else []
    max_depth = result[0]["max_depth"] if result and result[0]["max_depth"] else 0

    # Also get what the failed node depends on (its own dependencies)
    own_deps_query = """
    MATCH (failed:Component {name: $name})-[:DEPENDS_ON]->(dep:Component)
    RETURN COLLECT(dep.name) AS own_deps
    """
    own_result = _run(own_deps_query, {"name": failed_node})
    own_deps = own_result[0]["own_deps"] if own_result else []

    # Total components in graph (for percentage calculation)
    total_query = "MATCH (c:Component) RETURN COUNT(c) AS total"
    total_result = _run(total_query)
    total = total_result[0]["total"] if total_result else 1

    return {
        "failed_node": failed_node,
        "affected_nodes": [failed_node] + affected_nodes,
        "affected_count": len(affected_nodes),
        "max_depth": max_depth or 0,
        "own_dependencies": own_deps,
        "total_components": total,
        "blast_percentage": round((len(affected_nodes) / max(total - 1, 1)) * 100),
    }


def get_all_nodes_edges() -> tuple[list, list]:
    nodes_q = "MATCH (c:Component) RETURN c.name AS name, c.risk_score AS risk_score, c.category AS category"
    edges_q = "MATCH (a:Component)-[:DEPENDS_ON]->(b:Component) RETURN a.name AS source, b.name AS target"
    nodes = _run(nodes_q)
    edges = _run(edges_q)
    return nodes, edges


def get_critical_nodes() -> list[str]:
    """
    Critical nodes = nodes with the most dependents (highest in-degree in reverse)
    i.e., nodes that many others DEPEND_ON
    """
    q = """
    MATCH (c:Component)<-[:DEPENDS_ON]-(dependent:Component)
    WITH c, COUNT(DISTINCT dependent) AS dependent_count
    WHERE dependent_count >= 2
    RETURN c.name AS name
    ORDER BY dependent_count DESC
    LIMIT 5
    """
    result = _run(q)
    return [r["name"] for r in result]


def get_node_risk_score(name: str) -> int:
    result = _run(
        "MATCH (c:Component {name: $name}) RETURN c.risk_score AS score",
        {"name": name},
    )
    return result[0]["score"] if result else 0


# ── Helpers ───────────────────────────────────────────────────────────────────
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