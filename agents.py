"""
agents.py — Five AI agents powering System Collapse AI
Uses Mistral API via LangChain
"""

import json
import re
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import HumanMessage, SystemMessage

from config import get_secret, make_mistral_http_clients


# ── LLM factory ──────────────────────────────────────────────────────────────
def _get_llm(temperature: float = 0.3):
    api_key = get_secret("MISTRAL_API_KEY")
    client, async_client = make_mistral_http_clients(api_key)
    return ChatMistralAI(
        model="mistral-large-latest",
        temperature=temperature,
        mistral_api_key=api_key,
        client=client,
        async_client=async_client,
    )


def _parse_json(text: str) -> dict | list:
    """Strip markdown fences and parse JSON safely."""
    clean = re.sub(r"```(?:json)?|```", "", text).strip()
    # Find first JSON structure
    match = re.search(r'(\[.*\]|\{.*\})', clean, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    return json.loads(clean)


# ── Agent 1: Requirement Discovery ───────────────────────────────────────────
def run_requirement_discovery(idea: str) -> list[str]:
    """
    Extract 8-15 system components from a startup idea.
    Returns: ["Authentication", "Payments", "Orders", ...]
    """
    llm = _get_llm(temperature=0.2)
    messages = [
        SystemMessage(content="""You are a system architect agent specializing in startup product decomposition.
Your job is to extract all technical system components from a startup idea.
Be specific and technical. Include infrastructure, business logic, and user-facing systems.
Return ONLY a JSON array of component name strings. No explanation, no markdown, just the JSON array.
Example output: ["Authentication", "Payments", "Orders", "GPS Tracking", "Notifications"]"""),
        HumanMessage(content=f"""Startup idea: {idea}

Extract 8-14 distinct technical system components that would need to be built.
Return ONLY a JSON array of component names as strings."""),
    ]
    response = llm.invoke(messages)
    try:
        components = _parse_json(response.content)
        if isinstance(components, list):
            return [str(c).strip() for c in components if c]
    except Exception:
        pass
    # Fallback extraction
    return _fallback_components(idea)


def _fallback_components(idea: str) -> list[str]:
    base = ["Authentication", "User Profiles", "Payments", "Notifications", "Admin Dashboard"]
    lower = idea.lower()
    if "pet" in lower or "animal" in lower:
        base += ["Pet Profiles", "Vet Verification", "Insurance", "GPS Tracking", "Booking", "Reviews"]
    elif "food" in lower or "delivery" in lower or "restaurant" in lower:
        base += ["Restaurant Listings", "Order Management", "Driver Tracking", "Reviews", "Refunds"]
    elif "freelanc" in lower or "job" in lower:
        base += ["Job Listings", "Proposals", "Contracts", "Escrow", "Ratings", "Messaging"]
    else:
        base += ["Orders", "Search", "Reviews", "Refunds", "Analytics"]
    return list(dict.fromkeys(base))[:12]


# ── Agent 2: Dependency Mapping ───────────────────────────────────────────────
def run_dependency_mapping(idea: str, components: list[str]) -> list[dict]:
    """
    Create DEPENDS_ON relationships between components.
    A DEPENDS_ON B means: if B fails, A is affected.
    Returns: [{"source": "Orders", "target": "Payments"}, ...]
    """
    llm = _get_llm(temperature=0.1)
    comp_list = "\n".join(f"- {c}" for c in components)
    messages = [
        SystemMessage(content="""You are a dependency mapping agent. 
Your task: identify which system components DEPEND ON other components.
A DEPENDS_ON B means: Component A cannot function if Component B fails.
Return ONLY a JSON array of dependency objects with "source" and "target" keys.
Example: [{"source": "Orders", "target": "Payments"}, {"source": "Refunds", "target": "Payments"}]
Rules:
- Only use component names from the provided list (exact spelling)
- Create 1.5x-2x as many edges as there are components
- Make dependencies realistic and meaningful
- No self-loops
- No duplicate pairs"""),
        HumanMessage(content=f"""Startup idea: {idea}

Components:
{comp_list}

Map the DEPENDS_ON relationships between these components.
Return ONLY a JSON array of {{"source": "...", "target": "..."}} objects."""),
    ]
    response = llm.invoke(messages)
    try:
        deps = _parse_json(response.content)
        if isinstance(deps, list):
            valid = []
            seen = set()
            for d in deps:
                if isinstance(d, dict) and "source" in d and "target" in d:
                    src, tgt = d["source"].strip(), d["target"].strip()
                    if src != tgt and src in components and tgt in components:
                        key = (src, tgt)
                        if key not in seen:
                            seen.add(key)
                            valid.append({"source": src, "target": tgt})
            return valid
    except Exception:
        pass
    return _fallback_deps(components)


def _fallback_deps(components: list[str]) -> list[dict]:
    """Build sensible fallback deps based on common patterns."""
    deps = []
    # Payment-related
    payment_nodes = [c for c in components if any(k in c.lower() for k in ["pay", "billing"])]
    order_nodes = [c for c in components if any(k in c.lower() for k in ["order", "booking"])]
    notif_nodes = [c for c in components if any(k in c.lower() for k in ["notif", "email", "sms"])]
    auth_nodes = [c for c in components if any(k in c.lower() for k in ["auth", "login"])]
    
    for p in payment_nodes:
        for o in order_nodes: deps.append({"source": o, "target": p})
        for n in notif_nodes: deps.append({"source": n, "target": o[0] if order_nodes else p})
    for a in auth_nodes:
        for c in components[:5]:
            if c not in auth_nodes: deps.append({"source": c, "target": a})
    return deps[:20]


# ── Agent 3: Risk Analysis ────────────────────────────────────────────────────
def run_risk_analysis(components: list[str], deps: list[dict]) -> dict:
    """
    Score each component's risk (0-100) based on:
    - How many others depend on it (criticality)
    - Its nature (financial, auth = high risk)
    Returns: {"Payments": 95, "Authentication": 90, ...}
    """
    # Calculate dependency counts first (structural signal)
    dependency_counts = {c: 0 for c in components}
    for dep in deps:
        target = dep.get("target", "")
        if target in dependency_counts:
            dependency_counts[target] += 1

    llm = _get_llm(temperature=0.1)
    comp_with_deps = "\n".join(
        f"- {c} (depended on by {dependency_counts.get(c, 0)} other components)"
        for c in components
    )
    messages = [
        SystemMessage(content="""You are a risk analysis agent for distributed systems.
Score each component's FAILURE RISK on a scale of 0-100.
Consider: number of dependents, component type (financial/auth = high risk), single point of failure potential.
Return ONLY a JSON object mapping component name to integer score.
Example: {"Payments": 95, "Authentication": 88, "Reviews": 25}
Spread scores meaningfully — don't cluster everything at 50."""),
        HumanMessage(content=f"""Components and their dependent counts:
{comp_with_deps}

Return ONLY a JSON object with risk scores 0-100 for each component."""),
    ]
    response = llm.invoke(messages)
    try:
        scores = _parse_json(response.content)
        if isinstance(scores, dict):
            result = {}
            for c in components:
                score = scores.get(c, 30)
                # Boost score based on structural dependency count
                structural_boost = min(dependency_counts.get(c, 0) * 8, 40)
                result[c] = min(int(score) + structural_boost // 3, 100)
            return result
    except Exception:
        pass
    # Structural fallback
    return {
        c: min(30 + dependency_counts.get(c, 0) * 12 +
               (30 if any(k in c.lower() for k in ["pay", "auth", "login"]) else 0), 100)
        for c in components
    }


# ── Agent 4: Blast Radius Scoring ────────────────────────────────────────────
def run_blast_radius_agent(failed_node: str, blast_data: dict, deps: list[dict]) -> int:
    """
    Calculate a final impact score (0-100) based on Neo4j traversal results.
    This agent interprets the graph traversal output from Neo4j.
    """
    affected_count = blast_data.get("affected_count", 0)
    total = blast_data.get("total_components", 1)
    max_depth = blast_data.get("max_depth", 0)
    blast_pct = blast_data.get("blast_percentage", 0)

    # Base score from structural analysis
    base_score = (
        (blast_pct * 0.5) +           # % of system affected
        (min(affected_count * 5, 30)) + # raw count bonus
        (min(max_depth * 10, 20))        # depth bonus
    )

    # Nature bonus
    lower = failed_node.lower()
    if any(k in lower for k in ["pay", "auth", "login", "database", "api gateway"]):
        base_score += 20
    elif any(k in lower for k in ["order", "booking", "core"]):
        base_score += 10

    return min(int(base_score), 100)


# ── Agent 5: Explanation ──────────────────────────────────────────────────────
def run_explanation_agent(
    failed_node: str,
    blast_data: dict,
    impact_score: int,
    all_components: list[str],
) -> str:
    """
    Generate a technical, specific explanation of the failure cascade.
    """
    affected = [n for n in blast_data.get("affected_nodes", []) if n != failed_node]
    own_deps = blast_data.get("own_dependencies", [])
    depth = blast_data.get("max_depth", 0)

    llm = _get_llm(temperature=0.5)
    messages = [
        SystemMessage(content="""You are a senior site reliability engineer (SRE) explaining cascading system failures.
Write concise, technical, specific failure narratives. 
Use concrete language: "X will timeout", "Y will queue and backlog", "Z users will see error 503".
3-4 sentences max. No bullet points. No headers. Pure prose explanation."""),
        HumanMessage(content=f"""System failure analysis:
- Failed component: {failed_node}
- Impact score: {impact_score}/100
- Directly depends on: {', '.join(own_deps) if own_deps else 'nothing (root system)'}
- Cascade affects: {', '.join(affected) if affected else 'no downstream systems'}
- Failure depth: {depth} hops
- Full system has {len(all_components)} components

Explain the real-world cascading failure consequences in 3-4 technical sentences."""),
    ]
    response = llm.invoke(messages)
    return response.content.strip()


def run_chat_agent(
    question: str,
    components: list[str],
    deps: list[dict],
    risk_scores: dict,
    critical_nodes: list[str],
    history: list[dict] | None = None,
) -> str:
    """
    Answer a free-form question about the analyzed system, grounded in its graph.
    """
    dep_lines = [f"{d.get('from')} depends on {d.get('to')}" for d in deps]
    risk_lines = [f"{name}: {score}/100" for name, score in sorted(risk_scores.items(), key=lambda x: x[1], reverse=True)]

    llm = _get_llm(temperature=0.4)
    messages = [
        SystemMessage(content="""You are an architecture and reliability assistant for the user's system.
Answer questions using ONLY the provided components, dependencies, risk scores, and critical nodes.
Be concise and specific (2-5 sentences). If something isn't in the graph, say so plainly.
No headers. Plain prose or short bullets only."""),
        SystemMessage(content=f"""System context:
- Components ({len(components)}): {', '.join(components)}
- Dependencies: {'; '.join(dep_lines) if dep_lines else 'none'}
- Risk scores: {'; '.join(risk_lines) if risk_lines else 'none'}
- Critical nodes (single points of failure): {', '.join(critical_nodes) if critical_nodes else 'none'}"""),
    ]
    for turn in (history or []):
        role = turn.get("role")
        content = turn.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(SystemMessage(content=f"(your previous answer) {content}"))
    messages.append(HumanMessage(content=question))

    response = llm.invoke(messages)
    return response.content.strip()