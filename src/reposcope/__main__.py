"""Entry point for the reposcope command."""

from reposcope.cli import main

if __name__ == "__main__":
    main()

# This is needed for the entry point
def run_main():
    main()