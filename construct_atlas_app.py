import yaml, pathlib, streamlit as st
import pandas as pd

st.set_page_config(page_title="Construct Atlas", page_icon="🧭", layout="wide")

# ---------- KB loader ----------
KB_PATHS = [
    pathlib.Path(__file__).parent / "constructs.yaml",  # same folder as app
    pathlib.Path("constructs.yaml"),                    # repo root
    pathlib.Path("data/constructs.yaml"),               # optional data folder
]

@st.cache_data(show_spinner=False)
def load_kb():
    for p in KB_PATHS:
        if p.exists():
            with p.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data, str(p)
    return None, None

KB, KB_PATH = load_kb()

if KB is None or not isinstance(KB, dict):
    st.error("Could not load a valid YAML dict from any expected path.\n"
             f"Tried: {[str(p) for p in KB_PATHS]}")
    st.stop()

with st.expander("Debug: loaded YAML summary", expanded=False):
    st.write("File:", KB_PATH)
    st.write("Top-level keys:", list(KB.keys()))
    st.write("schema_version:", KB.get("schema_version"))

TAXON = KB.get("components_taxonomy", [])
CONSTRUCTS = KB.get("constructs", {})
MODELS = KB.get("models", {})

# ---------- UI helpers ----------
def pill(s): return f"<span style='padding:2px 8px;border:1px solid #ddd;border-radius:12px;margin-right:6px'>{s}</span>"

def show_construct_card(key, c):
    st.markdown(f"### {c.get('label', key)}")
    if c.get("synonyms"):
        st.markdown("**Synonyms:** " + ", ".join(c["synonyms"]))
    st.markdown("**Definition:** " + c.get("definition","—"))
    if "components" in c:
        st.markdown("**Components:**")
        cols = st.columns(4)
        i=0
        for comp, strength in c["components"].items():
            cols[i%4].markdown(pill(f"{comp} • {strength}"), unsafe_allow_html=True)
            i+=1
    if "theories" in c:
        st.markdown("**Theories:** " + ", ".join(c["theories"]))
    if "mechanisms" in c:
        st.markdown("**Mechanisms:**")
        for m in c["mechanisms"]:
            st.markdown(f"- {m}")
    if "measures" in c:
        st.markdown("**Measures:**")
        for m in c["measures"]:
            line = f"- *{m.get('name','?')}* — {m.get('type','')}."
            if m.get("targets"): line += f" Targets: {', '.join(m['targets'])}."
            if m.get("citation"): line += f" {m['citation']}"
            st.markdown(line)
    if "citations" in c:
        with st.expander("Citations"):
            for cit in c["citations"]:
                st.markdown("- " + cit)
    if c.get("notes"):
        st.info(c["notes"])

def page_explore_constructs():
    st.title("🧭 Construct Atlas — Explore Constructs")

    # taxonomy chips
    if TAXON:
        st.subheader("Components taxonomy")
        st.markdown(" ".join([pill(x) for x in TAXON]), unsafe_allow_html=True)

    keys_sorted = sorted(CONSTRUCTS.keys())
    pick = st.selectbox("Choose a construct", keys_sorted, index=keys_sorted.index("self-control") if "self-control" in keys_sorted else 0)
    show_construct_card(pick, CONSTRUCTS[pick])

    # quick search table
    st.subheader("Browse all constructs")
    rows=[]
    for k, c in CONSTRUCTS.items():
        rows.append({
            "key": k,
            "label": c.get("label", k),
            "definition": c.get("definition",""),
            "components": ", ".join(c.get("components",{}).keys())
        })
    df = pd.DataFrame(rows).sort_values("label")
    st.dataframe(df, use_container_width=True)

def page_compare_models():
    st.title("🔬 Compare Self-Control / SRL Models")

    if not MODELS:
        st.error("No `models:` section found in constructs.yaml.")
        return

    domain = st.selectbox("Filter by domain (optional)", ["all","general","education/SRL"])
    models_filtered = {k:v for k,v in MODELS.items() if domain=="all" or v.get("domain","general")==domain}

    keys = list(models_filtered.keys())
    sel = st.multiselect("Select models to compare", keys, default=keys[:3])
    if not sel:
        st.info("Select at least one model.")
        return

    dims = ["level_of_analysis","conflict","emotion_role","cognitive_function"]
    nice = {
        "level_of_analysis":"Level of Analysis",
        "conflict":"Conflict",
        "emotion_role":"Emotion Role",
        "cognitive_function":"Cognition Function",
    }
    data = {"Dimension":[nice[d] for d in dims]}
    for k in sel:
        m = models_filtered[k]
        dd = m.get("dimensions", {})
        data[m.get("label",k)] = [dd.get(d,"—") for d in dims]
    df = pd.DataFrame(data)
    st.table(df)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download table (CSV)", csv, file_name="model_comparison.csv", mime="text/csv")

    st.subheader("📚 Key References")
    for k in sel:
        m = models_filtered[k]
        with st.expander(m.get("label",k)):
            for cit in m.get("key_papers", []):
                st.markdown("- " + cit)

# ---------- Router ----------
tabs = st.tabs(["Explore Constructs","Compare Models"])
with tabs[0]:
    page_explore_constructs()
with tabs[1]:
    page_compare_models()
