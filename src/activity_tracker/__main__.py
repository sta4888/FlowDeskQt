import sys


def main() -> None:
    if "--self-check" in sys.argv[1:]:
        from activity_tracker.selfcheck import run

        raise SystemExit(run())

    from activity_tracker.ui.app import main as run_app

    run_app()


if __name__ == "__main__":
    main()
