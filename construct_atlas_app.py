import yaml, pathlib, streamlit as st

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

# DEBUG PANEL (helps on Cloud)
with st.expander("Debug: loaded YAML summary", expanded=False):
    st.write("File:", KB_PATH)
    st.write("Top-level keys:", list(KB.keys()))
    st.write("schema_version:", KB.get("schema_version"))

DEFAULT_TAXON = [
    "inhibitory control",
    "delay of gratification",
    "interference control",
    "attentional control",
    "working memory",
    "planning / goal maintenance",
    "monitoring / metacognition",
    "emotion regulation",
    "motivation / value alignment",
    "strategy use",
]

TAXON = KB.get("components_taxonomy", DEFAULT_TAXON)
if "components_taxonomy" not in KB:
    st.warning("`components_taxonomy` missing in constructs.yaml — using defaults.")

if "constructs" not in KB or not isinstance(KB["constructs"], dict):
    st.error("`constructs:` section missing or malformed in constructs.yaml.")
    st.stop()

CDB = KB["constructs"]
