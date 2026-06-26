import streamlit as st
import json
from config import get_secret
from pyvis.network import Network
import tempfile
import streamlit.components.v1 as components
from agents import (
    run_requirement_discovery,
    run_dependency_mapping,
    run_risk_analysis,
    run_blast_radius_agent,
    run_explanation_agent,
    run_chat_agent,
)
from graph_ops import (
    clear_graph,
    store_components,
    store_dependencies,
    get_blast_radius,
    get_all_nodes_edges,
    get_critical_nodes,
    get_node_risk_score,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="System Collapse AI",
    page_icon="💀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .stApp {
    background:
      radial-gradient(1200px 600px at 80% -10%, rgba(124,58,237,0.12), transparent 60%),
      radial-gradient(900px 500px at -10% 10%, rgba(29,78,216,0.12), transparent 55%),
      #0a0e1a;
    color: #e2e8f0;
  }

  /* Sidebar */
  [data-testid="stSidebar"] { background: #0d1117 !important; border-right: 1px solid #1e293b; }
  [data-testid="stSidebar"] * { color: #94a3b8 !important; }
  [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #f1f5f9 !important; }

  /* Feature cards (How to use the features) */
  .feature-card {
    position: relative; background: linear-gradient(180deg, #0f1521, #0b0f18);
    border: 1px solid #1e293b; border-radius: 16px; padding: 20px 18px 18px;
    height: 100%; overflow: hidden; transition: border-color 0.2s, transform 0.2s;
  }
  .feature-card:hover { transform: translateY(-3px); }
  .feature-card::before {
    content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: var(--accent, linear-gradient(90deg,#60a5fa,#a78bfa));
  }
  .feature-card.red { border-color: #3f1d2e; } .feature-card.red:hover { border-color: #ef4444; }
  .feature-card.amber { border-color: #3a2a12; } .feature-card.amber:hover { border-color: #f59e0b; }
  .feature-card.blue { border-color: #1c2a4a; } .feature-card.blue:hover { border-color: #3b82f6; }
  .feature-icon { font-size: 22px; margin-bottom: 8px; display: block; }
  .feature-title { font-family: 'JetBrains Mono', monospace; font-size: 14px; font-weight: 700; color: #f1f5f9; margin-bottom: 6px; }
  .feature-desc { font-size: 12px; color: #94a3b8; line-height: 1.55; }

  /* How-to-Use guide steps */
  .guide-step { display: flex; gap: 10px; align-items: flex-start; padding: 8px 0; border-bottom: 1px solid #161e2e; }
  .guide-step:last-child { border-bottom: none; }
  .guide-num {
    flex: none; width: 24px; height: 24px; border-radius: 7px;
    display: flex; align-items: center; justify-content: center;
    font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700;
    color: #c4b5fd !important; background: linear-gradient(135deg, rgba(29,78,216,0.25), rgba(124,58,237,0.25));
    border: 1px solid #312e81;
  }
  .guide-title { color: #e2e8f0 !important; font-size: 12.5px; font-weight: 600; line-height: 1.3; }
  .guide-desc { color: #64748b !important; font-size: 11px; line-height: 1.4; margin-top: 2px; }

  /* Metric cards */
  [data-testid="stMetric"] {
    background: linear-gradient(180deg, #0f1521, #0d1117);
    border: 1px solid #1e293b; border-radius: 14px; padding: 16px;
    transition: border-color 0.2s, transform 0.2s;
  }
  [data-testid="stMetric"]:hover { border-color: #3b82f6; transform: translateY(-2px); }
  [data-testid="stMetricValue"] { color: #f1f5f9 !important; font-family: 'JetBrains Mono', monospace; }
  [data-testid="stMetricLabel"] { color: #64748b !important; }

  /* Inputs */
  .stTextArea textarea, .stTextInput input {
    background: #0d1117 !important; border: 1px solid #1e293b !important;
    color: #e2e8f0 !important; border-radius: 8px !important; font-family: 'Inter', sans-serif;
  }
  .stTextArea textarea:focus, .stTextInput input:focus { border-color: #3b82f6 !important; box-shadow: 0 0 0 2px rgba(59,130,246,0.2) !important; }

  /* Buttons */
  .stButton > button {
    background: linear-gradient(135deg, #1d4ed8, #7c3aed) !important;
    color: #fff !important; border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; font-size: 14px !important; padding: 10px 24px !important;
    transition: all 0.2s !important;
  }
  .stButton > button:hover { opacity: 0.9 !important; transform: translateY(-1px) !important; }

  /* Custom cards */
  .card { background: #0d1117; border: 1px solid #1e293b; border-radius: 12px; padding: 20px; margin: 8px 0; transition: border-color 0.2s; }
  .card:hover { border-color: #334155; }
  .card-red { background: #0d1117; border: 1px solid #7f1d1d; border-radius: 12px; padding: 20px; margin: 8px 0; }
  .card-yellow { background: #0d1117; border: 1px solid #78350f; border-radius: 12px; padding: 20px; margin: 8px 0; }
  .card-green { background: #0d1117; border: 1px solid #14532d; border-radius: 12px; padding: 20px; margin: 8px 0; }

  .badge-red { background: #7f1d1d; color: #fca5a5; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
  .badge-yellow { background: #78350f; color: #fcd34d; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
  .badge-green { background: #14532d; color: #6ee7b7; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
  .badge-blue { background: #1e3a5f; color: #93c5fd; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }

  .section-header { color: #64748b; font-size: 11px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 12px; }
  .node-name { font-family: 'JetBrains Mono', monospace; font-size: 16px; font-weight: 700; color: #f1f5f9; }
  .impact-score { font-family: 'JetBrains Mono', monospace; font-size: 48px; font-weight: 700; color: #ef4444; line-height: 1; }
  .impact-label { font-size: 12px; color: #64748b; margin-top: 4px; }
  .affected-item { display: flex; align-items: center; gap: 8px; padding: 8px 0; border-bottom: 1px solid #1e293b; font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #fca5a5; }
  .affected-item:last-child { border-bottom: none; }
  .pulse { display: inline-block; width: 8px; height: 8px; background: #ef4444; border-radius: 50%; box-shadow: 0 0 0 0 rgba(239,68,68,0.4); animation: pulse 1.5s infinite; }
  @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); } 70% { box-shadow: 0 0 0 8px rgba(239,68,68,0); } 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); } }
  .logo-text { font-family: 'JetBrains Mono', monospace; font-size: 22px; font-weight: 700; }
  .logo-red { color: #ef4444; }
  .logo-white { color: #f1f5f9; }
  .stSpinner > div { border-top-color: #3b82f6 !important; }
  div[data-testid="stSelectbox"] > div { background: #0d1117 !important; border-color: #1e293b !important; color: #e2e8f0 !important; }
  .stInfo { background: #0f172a !important; border-color: #1e40af !important; color: #93c5fd !important; }
  hr { border-color: #1e293b !important; }
</style>
""", unsafe_allow_html=True)


# ── Session state init ────────────────────────────────────────────────────────
for key, default in {
    "graph_built": False,
    "components": [],
    "dependencies": [],
    "all_nodes": [],
    "all_edges": [],
    "blast_result": None,
    "selected_node": None,
    "explanation": "",
    "risk_scores": {},
    "critical_nodes": [],
    "graph_html": None,
    "chat_history": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── Helpers ───────────────────────────────────────────────────────────────────
def risk_color(score: int) -> str:
    if score >= 75: return "red"
    if score >= 40: return "yellow"
    return "green"


def build_pyvis(nodes, edges, highlighted: list = None, selected: str = None) -> str:
    highlighted = highlighted or []
    net = Network(height="520px", width="100%", bgcolor="#0a0e1a", font_color="#e2e8f0", directed=True)
    net.set_options(json.dumps({
        "nodes": {
            "shape": "dot",
            "size": 22,
            "font": {"size": 14, "face": "JetBrains Mono", "color": "#e2e8f0"},
            "borderWidth": 2,
            "shadow": {"enabled": True, "color": "rgba(0,0,0,0.6)", "size": 10}
        },
        "edges": {
            "arrows": {"to": {"enabled": True, "scaleFactor": 0.8}},
            "color": {"color": "#334155", "highlight": "#ef4444"},
            "width": 2,
            "smooth": {"type": "curvedCW", "roundness": 0.2}
        },
        "physics": {
            "enabled": True,
            "forceAtlas2Based": {"gravitationalConstant": -60, "centralGravity": 0.01, "springLength": 120},
            "solver": "forceAtlas2Based",
            "stabilization": {"iterations": 150}
        },
        "interaction": {"hover": True, "tooltipDelay": 100}
    }))

    for node in nodes:
        name = node["name"]
        score = st.session_state.risk_scores.get(name, 0)
        is_critical = name in st.session_state.critical_nodes
        is_selected = name == selected
        is_affected = name in highlighted

        if is_selected:
            color, border, size = "#1d4ed8", "#60a5fa", 32
        elif is_affected:
            color, border, size = "#7f1d1d", "#ef4444", 28
        elif is_critical:
            color, border, size = "#4c1d95", "#a78bfa", 26
        elif score >= 75:
            color, border, size = "#7f1d1d", "#dc2626", 24
        elif score >= 40:
            color, border, size = "#78350f", "#f59e0b", 22
        else:
            color, border, size = "#134e4a", "#10b981", 20

        tooltip = f"<b>{name}</b><br/>Risk Score: {score}/100<br/>{'⚠ CRITICAL' if is_critical else ''}"
        net.add_node(name, label=name, color={"background": color, "border": border},
                     size=size, title=tooltip,
                     borderWidth=3 if (is_selected or is_critical) else 2)

    for edge in edges:
        is_blast = edge["source"] in highlighted or edge["target"] in highlighted
        net.add_edge(edge["source"], edge["target"],
                     color="#ef4444" if is_blast else "#334155",
                     width=3 if is_blast else 2)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w") as f:
        net.save_graph(f.name)
        html = open(f.name).read()
    return html


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="logo-text"><span class="logo-red">SYS</span><span class="logo-white">::COLLAPSE</span></div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#475569;font-size:12px;margin-top:4px;">Agentic Graph Failure Predictor</p>', unsafe_allow_html=True)
    st.divider()

    st.markdown('<div class="section-header">Engine Status</div>', unsafe_allow_html=True)
    if get_secret("MISTRAL_API_KEY"):
        st.markdown('🟢 <span style="color:#10b981;font-size:13px;">In-Memory Graph Engine Ready</span>', unsafe_allow_html=True)
        st.caption("Powered by NetworkX — zero database setup required.")
    else:
        st.markdown('🟡 <span style="color:#f59e0b;font-size:13px;">Add your Mistral API key</span>', unsafe_allow_html=True)
        st.caption("Set MISTRAL_API_KEY in .streamlit/secrets.toml or a .env file to enable the AI agents.")

    st.divider()
    st.markdown('<div class="section-header">How to Use</div>', unsafe_allow_html=True)
    for i, (title, desc) in enumerate([
        ("Describe your idea", "Type any startup or system idea in the input box."),
        ("Analyze the architecture", "AI agents extract components, map dependencies & score risk."),
        ("Explore the graph", "An interactive dependency graph is rendered instantly."),
        ("Simulate a failure", "Pick any component to knock it offline."),
        ("Watch the blast radius", "The cascade lights up red across every affected system."),
        ("Read the AI analysis", "Get an SRE-style explanation of what breaks and why."),
    ], 1):
        st.markdown(
            f'<div class="guide-step"><span class="guide-num">{i:02d}</span>'
            f'<div><div class="guide-title">{title}</div>'
            f'<div class="guide-desc">{desc}</div></div></div>',
            unsafe_allow_html=True,
        )

    st.divider()
    if st.session_state.graph_built:
        st.markdown('<div class="section-header">Graph Stats</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.metric("Nodes", len(st.session_state.all_nodes))
        c2.metric("Edges", len(st.session_state.all_edges))
        if st.session_state.critical_nodes:
            st.markdown(f'<span class="badge-red">⚠ {len(st.session_state.critical_nodes)} Critical Nodes</span>', unsafe_allow_html=True)
        if st.button("🗑 Reset Graph", use_container_width=True):
            clear_graph()
            for key in ["graph_built","components","dependencies","all_nodes","all_edges","blast_result","selected_node","explanation","risk_scores","critical_nodes","graph_html","chat_history"]:
                st.session_state[key] = [] if key in ["components","dependencies","all_nodes","all_edges","critical_nodes","chat_history"] else (False if key=="graph_built" else (None if key in ["blast_result","selected_node","graph_html"] else ("" if key=="explanation" else {})))
            st.rerun()


# ── Main layout ───────────────────────────────────────────────────────────────
st.markdown("""
<h1 style="font-family:'JetBrains Mono',monospace;font-size:30px;margin-bottom:4px;font-weight:700;">
  ⚡ <span style="background:linear-gradient(90deg,#60a5fa,#a78bfa,#f472b6);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;">System Collapse AI</span>
</h1>
""", unsafe_allow_html=True)
st.markdown('<p style="color:#64748b;font-size:14px;margin-bottom:20px;">Convert <b style="color:#93c5fd;">startup ideas</b> into <b style="color:#93c5fd;">dependency graphs</b>. Predict <b style="color:#fca5a5;">cascading failures</b>. Survive the collapse.</p>', unsafe_allow_html=True)

# ── How to use the features ───────────────────────────────────────────────────
st.markdown('<div class="section-header">How to Use the Features</div>', unsafe_allow_html=True)
fc1, fc2, fc3 = st.columns(3)
with fc1:
    st.markdown(
        '<div class="feature-card red" style="--accent:linear-gradient(90deg,#f87171,#ef4444);">'
        '<span class="feature-icon">🔥</span>'
        '<div class="feature-title">AI Failure Analysis</div>'
        '<div class="feature-desc">An SRE-style post-mortem of what breaks and why after a node fails.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
with fc2:
    st.markdown(
        '<div class="feature-card amber" style="--accent:linear-gradient(90deg,#fbbf24,#f59e0b);">'
        '<span class="feature-icon">⚠️</span>'
        '<div class="feature-title">Critical Nodes</div>'
        '<div class="feature-desc">Your single points of failure — the components everything else depends on.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
with fc3:
    st.markdown(
        '<div class="feature-card blue" style="--accent:linear-gradient(90deg,#60a5fa,#3b82f6);">'
        '<span class="feature-icon">📊</span>'
        '<div class="feature-title">Component Risk Scores</div>'
        '<div class="feature-desc">Every component ranked 0–100, sorted highest-risk first.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
st.markdown('<div style="margin-bottom:24px;"></div>', unsafe_allow_html=True)

# ── Input section ─────────────────────────────────────────────────────────────
if not st.session_state.graph_built:
    col_input, col_examples = st.columns([2, 1])
    with col_input:
        st.markdown('<div class="section-header">Define Your System</div>', unsafe_allow_html=True)
        idea = st.text_area(
            "Startup Idea",
            placeholder="e.g. Build Uber for Pets — on-demand pet transportation with live GPS, vet verification, insurance...",
            height=120,
            label_visibility="collapsed",
        )
        if st.button("🚀 Analyze System Architecture", use_container_width=True):
            if not idea.strip():
                st.error("Enter a startup idea first.")
            else:
                with st.spinner("Running Requirement Discovery Agent..."):
                    components = run_requirement_discovery(idea)
                    st.session_state.components = components

                with st.spinner("Running Dependency Mapping Agent..."):
                    deps = run_dependency_mapping(idea, components)
                    st.session_state.dependencies = deps

                with st.spinner("Running Risk Analysis Agent..."):
                    risk_data = run_risk_analysis(components, deps)
                    st.session_state.risk_scores = risk_data

                with st.spinner("Building dependency graph..."):
                    clear_graph()
                    store_components(components, risk_data)
                    store_dependencies(deps)

                with st.spinner("Loading graph topology..."):
                    nodes, edges = get_all_nodes_edges()
                    st.session_state.all_nodes = nodes
                    st.session_state.all_edges = edges
                    st.session_state.critical_nodes = get_critical_nodes()

                with st.spinner("Rendering graph..."):
                    st.session_state.graph_html = build_pyvis(nodes, edges)
                    st.session_state.graph_built = True

                st.rerun()

    with col_examples:
        st.markdown('<div class="section-header">Example Ideas</div>', unsafe_allow_html=True)
        examples = ["Uber for Pets 🐾", "Airbnb for Boats ⛵", "DoorDash for Pharmacies 💊", "LinkedIn for Freelancers 🧑‍💻"]
        for ex in examples:
            st.markdown(f'<div class="card" style="cursor:default;padding:12px 16px;margin:6px 0;"><span style="font-size:13px;color:#94a3b8;">{ex}</span></div>', unsafe_allow_html=True)

# ── Graph + Analysis section ──────────────────────────────────────────────────
else:
    # Top metrics row
    risk_scores = st.session_state.risk_scores
    avg_risk = int(sum(risk_scores.values()) / len(risk_scores)) if risk_scores else 0
    max_node = max(risk_scores, key=risk_scores.get) if risk_scores else "N/A"
    max_score = risk_scores.get(max_node, 0)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Components", len(st.session_state.all_nodes), "Analyzed")
    m2.metric("Dependencies", len(st.session_state.all_edges), "Mapped")
    m3.metric("Avg Risk Score", f"{avg_risk}/100", "System-wide")
    m4.metric("Highest Risk", max_node, f"{max_score}/100")

    st.divider()

    # Main content: graph left, panel right
    col_graph, col_panel = st.columns([3, 2])

    with col_graph:
        st.markdown('<div class="section-header">Dependency Graph — Click a node to simulate failure</div>', unsafe_allow_html=True)
        
        # Node selector (simulates click)
        node_names = [n["name"] for n in st.session_state.all_nodes]
        selected = st.selectbox(
            "Select node to simulate failure:",
            ["— Select a component —"] + sorted(node_names),
            label_visibility="collapsed",
        )

        if selected and selected != "— Select a component —" and selected != st.session_state.selected_node:
            st.session_state.selected_node = selected
            with st.spinner(f"Traversing blast radius from {selected}..."):
                blast = get_blast_radius(selected)
                st.session_state.blast_result = blast
            with st.spinner("Running Blast Radius + Explanation Agents..."):
                score = run_blast_radius_agent(selected, blast, st.session_state.dependencies)
                explanation = run_explanation_agent(selected, blast, score, st.session_state.components)
                st.session_state.blast_result["impact_score"] = score
                st.session_state.explanation = explanation
            affected = [n for n in blast.get("affected_nodes", []) if n != selected]
            st.session_state.graph_html = build_pyvis(
                st.session_state.all_nodes,
                st.session_state.all_edges,
                highlighted=affected,
                selected=selected,
            )
            st.rerun()

        # Render graph
        if st.session_state.graph_html:
            components.html(st.session_state.graph_html, height=540, scrolling=False)

        # Legend
        st.markdown("""
        <div style="display:flex;gap:16px;margin-top:8px;flex-wrap:wrap;">
          <span style="font-size:11px;color:#64748b;">🔵 Selected</span>
          <span style="font-size:11px;color:#64748b;">🔴 Affected / High Risk</span>
          <span style="font-size:11px;color:#64748b;">🟣 Critical Node</span>
          <span style="font-size:11px;color:#64748b;">🟡 Medium Risk</span>
          <span style="font-size:11px;color:#64748b;">🟢 Low Risk</span>
        </div>
        """, unsafe_allow_html=True)

        # ── Ask about your system (chat) ──────────────────────────────────────
        st.divider()
        st.markdown('<div class="section-header">Ask About Your System</div>', unsafe_allow_html=True)
        st.caption("Ask anything about the components, dependencies, risk scores, or failure points.")

        for turn in st.session_state.chat_history:
            with st.chat_message("user" if turn["role"] == "user" else "assistant"):
                st.markdown(turn["content"])

        prompt = st.chat_input("e.g. Which component should I make redundant first?")
        if prompt:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Analyzing your system..."):
                    answer = run_chat_agent(
                        prompt,
                        st.session_state.components,
                        st.session_state.dependencies,
                        st.session_state.risk_scores,
                        st.session_state.critical_nodes,
                        history=st.session_state.chat_history[:-1],
                    )
                st.markdown(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})

    with col_panel:
        if st.session_state.blast_result and st.session_state.selected_node:
            blast = st.session_state.blast_result
            affected = [n for n in blast.get("affected_nodes", []) if n != st.session_state.selected_node]
            score = blast.get("impact_score", 0)
            rc = risk_color(score)

            st.markdown('<div class="section-header">Blast Radius Analysis</div>', unsafe_allow_html=True)

            # Impact score card
            st.markdown(f"""
            <div class="card-{rc}">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                  <div class="section-header">Failed Component</div>
                  <div class="node-name">💀 {st.session_state.selected_node}</div>
                </div>
                <div style="text-align:right;">
                  <div class="impact-score">{score}</div>
                  <div class="impact-label">Impact Score /100</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Affected systems
            st.markdown(f'<div class="section-header" style="margin-top:16px;">Affected Systems ({len(affected)} components)</div>', unsafe_allow_html=True)
            if affected:
                items_html = "".join([
                    f'<div class="affected-item"><span class="pulse"></span> {n}</div>'
                    for n in affected
                ])
                st.markdown(f'<div class="card-red">{items_html}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="card-green"><span style="color:#10b981;font-size:13px;">✓ No downstream dependencies affected</span></div>', unsafe_allow_html=True)

            # Depth
            depth = blast.get("max_depth", 0)
            st.markdown(f"""
            <div style="display:flex;gap:12px;margin-top:8px;">
              <div class="card" style="flex:1;text-align:center;padding:12px;">
                <div style="font-family:JetBrains Mono;font-size:24px;color:#f59e0b;">{depth}</div>
                <div style="font-size:11px;color:#64748b;">Failure Depth</div>
              </div>
              <div class="card" style="flex:1;text-align:center;padding:12px;">
                <div style="font-family:JetBrains Mono;font-size:24px;color:#ef4444;">{len(affected)}</div>
                <div style="font-size:11px;color:#64748b;">Systems Down</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            st.divider()

            # AI Explanation
            st.markdown('<div class="section-header">AI Failure Analysis</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card" style="font-size:13px;color:#94a3b8;line-height:1.7;">{st.session_state.explanation}</div>', unsafe_allow_html=True)

        else:
            st.markdown("""
            <div class="card" style="text-align:center;padding:60px 20px;">
              <div style="font-size:48px;margin-bottom:16px;">⚡</div>
              <div style="font-size:16px;color:#f1f5f9;font-weight:600;margin-bottom:8px;">Select a node to simulate failure</div>
              <div style="font-size:13px;color:#475569;">The engine will traverse the dependency graph and reveal the cascade</div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # Critical nodes panel
        st.markdown('<div class="section-header">Critical Nodes (Single Points of Failure)</div>', unsafe_allow_html=True)
        if st.session_state.critical_nodes:
            for node in st.session_state.critical_nodes:
                s = risk_scores.get(node, 0)
                rc = risk_color(s)
                badge_map = {"red": "badge-red", "yellow": "badge-yellow", "green": "badge-green"}
                st.markdown(f"""
                <div class="card-{rc}" style="padding:10px 16px;display:flex;justify-content:space-between;align-items:center;">
                  <span style="font-family:JetBrains Mono;font-size:13px;color:#f1f5f9;">⚠ {node}</span>
                  <span class="{badge_map[rc]}">{s}/100</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#475569;font-size:13px;">No critical nodes detected.</p>', unsafe_allow_html=True)

        # Risk score table
        st.divider()
        st.markdown('<div class="section-header">All Component Risk Scores</div>', unsafe_allow_html=True)
        sorted_risks = sorted(risk_scores.items(), key=lambda x: x[1], reverse=True)
        for name, score in sorted_risks:
            rc = risk_color(score)
            bar_color = "#ef4444" if rc=="red" else ("#f59e0b" if rc=="yellow" else "#10b981")
            st.markdown(f"""
            <div style="margin-bottom:10px;">
              <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <span style="font-size:12px;color:#94a3b8;font-family:JetBrains Mono;">{name}</span>
                <span style="font-size:12px;color:{bar_color};font-family:JetBrains Mono;">{score}/100</span>
              </div>
              <div style="background:#1e293b;border-radius:4px;height:4px;">
                <div style="width:{score}%;background:{bar_color};height:4px;border-radius:4px;transition:width 0.5s;"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)