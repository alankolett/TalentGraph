import json
import sys
from argparse import ArgumentParser
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from feature_engineering.behavioral import BehavioralSignalExtractor, SignalNormalizer
from preprocessing.models import CandidateRecord


def main() -> None:
    parser = ArgumentParser(description="Run Phase 7 Behavioral Signal Engineering.")
    parser.add_argument(
        "--processed-dir",
        default="data/processed",
        help="Directory containing candidates.parquet.",
    )
    parser.add_argument(
        "--output-path",
        default="data/processed/behavioral_profiles.jsonl",
        help="Output JSONL path for profiles.",
    )
    args = parser.parse_args()

    processed_dir = Path(args.processed_dir)
    output_path = Path(args.output_path)

    candidates_path = processed_dir / "candidates.parquet"
    if not candidates_path.exists():
        print(f"Error: {candidates_path} does not exist. Run Phase 2 first.")
        sys.exit(1)

    df = pd.read_parquet(candidates_path)
    records = [CandidateRecord.model_validate(row) for row in df.to_dict(orient="records")]

    extractor = BehavioralSignalExtractor()
    raw_profiles = []
    for record in records:
        profile = extractor.extract_raw_profile(
            candidate_id=record.id,
            metadata=record.activity_metadata,
            github_url=str(record.github_url) if record.github_url else None,
            skills=record.skills,
            career_history=record.career_history,
            experience_years=record.experience_years,
        )
        raw_profiles.append(profile)

    normalizer = SignalNormalizer()
    normalized_profiles = normalizer.normalize_population(raw_profiles)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for profile in normalized_profiles:
            handle.write(json.dumps(profile.model_dump(mode="json"), sort_keys=True) + "\n")

    print(f"Extracted and normalized {len(normalized_profiles)} behavioral profiles.")
    print(f"Profiles written to {output_path}")

    # Display results
    for profile in normalized_profiles:
        print(
            f"  Candidate: {profile.candidate_id} | "
            f"Recency: {profile.recency_score:.3f} | "
            f"Freq: {profile.contribution_frequency:.3f} | "
            f"Velocity: {profile.learning_velocity:.3f} | "
            f"OS Breadth: {profile.open_source_breadth:.3f} | "
            f"Confidence: {profile.signal_confidence:.2f}"
        )


if __name__ == "__main__":
    main()
