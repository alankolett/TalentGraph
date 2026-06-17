from argparse import ArgumentParser
from pathlib import Path

from preprocessing.pipeline import Phase2Pipeline


def main() -> None:
    parser = ArgumentParser(description="Run Phase 2 raw dataset cleaning and validation.")
    parser.add_argument(
        "--raw-dir",
        default="data/raw",
        help="Directory containing candidates/jobs files.",
    )
    parser.add_argument("--processed-dir", default="data/processed", help="Output directory.")
    args = parser.parse_args()

    result = Phase2Pipeline().run(Path(args.raw_dir), Path(args.processed_dir))
    print(f"candidates={result.candidate_count} -> {result.candidates_path}")
    print(f"jobs={result.job_count} -> {result.jobs_path}")
    print(f"rejected={result.rejected_count} -> {result.rejected_path}")


if __name__ == "__main__":
    main()
