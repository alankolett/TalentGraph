from argparse import ArgumentParser
from pathlib import Path

from parsers.pipeline import Phase3Pipeline


def main() -> None:
    parser = ArgumentParser(description="Run Phase 3 resume and job parsing.")
    parser.add_argument(
        "--processed-dir",
        default="data/processed",
        help="Directory containing Phase 2 parquet outputs.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for parsed JSONL outputs. Defaults to processed-dir.",
    )
    args = parser.parse_args()

    result = Phase3Pipeline().run(
        processed_dir=Path(args.processed_dir),
        output_dir=Path(args.output_dir) if args.output_dir else None,
    )
    print(f"parsed_resumes={result.resume_count} -> {result.parsed_resumes_path}")
    print(f"parsed_jobs={result.job_count} -> {result.parsed_jobs_path}")


if __name__ == "__main__":
    main()

