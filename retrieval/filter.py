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
                    # Mismatch
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
                    # case-insensitive check
                    if not any(
                        req_skill_lower in c_skill or c_skill in req_skill_lower
                        for c_skill in c_skills
                    ):
                        all_skills_met = False
                        break
                if not all_skills_met:
                    continue

            passed.append(candidate)

        return passed
