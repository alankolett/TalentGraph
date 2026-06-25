import re
from typing import Any

from parsers.models import ParsedResume


class JDRubricScorer:
    """Evaluates candidates against the JD-specific positive and disqualifying rubric rules."""

    def evaluate_candidate(
        self,
        resume: ParsedResume,
        metadata: dict[str, Any],
        experience_years: float | None,
        github_url: str | None = None,
    ) -> tuple[int, list[str]]:
        """Evaluate a candidate and return (positive_count, disqualifier_flags)."""
        # Collect all text content
        skills_lower = {s.lower().strip() for s in resume.raw_skills}

        # Combine all experience entry descriptions and titles
        exp_texts = []
        titles = []
        companies = []
        for entry in resume.experience_entries:
            desc = entry.description or ""
            title = entry.title or ""
            company = entry.company or ""
            exp_texts.append(f"{title} {company} {desc}".lower())
            titles.append(title.lower())
            companies.append(company.lower())

        full_experience_text = " ".join(exp_texts)

        # ------------------ POSITIVE SIGNALS ------------------
        pos_count = 0

        # 1. Production embeddings/retrieval experience
        has_emb = any(
            kw in full_experience_text or kw in skills_lower
            for kw in [
                "embeddings",
                "sentence transformers",
                "dense retrieval",
                "semantic search",
                "rag",
            ]
        )
        has_prod = any(
            kw in full_experience_text
            for kw in ["production", "deployed", "users", "scale", "infrastructure"]
        )
        if has_emb and has_prod:
            pos_count += 1

        # 2. Production vector-DB/hybrid-search experience
        has_vdb = any(
            kw in full_experience_text or kw in skills_lower
            for kw in [
                "qdrant",
                "pinecone",
                "weaviate",
                "milvus",
                "faiss",
                "chromadb",
                "chroma",
                "elasticsearch",
                "opensearch",
                "hybrid search",
            ]
        )
        if has_vdb and has_prod:
            pos_count += 1

        # 3. Hands-on ranking-evaluation experience
        has_eval = any(
            kw in full_experience_text
            for kw in [
                "ndcg",
                "mrr",
                "map",
                "precision",
                "recall",
                "evaluation",
                "a/b test",
                "ab test",
                "experimentation",
            ]
        )
        if has_eval:
            pos_count += 1

        # 4. India location or relocation willingness
        loc = str(metadata.get("location", "")).lower()
        willing = metadata.get("willing_to_relocate")
        allowed_cities = {
            "pune",
            "noida",
            "hyderabad",
            "mumbai",
            "delhi",
            "ncr",
            "gurgaon",
            "bangalore",
            "bengaluru",
            "chennai",
            "kolkata",
            "ahmedabad",
            "india",
        }
        loc_tokens = set(re.split(r"[\s,/;]+", loc))
        if loc_tokens.intersection(allowed_cities) or willing is True:
            pos_count += 1

        # 5. notice_period_days < 30
        notice = metadata.get("notice_period_days")
        if notice is not None and 0 <= notice < 30:
            pos_count += 1

        # 6. Prior HR-tech/recruiting/marketplace exposure
        has_hr = any(
            kw in full_experience_text
            for kw in [
                "hr-tech",
                "hr tech",
                "recruiting",
                "talent",
                "marketplace",
                "ats",
                "applicant tracking",
                "hiring",
                "job board",
                "matching",
            ]
        )
        if has_hr:
            pos_count += 1

        # 7. Open-source or public validation
        gh_score = metadata.get("github_activity_score", -1)
        has_os = any(
            kw in full_experience_text
            for kw in [
                "open source",
                "open-source",
                "talks",
                "papers",
                "conference",
                "published",
                "arxiv",
                "patent",
            ]
        )
        if (github_url and gh_score > 0) or has_os:
            pos_count += 1

        # ------------------ DISQUALIFYING SIGNALS ------------------
        flags = []

        # 1. Career entirely in academic/research roles with no production
        has_academic_title = any(
            any(
                kw in t
                for kw in [
                    "researcher",
                    "phd",
                    "postdoc",
                    "professor",
                    "academic",
                    "fellow",
                    "student",
                ]
            )
            for t in titles
        )
        if has_academic_title and not has_prod:
            flags.append("disqualifier_academic_only")

        # 2. AI experience under 12 months with no pre-LLM ML production background
        has_llm_only = any(
            kw in skills_lower or kw in full_experience_text
            for kw in ["llm", "langchain", "llamaindex", "openai", "gpt"]
        )
        has_traditional_ml = any(
            kw in skills_lower or kw in full_experience_text
            for kw in [
                "scikit-learn",
                "sklearn",
                "tensorflow",
                "pytorch",
                "keras",
                "xgboost",
                "machine learning",
                "regression",
                "classification",
                "pandas",
                "numpy",
            ]
        )
        yoe_val = experience_years or 0.0
        if has_llm_only and not has_traditional_ml and yoe_val < 1.0:
            flags.append("disqualifier_recent_ai_only")

        # 3. Current title manager/architect/lead with no coding signal
        if titles:
            current_title = titles[0]  # assuming first entry is current
            is_lead = any(
                kw in current_title
                for kw in ["manager", "architect", "lead", "head", "vp", "director"]
            )
            has_coding = False
            if exp_texts:
                has_coding = any(
                    kw in exp_texts[0]
                    for kw in [
                        "code",
                        "coded",
                        "write",
                        "writing",
                        "develop",
                        "implement",
                        "python",
                        "scala",
                        "java",
                        "c++",
                        "hands-on",
                    ]
                )
            if is_lead and not has_coding:
                flags.append("disqualifier_lead_no_coding")

        # 4. Career shows title-escalation / switching roughly every <18 months (job hopper)
        total_months = metadata.get("total_career_months")
        employers = metadata.get("num_employers")
        if total_months and employers:
            avg_tenure = total_months / max(1, employers)
            if avg_tenure < 18.0 and employers >= 3:
                flags.append("disqualifier_job_hopper")

        # 5. Entire career at consulting firms
        consulting_firms = {
            "tcs",
            "infosys",
            "wipro",
            "accenture",
            "cognizant",
            "capgemini",
            "hcl",
            "tech mahindra",
            "l&t",
            "lnt",
            "mindtree",
            "mphasis",
        }
        if companies:
            all_consulting = all(
                any(firm in c for firm in consulting_firms) for c in companies
            )
            if all_consulting:
                flags.append("disqualifier_consulting_only")

        # 6. Computer vision/speech/robotics with no NLP/IR
        has_cv_speech_rob = any(
            kw in skills_lower or kw in full_experience_text
            for kw in [
                "computer vision",
                "opencv",
                "image",
                "cnn",
                "object detection",
                "yolo",
                "speech",
                "asr",
                "tts",
                "audio",
                "robotics",
                "ros",
            ]
        )
        has_nlp_ir = any(
            kw in skills_lower or kw in full_experience_text
            for kw in [
                "nlp",
                "bert",
                "gpt",
                "embeddings",
                "search",
                "retrieval",
                "bm25",
                "elastic",
                "qdrant",
                "text",
                "language",
                "transformers",
                "ir",
                "information retrieval",
                "ranking",
            ]
        )
        if has_cv_speech_rob and not has_nlp_ir:
            flags.append("disqualifier_cv_speech_robotics_only")

        # 7. 5+ years entirely closed source with zero external validation
        if yoe_val >= 5.0 and (gh_score == -1 or gh_score == 0) and not has_os:
            flags.append("disqualifier_closed_source_only")

        return pos_count, flags
