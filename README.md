# ⚡Collapse AI

> Neo4j-powered Agentic GraphRAG system that converts startup ideas into dependency graphs and predicts cascading failures.


Most AI agents today are great at building things, but they're terrible at predicting failure.

When we use AI coding tools, we keep saying "build this", "refine this", "add this feature", and eventually we end up with a complex system. But neither the AI nor the developer has a clear understanding of the project's critical dependencies and failure points.

 Collapse AI, an agentic system that maps dependencies from a project idea or document and predicts cascading failures before they happen.

Instead of answering "How do I build this?", it answers "What breaks if this fails?"

Using document intelligence, the system extracts key entities and dependencies, stores them as a graph in Neo4j, and uses AI agents to simulate failure scenarios, identify single points of failure, calculate risk scores, and suggest recovery plans.

Think of it as a stress test for ideas, projects, and AI systems before time, money, and tokens are wasted building the wrong thing.

---

## Architecture

```
Startup Idea
     │
     ▼
[Agent 1: Requirement Discovery]  ─── Extracts 8-14 system components
     │
     ▼
[Agent 2: Dependency Mapping]     ─── Maps DEPENDS_ON relationships
     │
     ▼
[Agent 3: Risk Analysis]          ─── Scores each component 0-100
     │
     ▼
     Neo4j AuraDB  ◄──────────────── Stores graph + vector indexes
     │
     ▼
[PyVis Visualization]             ─── Interactive graph in Streamlit
     │
     ▼
[User clicks a node]
     │
     ▼
[Neo4j Cypher Traversal]          ─── Variable-length path blast radius
     │
     ▼
[Agent 4: Blast Radius Scoring]   ─── Impact score 0-100
     │
     ▼
[Agent 5: Explanation]            ─── SRE-style failure narrative
```

## Neo4j Schema

```cypher
// Nodes
(:Component {
  name: String,          // "Payments"
  risk_score: Integer,   // 0-100
  category: String,      // "Financial", "Security", etc.
  created_at: Long       // timestamp
})

// Relationships
(:Component)-[:DEPENDS_ON]->(:Component)
// A DEPENDS_ON B = "A fails when B fails"
// = "B's failure propagates to A"
```

## Key Cypher Queries

### Blast Radius (variable-length traversal)
```cypher
MATCH path = (dependent:Component)-[:DEPENDS_ON*1..]->(failed:Component {name: $name})
WHERE dependent.name <> $name
WITH dependent, length(path) AS depth
ORDER BY depth ASC
RETURN COLLECT(DISTINCT dependent.name) AS affected_nodes,
       MAX(depth) AS max_depth
```

### Critical Nodes (single points of failure)
```cypher
MATCH (c:Component)<-[:DEPENDS_ON]-(dependent:Component)
WITH c, COUNT(DISTINCT dependent) AS dependent_count
WHERE dependent_count >= 2
RETURN c.name AS name
ORDER BY dependent_count DESC
LIMIT 5
```

---

## Quick Start

### 1. Clone and install

```bash
git clone <this-repo>
cd system_collapse_ai
pip install -r requirements.txt
```

### 2. Configure secrets

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Or set up Streamlit secrets (recommended):

```bash
mkdir -p .streamlit
cp .streamlit/secrets.toml .streamlit/secrets.toml
# Edit .streamlit/secrets.toml with your values
```

### 3. Get your API keys

- **Neo4j AuraDB**: Already configured (use your AuraDB password)
- **Mistral API**: https://console.mistral.ai → Get API Key (free tier available)

### 4. Run

```bash
streamlit run app.py
```

---

## Project Structure

```
system_collapse_ai/
├── app.py              # Main Streamlit UI
├── agents.py           # 5 AI agents (Mistral-powered)
├── neo4j_ops.py        # All Neo4j operations + Cypher queries
├── requirements.txt
├── .env.example
├── .streamlit/
│   └── secrets.toml
└── README.md
```

---

## Agents

| Agent | Role |
|-------|------|
| Requirement Discovery | Extracts system components from startup idea |
| Dependency Mapping | Creates DEPENDS_ON relationships |
| Risk Analysis | Scores each component 0-100 |
| Blast Radius | Interprets Neo4j traversal into impact score |
| Explanation | Generates SRE-style failure narrative |

---

## Demo Script

1. Type: **"Uber for Pets"**
2. Click **Analyze System Architecture**
3. Watch agents run and graph appear
4. Select **"Payments"** from the dropdown
5. Show: red cascade, impact score, affected systems
6. Read the AI explanation
7. Select **"Authentication"** — show different blast radius
8. Point to Critical Nodes panel — "these are single points of failure"