from collections import Counter

import networkx as nx


class CareerTrajectoryAnalyzer:
    def compute_trajectory_vector(self, graph: nx.DiGraph, candidate_id: str) -> dict[str, float]:
        candidate_node = f"candidate:{candidate_id}"
        if candidate_node not in graph:
            return {
                "role_count": 0.0,
                "skill_count": 0.0,
                "company_count": 0.0,
                "avg_role_duration_months": 0.0,
            }

        role_nodes = [
            target
            for _, target, data in graph.out_edges(candidate_node, data=True)
            if data.get("kind") == "WORKED_AS"
        ]
        skill_nodes = [
            target
            for _, target, data in graph.out_edges(candidate_node, data=True)
            if data.get("kind") == "HAS_SKILL"
        ]
        companies = Counter()
        durations = []
        for role_node in role_nodes:
            duration = graph.nodes[role_node].get("duration_months")
            if isinstance(duration, int | float):
                durations.append(float(duration))
            for _, company_node, data in graph.out_edges(role_node, data=True):
                if data.get("kind") == "AT_COMPANY":
                    companies[company_node] += 1

        return {
            "role_count": float(len(role_nodes)),
            "skill_count": float(len(set(skill_nodes))),
            "company_count": float(len(companies)),
            "avg_role_duration_months": sum(durations) / len(durations) if durations else 0.0,
        }
