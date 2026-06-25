import re
from typing import Any

from parsers.models import ParsedJob


class MetadataFilter:
    """Applies hard metadata filters as a mask to candidate lists."""

    def apply_hard_filters(
        self,
        candidates: list[dict[str, Any]],
        job: ParsedJob,
    ) -> list[dict[str, Any]]:
        """Filter out candidates that fail hard constraints.

        Gracefully ignores missing candidate values to avoid penalizing them.
        """
        # Define synonym sets for must-have skill check relaxation
        SKILL_SYNONYMS = {
            "embeddings-based retrieval systems": {
                "embeddings-based retrieval systems",
                "embeddings",
                "sentence transformers",
                "rag",
                "semantic search",
                "dense retrieval",
                "information retrieval",
                "retrieval",
                "vector search",
                "vector embeddings",
                "bge",
                "e5",
            },
            "vector databases": {
                "vector databases",
                "vector database",
                "qdrant",
                "pinecone",
                "weaviate",
                "milvus",
                "faiss",
                "chroma",
                "chromadb",
                "elasticsearch",
                "opensearch",
            },
            "hybrid search infrastructure": {
                "hybrid search",
                "hybrid search infrastructure",
                "bm25",
                "elasticsearch",
                "opensearch",
                "information retrieval",
                "solr",
                "lucene",
                "retrieval",
            },
            "python": {"python"},
            "evaluation frameworks for ranking systems": {
                "evaluation frameworks for ranking systems",
                "evaluation",
                "ndcg",
                "mrr",
                "map",
                "precision",
                "recall",
                "ranking",
                "learning to rank",
                "recommendation systems",
                "experimentation",
                "a/b testing",
                "a/b test",
            },
        }

        # Delhi NCR cities and other Tier-1 cities allowed for relocation/hybrid
        allowed_relocation = {
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

        passed = []
        for candidate in candidates:
            # support both list of raw dicts or structures containing 'payload'
            payload = candidate.get("payload")
            if payload is None:
                # if candidate doesn't have 'payload' key, treat candidate itself as payload
                payload = candidate

            # 1. Location constraint
            candidate_loc = payload.get("location")
            job_loc = job.location
            if candidate_loc and job_loc:
                c_loc = str(candidate_loc).lower().strip()
                j_loc = str(job_loc).lower().strip()
                if c_loc != j_loc and c_loc != "remote" and j_loc != "remote":
                    # Let's check token overlap
                    c_tokens = set(re.split(r"[\s,/;]+", c_loc))
                    j_tokens = set(re.split(r"[\s,/;]+", j_loc))

                    if not c_tokens.intersection(j_tokens):
                        # Special check: if job location is the Redrob JD "pune/noida, india"
                        # we also allow other Tier-1 relocation cities mentioned in the JD
                        is_redrob_job = "pune" in j_tokens or "noida" in j_tokens
                        if not (is_redrob_job and c_tokens.intersection(allowed_relocation)):
                            continue

            # 2. Seniority-experience constraints
            yoe = payload.get("experience_years")
            if yoe is not None and job.seniority:
                try:
                    yoe_val = float(yoe)
                except (ValueError, TypeError):
                    yoe_val = 0.0

                j_sen = str(job.seniority).lower()
                if any(kw in j_sen for kw in ["senior", "lead", "staff", "principal", "sr"]):
                    if yoe_val < 5.0:
                        continue
                elif "mid" in j_sen:
                    if yoe_val < 3.0:
                        continue

            # 3. Must-have skills constraints
            if job.must_have and payload.get("skills"):
                c_skills = [s.lower().strip() for s in payload.get("skills", [])]
                all_skills_met = True
                for req_skill in job.must_have:
                    req_skill_lower = req_skill.lower().strip()
                    # Resolve synonyms or fallback to required skill itself
                    syn_set = SKILL_SYNONYMS.get(req_skill_lower, {req_skill_lower})

                    has_skill = False
                    for syn in syn_set:
                        syn_lower = syn.lower().strip()
                        if any(
                            syn_lower in c_skill or c_skill in syn_lower
                            for c_skill in c_skills
                        ):
                            has_skill = True
                            break
                    if not has_skill:
                        all_skills_met = False
                        break
                if not all_skills_met:
                    continue

            passed.append(candidate)

        return passed


