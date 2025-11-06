import streamlit as st
import yaml, pandas as pd, plotly.graph_objects as go

st.set_page_config(page_title="Construct Atlas – Explore Constructs", layout="wide")
st.title("🧭 Construct Atlas — Explore Constructs")

@st.cache_data
def load_kb(path="constructs.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

KB = load_kb()
TAXON = KB["components_taxonomy"]
CDB = KB["constructs"]

# ---------- helpers ----------
def comp_vector(cnode):
    vec = []
    levels = {"low":1, "medium":2, "strong":3}
    comps = cnode.get("components", {})
    for c in TAXON:
        v = comps.get(c, 0)
        if isinstance(v, str): v = levels.get(v.lower(), 0)
        vec.append(v)
    return vec

def jingle_jangle_alerts(selected):
    # naive alerts: overlap of synonyms/notes flags
    warnings = []
    labels = [CDB[c]["label"].lower() for c in selected]
    if "self-control" in selected and "grit" in selected:
        warnings.append("Jangle risk: **Self-control** and **Grit** often correlate and share self-report items.")
    if "self-control" in selected and "self-regulation" in selected:
        warnings.append("Jingle risk: **Self-control** (trait/impulse conflict) vs. **Self-regulation** (SRL process). Check definitions & measures.")
    if "executive-function" in selected and "self-control" in selected:
        warnings.append("Jangle risk: **EF tasks** are sometimes used as proxies for **Self-control**; construct scopes differ.")
    return warnings

def radar(fig_title, construct_keys):
    fig = go.Figure()
    for k in construct_keys:
        node = CDB[k]
        vec = comp_vector(node)
        fig.add_trace(go.Scatterpolar(
            r=vec + [vec[0]], theta=TAXON + [TAXON[0]],
            name=node["label"], fill='toself', opacity=0.3))
    fig.update_layout(
        title=fig_title, polar=dict(radialaxis=dict(visible=True, range=[0,3])),
        showlegend=True, margin=dict(l=10,r=10,t=40,b=10))
    return fig

def measure_table(keys):
    rows = []
    for k in keys:
        node = CDB[k]
        for m in node.get("measures", []):
            rows.append({
                "Construct": node["label"],
                "Measure": m["name"],
                "Type": m.get("type",""),
                "Targets": ", ".join(m.get("targets", [])),
                "Notes": m.get("notes","")
            })
    return pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["Construct","Measure","Type","Targets","Notes"]
    )

# ---------- sidebar ----------
with st.sidebar:
    st.subheader("Filters")
    search = st.text_input("Search constructs (name/synonym)")
    default_pick = ["self-control","self-regulation","executive-function"]
    keys = list(CDB.keys())
    if search:
        keys = [k for k in keys if search.lower() in (CDB[k]["label"].lower()+" "+" ".join(CDB[k].get("synonyms",[])).lower())]
    selected = st.multiselect("Select constructs to compare", options=keys, default=[k for k in default_pick if k in keys])

if not selected:
    st.info("Use the sidebar to select one or more constructs to compare.")
    st.stop()

# ---------- top warnings ----------
for w in jingle_jangle_alerts(selected):
    st.warning(w)

# ---------- cards ----------
cols = st.columns(min(3, len(selected)))
for idx, k in enumerate(selected):
    node = CDB[k]
    with cols[idx % len(cols)]:
        st.markdown(f"### {node['label']}")
        st.caption(", ".join(node.get("synonyms",[])))
        st.write(f"**Definition:** {node['definition']}")
        st.write("**Key components:** " + ", ".join([f"{c} ({lvl})" if isinstance(lvl,str) else c for c,lvl in node.get('components',{}).items()]))
        if node.get("theories"):
            st.write("**Theories:** " + "; ".join(node["theories"]))
        if node.get("mechanisms"):
            st.write("**Mechanisms:** " + "; ".join(node["mechanisms"]))
        if node.get("interventions"):
            ivs = [f"{iv['name']} → {', '.join(iv.get('target_components',[]))} ({iv.get('strength','')})" for iv in node["interventions"]]
            st.write("**Interventions:**")
            for s in ivs: st.write("• " + s)
        if node.get("exemplar_outcomes"):
            st.write("**Outcomes:** " + ", ".join(node["exemplar_outcomes"]))
        if node.get("notes"): st.info(node["notes"])

st.divider()

# ---------- radar ----------
st.subheader("Component coverage comparison")
st.plotly_chart(radar("Components radar", selected), use_container_width=True)

# ---------- measures ----------
st.subheader("Measures used")
df = measure_table(selected)
st.dataframe(df, use_container_width=True, hide_index=True)

st.caption("Tip: strengthen this KB by adding citations, psychometrics, and outcome links to each measure/construct in the YAML.")
