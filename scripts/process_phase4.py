import sys
from argparse import ArgumentParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from knowledge_graph.pipeline import Phase4Pipeline


def main() -> None:
    parser = ArgumentParser(description="Run Phase 4 skill ontology and knowledge graph build.")
    parser.add_argument(
        "--processed-dir",
        default="data/processed",
        help="Directory containing Phase 3 parsed JSONL outputs.",
    )
    parser.add_argument(
        "--graph-dir",
        default="data/knowledge_graph",
        help="Directory for ontology and graph outputs.",
    )
    args = parser.parse_args()

    result = Phase4Pipeline().run(Path(args.processed_dir), Path(args.graph_dir))
    print(f"ontology -> {result.ontology_path}")
    print(f"graph -> {result.graph_path}")
    print(f"nodes={result.node_count} edges={result.edge_count}")


if __name__ == "__main__":
    main()
