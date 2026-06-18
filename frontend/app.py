import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
import io
import sys
from pathlib import Path
from typing import Any

# Ensure local directories can be imported when running streamlit from anywhere
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import local backend classes for direct python fallback if API is offline
from api.database import DatabaseManager
from api.orchestrator import RankingOrchestrator
from embeddings.service import EmbeddingService
from embeddings.models import EmbeddingConfig
from reranking.reranker import CrossEncoderReranker

# Configure Streamlit page layout
st.set_page_config(
    page_title="TalentGraph AI",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API endpoint URL
API_URL = "http://localhost:8000"

# --- THEME STATE MANAGEMENT ---
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

IS_DARK = st.session_state.theme == "dark"

# --- API CONNECTIVITY CHECK ---
def check_api_status() -> bool:
    try:
        response = requests.get(f"{API_URL}/health", timeout=1.0)
        return response.status_code == 200
    except Exception:
        return False

API_ONLINE = check_api_status()

# --- BACKEND SINGLETON CACHING (LOCAL FALLBACK) ---
@st.cache_resource
def get_local_backend():
    db = DatabaseManager()
    embeddings = EmbeddingService(EmbeddingConfig(dimension=128))
    reranker = CrossEncoderReranker(backend="mock")
    orchestrator = RankingOrchestrator(
        db=db,
        embedding_service=embeddings,
        cross_encoder=reranker,
    )
    return orchestrator, db

# --- BACKEND HELPER FUNCTIONS ---
def add_job(job_data: dict) -> dict:
    if API_ONLINE:
        try:
            r = requests.post(f"{API_URL}/jobs", json=job_data, timeout=3.0)
            if r.status_code in (200, 201):
                return r.json()
        except Exception:
            pass
    # Local fallback
    _, db = get_local_backend()
    job_mapped = dict(job_data)
    if "raw_description" in job_mapped and "raw_text" not in job_mapped:
        job_mapped["raw_text"] = job_mapped["raw_description"]
    db.save_job(job_mapped)
    return {"status": "success", "job_id": job_data["id"]}

def upload_candidates(candidates_list: list) -> dict:
    if API_ONLINE:
        try:
            r = requests.post(f"{API_URL}/candidates/bulk-upload", json=candidates_list, timeout=5.0)
            if r.status_code in (200, 201):
                return r.json()
        except Exception:
            pass
    # Local fallback
    _, db = get_local_backend()
    for c in candidates_list:
        db.save_candidate(c)
    return {"status": "success", "count": len(candidates_list)}

def get_all_jobs() -> list[dict]:
    _, db = get_local_backend()
    return db.get_all_jobs()

def get_all_candidates() -> list[dict]:
    _, db = get_local_backend()
    return db.get_all_candidates()

def run_ranking(job_id: str, alpha: float = 0.5, top_n: int = 10) -> list[dict]:
    if API_ONLINE:
        try:
            r = requests.post(f"{API_URL}/rank/{job_id}", params={"alpha": alpha, "top_n": top_n}, timeout=10.0)
            if r.status_code == 200:
                return r.json()["results"]
        except Exception:
            pass
    # Local fallback
    orchestrator, _ = get_local_backend()
    return orchestrator.orchestrate_ranking(job_id=job_id, alpha=alpha, top_n=top_n)

def get_candidate_details(candidate_id: str) -> dict:
    if API_ONLINE:
        try:
            r = requests.get(f"{API_URL}/candidates/{candidate_id}", timeout=2.0)
            if r.status_code == 200:
                return r.json()["candidate"]
        except Exception:
            pass
    # Local fallback
    _, db = get_local_backend()
    return db.get_candidate(candidate_id)

def load_sample_dataset() -> bool:
    try:
        # Load sample jobs
        jobs_df = pd.read_csv("data/raw/jobs.csv")
        for _, row in jobs_df.iterrows():
            job_data = {
                "id": row["job_id"],
                "title": row["job_title"],
                "raw_description": row["description"],
                "must_have_skills": [s.strip() for s in str(row["required_skills"]).split(",") if s.strip()],
                "nice_to_have_skills": [s.strip() for s in str(row["preferred_skills"]).split(",") if s.strip()] if pd.notna(row["preferred_skills"]) else [],
                "seniority": row["seniority"],
                "location": row["location"]
            }
            add_job(job_data)
        
        # Load sample candidates
        candidates_df = pd.read_csv("data/raw/candidates.csv")
        candidates_list = []
        for _, row in candidates_df.iterrows():
            cand_data = {
                "id": row["candidate_id"],
                "raw_resume_text": row["resume"],
                "skills_raw": [s.strip() for s in str(row["skills"]).split(",") if s.strip()],
                "experience_years": float(row["years_experience"]) if pd.notna(row["years_experience"]) else 0.0,
                "location": row["location"],
                "github_url": row["github"] if pd.notna(row["github"]) else None,
                "activity_metadata": row["activity_metadata"] if pd.notna(row["activity_metadata"]) else "{}"
            }
            candidates_list.append(cand_data)
        upload_candidates(candidates_list)
        return True
    except Exception as e:
        st.error(f"Failed to load sample dataset: {e}")
        return False

# --- LIVE METRIC BENCHMARK COMPARATOR ---
def run_evaluation_benchmark(alpha: float = 0.5):
    from evaluation.harness import EvaluationHarness
    from evaluation.models import RelevanceJudgment
    from parsers.models import ParsedJob, ParsedResume
    from parsers.resumes import ResumeParser
    from preprocessing.models import CandidateRecord
    
    jobs = get_all_jobs()
    candidates = get_all_candidates()
    
    if not jobs or not candidates:
        return None
        
    judgments = [
        RelevanceJudgment(job_id="j1", candidate_id="c1", relevance=3),
        RelevanceJudgment(job_id="j1", candidate_id="c2", relevance=1),
        RelevanceJudgment(job_id="j1", candidate_id="c3", relevance=0),
        RelevanceJudgment(job_id="j2", candidate_id="c1", relevance=1),
        RelevanceJudgment(job_id="j2", candidate_id="c2", relevance=3),
        RelevanceJudgment(job_id="j2", candidate_id="c3", relevance=0),
    ]
    
    harness = EvaluationHarness()
    
    parsed_jobs = []
    for j in jobs:
        parsed_jobs.append(ParsedJob(
            job_id=j["job_id"],
            title=j["title"],
            seniority=j["seniority"],
            location=j["location"],
            must_have=j["must_have"],
            nice_to_have=j["nice_to_have"],
            responsibilities=j["responsibilities"],
            raw_text=j["raw_text"]
        ))
        
    resume_parser = ResumeParser()
    parsed_resumes_list = []
    parsed_resumes_map = {}
    candidates_meta = {}
    
    orchestrator, db = get_local_backend()
    
    raw_profiles = []
    for cand in candidates:
        record = CandidateRecord.model_validate(cand)
        resume = resume_parser.parse(record)
        parsed_resumes_list.append(resume)
        parsed_resumes_map[record.id] = resume
        candidates_meta[record.id] = record.experience_years or 0.0

        raw_prof = orchestrator.behavioral_extractor.extract_raw_profile(
            candidate_id=record.id,
            metadata=record.activity_metadata,
            github_url=str(record.github_url) if record.github_url else None,
        )
        raw_profiles.append(raw_prof)

    normalized_behav = orchestrator.behavioral_normalizer.normalize_population(raw_profiles)
    behav_profiles = {p.candidate_id: p for p in normalized_behav}
    
    from retrieval.bm25 import BM25Index
    from embeddings.indexer import QdrantIndexer
    from embeddings.models import CandidateVectorPoint
    from retrieval.dense import DenseRetriever
    from retrieval.filter import MetadataFilter
    from retrieval.hybrid import HybridRetriever
    
    bm25_index = BM25Index()
    bm25_index.build_bm25_index(parsed_resumes_list)

    indexer = QdrantIndexer(vector_size=orchestrator.embedding_service.config.dimension)
    candidate_points = []
    for resume in parsed_resumes_list:
        cid = resume.candidate_id
        payload = {
            "skills": resume.raw_skills,
            "experience_years": candidates_meta.get(cid),
            "location": db.get_candidate(cid).get("location"),
        }
        candidate_points.append(
            CandidateVectorPoint(
                id=cid,
                vector=orchestrator.embedding_service.embed_candidate(resume),
                payload=payload,
            )
        )
    indexer.upsert_candidates(candidate_points)

    ontology = orchestrator.kg_builder.ontology_builder.build_ontology(
        [skill for r in parsed_resumes_list for skill in r.raw_skills]
        + [skill for j in parsed_jobs for skill in [*j.must_have, *j.nice_to_have]]
    )
    kg = orchestrator.kg_builder.build_skill_graph(ontology)
    for resume in parsed_resumes_list:
        orchestrator.kg_builder.add_candidate_to_graph(kg, resume)
    for job in parsed_jobs:
        orchestrator.kg_builder.add_job_to_graph(kg, job)

    dense = DenseRetriever(indexer)
    metadata_filter = MetadataFilter()
    hybrid_retriever = HybridRetriever(
        bm25_index=bm25_index,
        dense_retriever=dense,
        metadata_filter=metadata_filter,
        embedding_service=orchestrator.embedding_service,
    )
    
    baseline_recs = harness.run_baseline(parsed_jobs, parsed_resumes_list)
    system_recs = harness.run_full_system(
        jobs=parsed_jobs,
        hybrid_retriever=hybrid_retriever,
        feature_builder=orchestrator.feature_builder,
        scoring_engine=orchestrator.scoring_engine,
        reranker=orchestrator.cross_encoder,
        blender=orchestrator.score_blender,
        resumes=parsed_resumes_map,
        kg=kg,
        behav_profiles=behav_profiles,
        candidates_meta=candidates_meta,
        alpha=alpha
    )
    
    results = harness.compare(baseline_recs, system_recs, judgments, k=3)
    return results

# --- CSS INJECTION & MODERN DESIGN SYSTEM ---
BG_COLOR = "#090d16" if IS_DARK else "#f8fafc"
BG_SUBTLE = "#111827" if IS_DARK else "#f1f5f9"
CARD_COLOR = "#1f2937" if IS_DARK else "#ffffff"
CARD_HOVER = "#374151" if IS_DARK else "#f8fafc"
BORDER_COLOR = "#374151" if IS_DARK else "#e2e8f0"
BORDER_SUBTLE = "#4b5563" if IS_DARK else "#f1f5f9"
TEXT_COLOR = "#f9fafb" if IS_DARK else "#111827"
TEXT_MUTED = "#9ca3af" if IS_DARK else "#64748b"
TEXT_DIM = "#6b7280" if IS_DARK else "#9ca3af"
ACCENT_COLOR = "#6366f1" if IS_DARK else "#3b82f6"  # Indigo/Blue
ACCENT_MUTED = "#4f46e5" if IS_DARK else "#1d4ed8"
ACCENT_GLOW = "rgba(99, 102, 241, 0.15)" if IS_DARK else "rgba(59, 130, 246, 0.08)"
SHADOW_VAL = "0 8px 30px rgba(0,0,0,0.5)" if IS_DARK else "0 8px 30px rgba(0,0,0,0.04), 0 2px 8px rgba(0,0,0,0.02)"

css_style = f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&family=JetBrains+Mono:ital,wght@0,100..800;1,100..800&display=swap" rel="stylesheet">

<style>
/* Keyframe Animations */
@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

@keyframes slideIn {{
    from {{ opacity: 0; transform: translateX(-4px); }}
    to {{ opacity: 1; transform: translateX(0); }}
}}

@keyframes pulseGlow {{
    0% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }}
    70% {{ box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }}
    100% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
}}

/* Hide default streamlit header/decorations */
header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton,
div[data-testid="stSidebarCollapsedControl"] {{
    display: none !important;
}}

/* Global app styling */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container, section[data-testid="stMain"] {{
    background-color: {BG_COLOR} !important;
    color: {TEXT_COLOR} !important;
    font-family: 'DM Sans', -apple-system, sans-serif !important;
}}

.block-container {{
    padding: 1.5rem 2rem 2rem !important;
    max-width: 1400px !important;
}}

/* Custom container wrapper using st.container(border=True) */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background-color: {CARD_COLOR} !important;
    border: 1px solid {BORDER_COLOR} !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
    box-shadow: {SHADOW_VAL} !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
    border-color: {ACCENT_COLOR} !important;
    box-shadow: 0 10px 30px {ACCENT_GLOW} !important;
    transform: translateY(-2px);
}}

/* Custom component metrics */
.metric-card {{
    background: {CARD_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 12px;
    padding: 1.3rem 1.4rem;
    box-shadow: {SHADOW_VAL};
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}}
.metric-card:hover {{
    border-color: {ACCENT_COLOR};
    transform: translateY(-2px);
    box-shadow: 0 10px 25px {ACCENT_GLOW};
}}
.metric-label {{
    font-size: 0.74rem;
    color: {TEXT_MUTED};
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
.metric-value {{
    font-size: 1.7rem;
    font-weight: 700;
    color: {TEXT_COLOR};
    letter-spacing: -0.03em;
    margin-top: 0.25rem;
}}
.metric-delta {{
    font-size: 0.72rem;
    font-weight: 500;
    margin-top: 0.4rem;
    padding: 2px 7px;
    border-radius: 5px;
    display: inline-flex;
    align-items: center;
    gap: 3px;
}}
.delta-up {{ color: #10b981; background: rgba(16, 185, 129, 0.12); }}
.delta-down {{ color: #f43f5e; background: rgba(244, 63, 94, 0.12); }}
.delta-blue {{ color: #6366f1; background: rgba(99, 102, 241, 0.12); }}
.delta-warn {{ color: #f59e0b; background: rgba(245, 158, 11, 0.12); }}

/* Card Wrappers */
.chart-wrap {{
    background: {CARD_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 12px;
    padding: 1.4rem;
    box-shadow: {SHADOW_VAL};
    margin-bottom: 1.25rem;
    transition: border-color 0.25s ease;
    animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}}
.chart-wrap:hover {{
    border-color: {ACCENT_COLOR};
}}
.chart-title {{
    font-size: 0.92rem;
    font-weight: 700;
    color: {TEXT_COLOR};
    letter-spacing: -0.01em;
}}
.chart-subtitle {{
    font-size: 0.76rem;
    color: {TEXT_MUTED};
    margin-bottom: 1rem;
}}

/* Custom HTML Tables */
.data-table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.84rem;
    margin-top: 0.5rem;
}}
.data-table th {{
    text-align: left;
    padding: 0.8rem 1rem;
    color: {TEXT_MUTED};
    font-weight: 600;
    font-size: 0.76rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    border-bottom: 1px solid {BORDER_COLOR};
    background-color: {BG_SUBTLE};
}}
.data-table td {{
    padding: 0.85rem 1rem;
    color: {TEXT_COLOR};
    border-bottom: 1px solid {BORDER_SUBTLE};
}}
.data-table tr {{
    transition: background-color 0.15s ease;
}}
.data-table tr:hover td {{
    background-color: {CARD_HOVER} !important;
}}
.data-table tr:last-child td {{
    border-bottom: none;
}}

/* Custom Status Badges */
.badge {{
    display: inline-block;
    padding: 3px 9px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}}
.badge-green {{
    color: #10b981;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.2);
    animation: pulseGlow 2s infinite;
}}
.badge-red {{ color: #f43f5e; background: rgba(244, 63, 94, 0.12); border: 1px solid rgba(244, 63, 94, 0.2); }}
.badge-amber {{ color: #f59e0b; background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.2); }}
.badge-blue {{ color: #6366f1; background: rgba(99, 102, 241, 0.12); border: 1px solid rgba(99, 102, 241, 0.2); }}

.explain-narrative {{
    background-color: {BG_SUBTLE};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 1.15rem;
    font-size: 0.86rem;
    line-height: 1.55;
    margin-bottom: 1rem;
    animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}}

/* Restyle Native Buttons */
div.stButton > button {{
    background: linear-gradient(135deg, {ACCENT_COLOR}, {ACCENT_MUTED}) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.4rem !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    letter-spacing: -0.015em !important;
    box-shadow: 0 4px 12px {ACCENT_GLOW} !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}}
div.stButton > button:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px {ACCENT_GLOW} !important;
    background: linear-gradient(135deg, {ACCENT_MUTED}, {ACCENT_COLOR}) !important;
}}
div.stButton > button:active {{
    transform: translateY(1px) !important;
}}

/* Restyle Native Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
    background-color: {BG_SUBTLE} !important;
    color: {TEXT_COLOR} !important;
    border: 1px solid {BORDER_COLOR} !important;
    border-radius: 8px !important;
    font-size: 0.86rem !important;
    padding: 0.4rem 0.65rem !important;
    box-shadow: inset 0 1px 2px rgba(0,0,0,0.05) !important;
    transition: all 0.2s ease !important;
}}
.stTextInput input:hover, .stTextArea textarea:hover, .stSelectbox div[data-baseweb="select"]:hover {{
    border-color: {TEXT_MUTED} !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox div[data-baseweb="select"]:focus-within {{
    border-color: {ACCENT_COLOR} !important;
    box-shadow: 0 0 0 3px {ACCENT_GLOW} !important;
}}

/* Pill tab styling */
button[data-baseweb="tab"] {{
    background: transparent !important;
    color: {TEXT_MUTED} !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.4rem !important;
    border: 1px solid transparent !important;
    border-radius: 8px !important;
    transition: all 0.25s ease !important;
}}
button[data-baseweb="tab"]:hover {{
    color: {TEXT_COLOR} !important;
    background-color: {BG_SUBTLE} !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    color: {TEXT_COLOR} !important;
    background: {CARD_COLOR} !important;
    border-color: {BORDER_COLOR} !important;
    box-shadow: {SHADOW_VAL} !important;
}}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {{
    display: none !important;
}}
[data-baseweb="tab-list"] {{
    gap: 6px !important;
    background: {BG_SUBTLE} !important;
    border: 1px solid {BORDER_COLOR} !important;
    border-radius: 10px !important;
    padding: 4px !important;
    margin-bottom: 1.5rem !important;
}}

/* Sliders */
.stSlider [data-testid="stTickBar"] {{
    display: none !important;
}}

/* Spacing layout override */
[data-testid="stHorizontalBlock"] {{
    gap: 1.4rem !important;
}}
</style>
"""
st.markdown(css_style, unsafe_allow_html=True)

# --- SIDEBAR GLOBAL NAVIGATION & CONTROL PANEL ---
with st.sidebar:
    st.markdown(f"""
    <div style="text-align: center; padding: 0.8rem 0;">
        <span style="font-size: 1.5rem; font-weight: 800; background: linear-gradient(135deg, #6366f1, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.04em;">◆ TalentGraph AI</span>
        <div style="font-size: 0.68rem; color: #9ca3af; font-weight: 600; text-transform: uppercase; margin-top: 4px; letter-spacing: 0.05em;">SYSTEM MANAGEMENT PORTAL</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 0.8rem 0; border: none; border-top: 1px solid " + BORDER_COLOR + ";'>", unsafe_allow_html=True)
    
    # 1. API status widget
    status_lbl = "Connected" if API_ONLINE else "API Offline (Local Mode)"
    status_class = "badge-green" if API_ONLINE else "badge-amber"
    st.markdown(f"""
    <div style="padding: 0.85rem; background-color: {BG_SUBTLE}; border: 1px solid {BORDER_COLOR}; border-radius: 8px; margin-bottom: 1rem;">
        <div style="font-size: 0.7rem; color: #9ca3af; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em;">Active Host Connection</div>
        <div style="margin-top: 0.4rem;">
            <span class="badge {status_class}">{status_lbl}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. Database seed options
    st.markdown("##### Registry Administration")
    st.write("Clean-slate import of standard candidates and jobs datasets:")
    if st.button("📥 Load Sample Datasets", use_container_width=True):
        with st.spinner("Seeding database..."):
            if load_sample_dataset():
                st.success("Sample data seeded!")
                st.rerun()
                
    st.markdown("<hr style='margin: 0.8rem 0; border: none; border-top: 1px solid " + BORDER_COLOR + ";'>", unsafe_allow_html=True)
    
    # 3. Export tools
    st.markdown("##### Pipeline Tools")
    st.write("Export composite rankings to local filesystem format:")
    if st.button("💾 Export Rankings to JSON", use_container_width=True):
        with st.spinner("Writing data/final_rankings.json..."):
            try:
                import subprocess
                subprocess.run(["python", "scripts/export_rankings.py"])
                st.success("Exported rankings!")
            except Exception as e:
                st.error(f"Export failed: {e}")

# --- MAIN PAGE HEADER ---
st.markdown(f"""
<div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(168, 85, 247, 0.03)); border: 1px solid {BORDER_COLOR}; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; position: relative; overflow: hidden; animation: fadeIn 0.4s ease-out forwards;">
    <div style="position: absolute; right: -20px; top: -20px; font-size: 8rem; opacity: 0.02; font-weight: 900; color: {ACCENT_COLOR}; pointer-events: none;">TG</div>
    <span style="font-size: 2rem; font-weight: 800; letter-spacing: -0.04em; background: linear-gradient(to right, #6366f1, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">TalentGraph Recruiter Portal</span>
    <div style="font-size: 0.84rem; color: {TEXT_MUTED}; margin-top: 4px;">
        AI-driven candidate retrieval, cross-attention reranking, and semantic skill-ontology alignment.
    </div>
</div>
""", unsafe_allow_html=True)

# --- SYSTEM METRIC KPI CARDS ---
c_kpi1, c_kpi2, c_kpi3 = st.columns(3)
with c_kpi1:
    total_c = len(get_all_candidates())
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Ingested Candidates</div>
        <div class="metric-value">{total_c}</div>
        <div class="metric-delta delta-up">⚡ Active Registry</div>
    </div>
    """, unsafe_allow_html=True)
with c_kpi2:
    total_j = len(get_all_jobs())
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Job Profiles</div>
        <div class="metric-value">{total_j}</div>
        <div class="metric-delta delta-blue">📋 Sourced Configs</div>
    </div>
    """, unsafe_allow_html=True)
with c_kpi3:
    status_lbl = "Connected" if API_ONLINE else "Local Offline"
    status_class = "delta-up" if API_ONLINE else "delta-warn"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">System Mode</div>
        <div class="metric-value">{status_lbl}</div>
        <div class="metric-delta {status_class}">◆ Host API</div>
    </div>
    """, unsafe_allow_html=True)

# --- PLOTLY CHARTS THEME CONFIG ---
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#71717a" if not IS_DARK else "#a1a1aa", size=11),
    margin=dict(l=40, r=20, t=10, b=30),
    xaxis=dict(
        gridcolor="rgba(0,0,0,0.05)" if not IS_DARK else "rgba(255,255,255,0.05)",
        zerolinecolor="rgba(0,0,0,0.05)" if not IS_DARK else "rgba(255,255,255,0.05)",
        tickfont=dict(size=10, color="#71717a"),
    ),
    yaxis=dict(
        gridcolor="rgba(0,0,0,0.05)" if not IS_DARK else "rgba(255,255,255,0.05)",
        zerolinecolor="rgba(0,0,0,0.05)" if not IS_DARK else "rgba(255,255,255,0.05)",
        tickfont=dict(size=10, color="#71717a"),
    ),
)

# --- WORKFLOW TABS ---
tab_ranker, tab_directory, tab_benchmarks = st.tabs([
    "🔍 Job Matching & Ranking",
    "🗂️ Candidate Directory",
    "📊 System Evaluation"
])

# ==========================================
# TAB 1: JOB MATCHING & RANKING
# ==========================================
with tab_ranker:
    # Load available jobs
    existing_jobs = get_all_jobs()
    job_options = ["Create New Job Profile..."] + [f"{j['title']} ({j['job_id']})" for j in existing_jobs]
    
    col_input, col_display = st.columns([1, 2])
    
    with col_input:
        st.markdown(f'<div class="chart-wrap"><div class="chart-title">Job Configuration</div><div class="chart-subtitle">Select or configure requirements</div>', unsafe_allow_html=True)
        
        job_selection = st.selectbox("Active Job Profile", job_options)
        
        selected_job_id = None
        
        # If selecting existing job
        if job_selection != "Create New Job Profile...":
            selected_job_id = job_selection.split("(")[-1].replace(")", "").strip()
            job_details = next(j for j in existing_jobs if j["job_id"] == selected_job_id)
            
            st.text_input("Job Title", value=job_details["title"], disabled=True)
            st.text_input("Seniority Requirement", value=job_details["seniority"] or "N/A", disabled=True)
            st.text_input("Location", value=job_details["location"] or "N/A", disabled=True)
            st.text_area("Must-have Skills", value=", ".join(job_details["must_have"]), disabled=True)
            st.text_area("Nice-to-have Skills", value=", ".join(job_details["nice_to_have"]), disabled=True)
        else:
            # Creation form
            new_job_id = st.text_input("Job ID*", value="j3")
            new_title = st.text_input("Job Title*", value="Lead Data Scientist")
            new_seniority = st.selectbox("Seniority Requirement", ["senior", "mid", "junior"])
            new_location = st.text_input("Location Requirement", value="Remote")
            new_must = st.text_area("Must-have Skills (comma separated)*", value="Python, PyTorch, SQL")
            new_nice = st.text_area("Nice-to-have Skills (comma separated)", value="MLOps, GCP")
            new_desc = st.text_area("Raw Job Description*", value="We are looking for a Senior Data Scientist to lead candidate recommendation analytics.")
            
            if st.button("Create and Save Job", use_container_width=True):
                if not new_job_id or not new_title or not new_must or not new_desc:
                    st.error("Please fill in all required (*) fields.")
                else:
                    save_payload = {
                        "id": new_job_id,
                        "title": new_title,
                        "raw_description": new_desc,
                        "must_have_skills": [s.strip() for s in new_must.split(",") if s.strip()],
                        "nice_to_have_skills": [s.strip() for s in new_nice.split(",") if s.strip()],
                        "seniority": new_seniority,
                        "location": new_location
                    }
                    result = add_job(save_payload)
                    st.success(f"Job '{new_title}' successfully created!")
                    st.rerun()
        
        # Pipeline tunables
        st.markdown("<hr style='margin: 1rem 0; border: none; border-top: 1px solid " + BORDER_COLOR + ";'>", unsafe_allow_html=True)
        st.markdown("##### Scoring Config")
        alpha = st.slider("Reranker Blend Weight (α)", min_value=0.0, max_value=1.0, value=0.5, step=0.1, help="0.0 = Feature Vector only, 1.0 = Cross-Encoder reranker only")
        top_n = st.slider("Maximum Results (Top N)", min_value=1, max_value=20, value=10)
        
        # Big Rank button
        if st.button("⚡ Sourced & Rank Candidates", type="primary", use_container_width=True, disabled=(selected_job_id is None)):
            with st.spinner("Executing pipeline (Hybrid Retrieval, Feature Scoring, Reranker, Explainability)..."):
                try:
                    rankings = run_ranking(selected_job_id, alpha=alpha, top_n=top_n)
                    st.session_state[f"rankings_{selected_job_id}"] = rankings
                    st.success("Pipeline executed successfully!")
                except Exception as e:
                    st.error(f"Error during ranking pipeline: {e}")
                    
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_display:
        st.markdown(f'<div class="chart-wrap"><div class="chart-title">Ranking Results & Score Breakdowns</div><div class="chart-subtitle">Selected Job Requirements Rank Matrix</div>', unsafe_allow_html=True)
        
        if selected_job_id is None:
            st.info("👈 Select or create a Job Profile to rank candidates.")
        else:
            rank_results = st.session_state.get(f"rankings_{selected_job_id}", None)
            
            # If no current ranking executed, fetch saved ones
            if not rank_results:
                try:
                    # Look up if database has rankings already
                    _, db = get_local_backend()
                    rank_results = db.get_rankings(selected_job_id)
                except Exception:
                    pass
            
            if not rank_results:
                st.warning("⚠️ No rankings exist yet. Click 'Sourced & Rank Candidates' to run the pipeline.")
            else:
                # 1. Highlight Top Candidate Card
                top_cand = rank_results[0]
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.08), rgba(16, 185, 129, 0.02)); border: 1px dashed #10b981; border-radius: 10px; padding: 1.25rem; margin-bottom: 1.5rem; animation: fadeIn 0.4s ease-out forwards;">
                    <span class="badge badge-green" style="margin-bottom: 6px;">👑 TOP MATCH CANDIDATE</span>
                    <div style="font-size: 1.3rem; font-weight: 800; color: {TEXT_COLOR}; margin-top: 2px;">
                        Candidate ID: <span style="font-family: monospace; color: #10b981;">{top_cand['candidate_id']}</span>
                    </div>
                    <div style="font-size: 0.84rem; color: {TEXT_MUTED}; margin-top: 6px; line-height: 1.5;">
                        {top_cand['narrative']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 2. Build HTML Table
                table_rows = ""
                for r in rank_results:
                    tags_html = "".join([f'<span class="badge badge-blue" style="margin-right: 3px; font-size: 0.65rem;">{t}</span>' for t in r["tags"][:2]])
                    table_rows += f"""
                    <tr>
                        <td style="font-weight: 700;">#{r['rank']}</td>
                        <td style="font-family: 'JetBrains Mono', monospace; font-weight: 600; color: {ACCENT_COLOR};">{r['candidate_id']}</td>
                        <td><span style="font-weight: bold;">{r['final_score']:.4f}</span></td>
                        <td>{tags_html}</td>
                        <td><span class="badge badge-green">Matching</span></td>
                    </tr>
                    """
                
                table_html = f"""
                <table class="data-table">
                    <thead>
                        <tr>
                            <th style="width: 10%;">Rank</th>
                            <th style="width: 25%;">Candidate ID</th>
                            <th style="width: 20%;">Composite Score</th>
                            <th style="width: 30%;">Classified Tags</th>
                            <th style="width: 15%;">Match Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
                """
                st.markdown(table_html, unsafe_allow_html=True)
                
                # Active candidate detail selector
                cand_ids = [r["candidate_id"] for r in rank_results]
                st.markdown("<br><h5>Candidate Exploration & AI Justification</h5>", unsafe_allow_html=True)
                selected_cand = st.selectbox("Inspect Candidate Details", cand_ids)
                
                if selected_cand:
                    cand_rank_info = next(r for r in rank_results if r["candidate_id"] == selected_cand)
                    cand_db_info = get_candidate_details(selected_cand)
                    
                    # 3. Tabbed Candidate Inspections
                    cand_tabs = st.tabs([
                        "💬 AI Justification Narrative",
                        "🧩 Skill Requirements Analysis",
                        "🕸️ Multi-Dimensional Fit Chart"
                    ])
                    
                    with cand_tabs[0]:
                        st.markdown(f"**Candidate:** `{selected_cand}` | **Location:** `{cand_db_info.get('location') or 'Remote'}` | **Experience:** `{cand_db_info.get('experience_years') or 0.0} YoE`")
                        
                        st.markdown("<div class='explain-narrative'>", unsafe_allow_html=True)
                        st.markdown(f"**AI Narrative Narrative:**\n\n{cand_rank_info['narrative']}")
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Tags list
                        tag_badges = "".join([f'<span class="badge badge-blue" style="margin-right: 5px; margin-bottom: 5px;">{t}</span>' for t in cand_rank_info["tags"]])
                        st.markdown(f"**Tags:** {tag_badges if tag_badges else '*None*'}", unsafe_allow_html=True)
                    
                    with cand_tabs[1]:
                        # Matched vs Missing list
                        m_col1, m_col2 = st.columns(2)
                        with m_col1:
                            st.markdown("✅ **Matched Competencies**")
                            matched_list = cand_rank_info.get("matched_points") or []
                            if matched_list:
                                st.markdown("\n".join([f"- {pt}" for pt in matched_list]))
                            else:
                                st.markdown("*No specific matched points listed*")
                        with m_col2:
                            st.markdown("⚠️ **Skill & Profile Gaps**")
                            missing_list = cand_rank_info.get("missing_points") or []
                            if missing_list:
                                st.markdown("\n".join([f"- {pt}" for pt in missing_list]))
                            else:
                                st.markdown("*No significant gaps identified*")
                                
                    with cand_tabs[2]:
                        # Display polar radar chart of features
                        f = cand_rank_info["features"]
                        features_names = [
                            "Skills Overlap", "KG Distance", "Dense Similarity",
                            "BM25 Score", "Trajectory Align", "Behavioral Score", "Seniority Match"
                        ]
                        features_values = [
                            f.get("skill_overlap", 0.0), f.get("kg_skill_distance", 0.0),
                            f.get("dense_similarity", 0.0), f.get("bm25_score", 0.0),
                            f.get("trajectory_alignment", 0.5), f.get("behavioral_score", 0.5),
                            f.get("seniority_match", 1.0)
                        ]
                        
                        # Radar Plotly Chart
                        fig = go.Figure(data=go.Scatterpolar(
                            r=features_values,
                            theta=features_names,
                            fill='toself',
                            line_color=ACCENT_COLOR,
                            name=selected_cand
                        ))
                        
                        fig.update_layout(
                            polar=dict(
                                radialaxis=dict(visible=True, range=[0, 1]),
                                bgcolor="rgba(0,0,0,0)",
                            ),
                            showlegend=False,
                            margin=dict(l=30, r=30, t=10, b=10),
                            height=240,
                            paper_bgcolor="rgba(0,0,0,0)",
                        )
                        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                            
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# TAB 2: CANDIDATE DIRECTORY & INGESTION
# ==========================================
with tab_directory:
    st.markdown(f'<div class="chart-wrap"><div class="chart-title">Ingestion Control Center</div><div class="chart-subtitle">Bulk upload resumes and candidates profiles</div>', unsafe_allow_html=True)
    
    col_up1, col_up2 = st.columns([1, 1])
    
    with col_up1:
        st.write("##### Custom Ingestion Upload")
        uploaded_file = st.file_uploader("Upload candidates file (CSV or JSON)", type=["csv", "json"])
        
        if uploaded_file is not None:
            if st.button("⚡ Execute Bulk Upload", use_container_width=True):
                with st.spinner("Processing cleaner and schema validator pipeline..."):
                    # Call API or process local files
                    ext = Path(uploaded_file.name).suffix.lower()
                    try:
                        content = uploaded_file.read()
                        if ext == ".csv":
                            df = pd.read_csv(io.BytesIO(content))
                        else:
                            df = pd.read_json(io.BytesIO(content))
                            
                        # Format list
                        from preprocessing.cleaning import DataCleaner
                        from preprocessing.validation import SchemaValidator
                        cleaner = DataCleaner()
                        validator = SchemaValidator()
                        cleaned = cleaner.clean_candidates(df)
                        valid_df, _ = validator.validate_candidates(cleaned, uploaded_file.name)
                        
                        cand_list = []
                        for _, row in valid_df.iterrows():
                            cand_list.append({
                                "id": row["id"],
                                "raw_resume_text": row["raw_resume_text"],
                                "skills_raw": row.get("skills_raw", []),
                                "experience_years": float(row["experience_years"]) if pd.notna(row["experience_years"]) else 0.0,
                                "location": row.get("location"),
                                "github_url": str(row["github_url"]) if pd.notna(row.get("github_url")) else None,
                                "activity_metadata": row.get("activity_metadata", {})
                            })
                        upload_candidates(cand_list)
                        st.success(f"Successfully processed and uploaded {len(cand_list)} candidates!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to parse or process file: {e}")
                        
    with col_up2:
        st.write("##### Quick Guide")
        st.info("💡 Tip: Use the Sidebar Portal control panel to instantly load standard baseline candidate profiles and seed the database with testing configurations.")
                        
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Render all candidates
    st.markdown(f'<div class="chart-wrap"><div class="chart-title">Ingested Candidates Catalog</div><div class="chart-subtitle">Explore and filter active candidate records in the SQLite registry</div>', unsafe_allow_html=True)
    
    all_candidates = get_all_candidates()
    if not all_candidates:
        st.info("No candidates loaded. Use the controls above to populate candidate data.")
    else:
        cat_l, cat_r = st.columns([5, 3])
        
        with cat_l:
            search_query = st.text_input("🔍 Filter catalog by candidate ID, location, or skills (e.g. Python)", "")
            
            # Filter candidates based on search
            filtered_candidates = []
            for c in all_candidates:
                q = search_query.lower().strip()
                if not q:
                    filtered_candidates.append(c)
                elif (q in c["id"].lower() or 
                      (c.get("location") and q in c["location"].lower()) or 
                      any(q in s.lower() for s in c["skills_raw"])):
                    filtered_candidates.append(c)
            
            if not filtered_candidates:
                st.info("No matching candidates found.")
            else:
                table_rows = ""
                for c in filtered_candidates:
                    skills_badges = "".join([f'<span class="badge badge-blue" style="margin-right: 3px; font-size: 0.65rem; margin-bottom: 2px;">{s}</span>' for s in c["skills_raw"][:4]])
                    if len(c["skills_raw"]) > 4:
                        skills_badges += f'<span class="badge badge-amber" style="font-size: 0.65rem;">+{len(c["skills_raw"]) - 4} more</span>'
                        
                    table_rows += f"""
                    <tr>
                        <td style="font-family: 'JetBrains Mono', monospace; font-weight: 600; color: {ACCENT_COLOR};">{c['id']}</td>
                        <td>{c.get('experience_years') or 0.0} yrs</td>
                        <td>{c.get('location') or 'Remote'}</td>
                        <td>{skills_badges}</td>
                        <td style="font-size: 0.75rem;"><a href="{c.get('github_url')}" target="_blank">{c.get('github_url') or 'N/A'}</a></td>
                    </tr>
                    """
                
                table_html = f"""
                <table class="data-table">
                    <thead>
                        <tr>
                            <th style="width: 20%;">Candidate ID</th>
                            <th style="width: 15%;">Experience</th>
                            <th style="width: 20%;">Location</th>
                            <th style="width: 30%;">Skills</th>
                            <th style="width: 15%;">GitHub</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
                """
                st.markdown(table_html, unsafe_allow_html=True)
                
        with cat_r:
            st.write("##### Core Skill Densities")
            from collections import Counter
            all_skills = []
            for c in all_candidates:
                all_skills.extend(c["skills_raw"])
            
            if all_skills:
                skill_counts = Counter(all_skills).most_common(8)
                skills_df = pd.DataFrame(skill_counts, columns=["Skill", "Count"])
                
                fig_skills = px.bar(
                    skills_df,
                    x="Count",
                    y="Skill",
                    orientation="h",
                    color_discrete_sequence=[ACCENT_COLOR]
                )
                fig_skills.update_layout(
                    PLOT_LAYOUT,
                    margin=dict(l=80, r=20, t=10, b=30),
                    height=260
                )
                # Reverse y-axis to show largest on top
                fig_skills.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_skills, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No skill data available to map.")
                
        # 4. Raw resume / commits details inspector
        st.markdown("<br><hr style='border: none; border-top: 1px solid " + BORDER_COLOR + ";'>", unsafe_allow_html=True)
        st.markdown("##### 📁 Candidate Profile & Behavioral Signal Explorer", unsafe_allow_html=True)
        selected_cand_profile = st.selectbox("Select Candidate to view raw resume & commits timeline", [c["id"] for c in filtered_candidates])
        
        if selected_cand_profile:
            p_info = next(c for c in filtered_candidates if c["id"] == selected_cand_profile)
            
            p_col1, p_col2 = st.columns([5, 3])
            with p_col1:
                st.write("###### Detected Resume Content")
                st.code(p_info["raw_resume_text"], language="text")
            with p_col2:
                st.write("###### Activity & Profile Insights")
                st.markdown(f"**Location:** `{p_info.get('location') or 'Remote'}`")
                st.markdown(f"**Experience:** `{p_info.get('experience_years') or 0.0} Years`")
                if p_info.get("github_url"):
                    st.markdown(f"**GitHub Account:** [Link]({p_info['github_url']})")
                
                # Render GitHub Timeline commit history if available in activity metadata
                meta = p_info.get("activity_metadata", {})
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except Exception:
                        meta = {}
                
                if meta and "timeline" in meta:
                    st.write("**Commit History Timeline:**")
                    timeline_rows = ""
                    for entry in meta["timeline"]:
                        timeline_rows += f"- **{entry.get('date')}**: `{entry.get('count')}` commits in repo `{entry.get('repo')}`\n"
                    st.markdown(timeline_rows)
                else:
                    st.info("No GitHub commit timeline available for this candidate.")
                
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# TAB 3: SYSTEM EVALUATION & BENCHMARKS
# ==========================================
with tab_benchmarks:
    st.markdown(f'<div class="chart-wrap"><div class="chart-title">System Rank Evaluation Benchmark Suite</div><div class="chart-subtitle">NDCG, MRR and Precision Comparisons</div>', unsafe_allow_html=True)
    
    st.write("Compare the scientific performance of the hybrid embedding graph-blend pipeline against standard keyword search baseline methods (Jaccard skill count intersection).")
    
    eval_alpha = st.slider("Evaluation Blend Weight (α)", min_value=0.0, max_value=1.0, value=0.5, step=0.1, key="eval_alpha")
    
    if st.button("⚡ Execute Evaluation Suite (K=3)", use_container_width=True):
        with st.spinner("Calculating performance metrics for all job queries..."):
            eval_results = run_evaluation_benchmark(alpha=eval_alpha)
            
            if eval_results is None:
                st.error("Cannot run benchmarks: Please load the sample dataset first!")
            else:
                metrics_list = []
                base_scores = []
                sys_scores = []
                deltas = []
                
                for res in eval_results:
                    metrics_list.append(res.metric_name)
                    base_scores.append(res.baseline_score)
                    sys_scores.append(res.system_score)
                    deltas.append(res.delta)
                
                # Show results in metric cards
                c_m1, c_m2, c_m3 = st.columns(3)
                for idx, (m_name, base_s, sys_s, delta) in enumerate(zip(metrics_list, base_scores, sys_scores, deltas)):
                    col = [c_m1, c_m2, c_m3][idx]
                    with col:
                        # Metric visual card
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">{m_name}</div>
                            <div class="metric-value">{sys_s:.4f}</div>
                            <div class="metric-delta {'delta-up' if delta > 0 else 'delta-down' if delta < 0 else 'delta-warn'}">
                                {'↑' if delta > 0 else '↓' if delta < 0 else '→'} {delta:+.4f} vs Baseline ({base_s:.4f})
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Visual Bar Chart
                df_chart = pd.DataFrame({
                    "Metric": metrics_list * 2,
                    "Score": base_scores + sys_scores,
                    "System": ["Baseline (Jaccard Overlap)"] * 3 + ["Hybrid Ranker (Ours)"] * 3
                })
                
                fig = px.bar(
                    df_chart,
                    x="Metric",
                    y="Score",
                    color="System",
                    barmode="group",
                    color_discrete_map={
                        "Baseline (Jaccard Overlap)": "#71717a",
                        "Hybrid Ranker (Ours)": ACCENT_COLOR
                    }
                )
                
                fig.update_layout(
                    PLOT_LAYOUT,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    height=300
                )
                
                st.markdown("<br><h5>Performance Comparison Chart</h5>", unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                
    st.markdown("</div>", unsafe_allow_html=True)
