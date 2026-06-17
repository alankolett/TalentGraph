import sys
from argparse import ArgumentParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from embeddings.models import EmbeddingConfig
from embeddings.pipeline import Phase5Pipeline


def main() -> None:
    parser = ArgumentParser(description="Run Phase 5 dense embedding and candidate indexing.")
    parser.add_argument(
        "--processed-dir",
        default="data/processed",
        help="Directory containing Phase 3 parsed JSONL outputs.",
    )
    parser.add_argument(
        "--embeddings-dir",
        default="data/embeddings",
        help="Directory for embedding parquet outputs.",
    )
    parser.add_argument("--dimension", type=int, default=128, help="Embedding dimension.")
    parser.add_argument(
        "--backend",
        choices=["hash", "sentence-transformers"],
        default="hash",
        help="Embedding backend. Use sentence-transformers for real model embeddings.",
    )
    args = parser.parse_args()

    config = EmbeddingConfig(dimension=args.dimension, backend=args.backend)
    result = Phase5Pipeline.from_config(config).run(
        processed_dir=Path(args.processed_dir),
        embeddings_dir=Path(args.embeddings_dir),
    )
    print(f"candidate_embeddings -> {result.candidate_embeddings_path}")
    print(f"job_embeddings -> {result.job_embeddings_path}")
    print(f"indexed_candidates={result.indexed_count}")


if __name__ == "__main__":
    main()
