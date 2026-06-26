# ⚡ Collapse AI

> An **Agentic Graph** system that turns startup ideas into **dependency graphs** and predicts **cascading failures** before they happen — with **zero database setup**.

Most AI agents today are great at building things, but they're terrible at predicting failure.

When we use AI coding tools, we keep saying *"build this"*, *"refine this"*, *"add this feature"*, and eventually we end up with a complex system. But neither the AI nor the developer has a clear understanding of the project's **critical dependencies** and **failure points**.

**Collapse AI** is an agentic system that maps dependencies from a project idea and predicts cascading failures before they happen.

Instead of answering *"How do I build this?"*, it answers **"What breaks if this fails?"**

The system extracts key components and dependencies, holds them as an **in-memory graph** (powered by **NetworkX**), and uses **AI agents** to simulate failure scenarios, identify **single points of failure**, calculate **risk scores**, and explain the blast radius.

Think of it as a **stress test for ideas** before time, money, and tokens are wasted building the wrong thing.

---

## ✨ Highlights

- **No database required** — the dependency graph lives in memory via **NetworkX**.
- **5 AI agents** — discovery, dependency mapping, risk scoring, blast radius, and explanation.
- **Interactive graph** — click any node to simulate a failure and watch the **cascade** light up.
- **One dependency to configure** — just a **Mistral API key**.

---

## 🚀 How to Use

> Follow these **six steps** — the whole flow takes under a minute.

### 1. **Describe your idea**
Type any startup or system idea into the input box, e.g. **"Build Uber for Pets"**.

### 2. **Analyze the architecture**
Click **Analyze System Architecture**. The AI agents run in sequence and:
- **Extract** the system components,
- **Map** the `DEPENDS_ON` relationships,
- **Score** each component's risk from **0–100**.

### 3. **Explore the graph**
An **interactive dependency graph** renders instantly. Node **color** = risk level, node **size** = importance.

### 4. **Simulate a failure**
Pick any component from the **Select node** dropdown to knock it **offline**.

### 5. **Watch the blast radius**
Every **affected system** lights up **red**, and you get an **Impact Score**, the **failure depth**, and the count of **systems down**.

### 6. **Read the AI analysis**
The engine hands the affected nodes to the LLM, which writes a concise **SRE-style explanation** of what breaks and why.

> 💡 **Tip:** Check the **Critical Nodes** panel — those are your **single points of failure**.

---

## Example Workflow

```text
Build Uber for Pets
        ↓
Graph appears
        ↓
Click Payments
        ↓
Half the graph turns red
        ↓
Impact Score: 95
        ↓
AI explains why
```

---

## 🧠 How It Works

```text
User Idea
   │
   ▼
LLM extracts the component graph
   │
   ▼
NetworkX holds the graph in memory
   │
   ▼
NetworkX traverses dependencies (blast radius)
   │
   ▼
LLM explains the results in plain English
```

**The LLM creates the graph. NetworkX performs the reasoning. The LLM explains the reasoning.**

---

## Architecture

```text
Startup Idea
     │
     ▼
[Agent 1: Requirement Discovery]  ─── Extracts 8–14 system components
     │
     ▼
[Agent 2: Dependency Mapping]     ─── Maps DEPENDS_ON relationships
     │
     ▼
[Agent 3: Risk Analysis]          ─── Scores each component 0–100
     │
     ▼
     NetworkX (in-memory graph)   ◄─── Holds nodes + edges
     │
     ▼
[PyVis Visualization]             ─── Interactive graph in Streamlit
     │
     ▼
[User clicks a node]
     │
     ▼
[Graph Traversal]                 ─── Variable-length blast radius
     │
     ▼
[Agent 4: Blast Radius Scoring]   ─── Impact score 0–100
     │
     ▼
[Agent 5: Explanation]            ─── SRE-style failure narrative
```

---

## Graph Model

```text
Node:  Component { name, risk_score (0–100), category }
Edge:  (A) ──DEPENDS_ON──▶ (B)
       "A fails when B fails"  →  B's failure propagates to A
```

**Blast radius** = every node that (directly or transitively) depends on the failed node — found with `networkx.ancestors`.

**Critical nodes** = components with the highest **in-degree** (the most dependents) — i.e. **single points of failure**.

---

## ⚡ Quick Start

### 1. Clone and install

```bash
git clone <this-repo>
cd collapse_ai
pip install -e .          # or: uv sync
```

### 2. Configure your key

Copy `.env.example` to `.env` and add your key:

```bash
cp .env.example .env
```

```env
MISTRAL_API_KEY = "your-mistral-api-key"
```

Or use Streamlit secrets (`.streamlit/secrets.toml`):

```toml
MISTRAL_API_KEY = "your-mistral-api-key"
```

> Get a free **Mistral API key** at https://console.mistral.ai → **API Keys**.

### 3. Run

```bash
streamlit run app.py
```

---

## Project Structure

```text
collapse_ai/
├── app.py              # Main Streamlit UI
├── agents.py           # 5 AI agents (Mistral-powered)
├── graph_ops.py        # In-memory graph engine (NetworkX)
├── config.py           # Loads the Mistral API key
├── pyproject.toml
├── .env.example
├── .streamlit/
│   └── secrets.toml.example
└── README.md
```

---

## Agents

| Agent | Role |
|-------|------|
| **Requirement Discovery** | Extracts system components from the startup idea |
| **Dependency Mapping** | Creates `DEPENDS_ON` relationships |
| **Risk Analysis** | Scores each component **0–100** |
| **Blast Radius** | Turns the graph traversal into an **impact score** |
| **Explanation** | Generates an **SRE-style** failure narrative |

---

## Demo Script

1. Type **"Uber for Pets"**
2. Click **Analyze System Architecture**
3. Watch the agents run and the graph appear
4. Select **"Payments"** from the dropdown
5. Show the **red cascade**, the **impact score**, and the **affected systems**
6. Read the **AI explanation**
7. Select **"Authentication"** — show a different **blast radius**
8. Point to the **Critical Nodes** panel — *"these are the single points of failure"*
