"""Command-line entrypoint for the data pipeline."""

from eggcup_leaderboard.pipeline import main as run_pipeline


def main() -> int:
    return run_pipeline()


if __name__ == "__main__":
    raise SystemExit(main())
