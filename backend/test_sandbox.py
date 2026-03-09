"""Smoke test for E2B sandbox executor."""

from dotenv import load_dotenv

load_dotenv()

from sandbox.executor import execute_code

TEST_FILES: list[dict[str, str]] = [
    {
        "filename": "main.py",
        "content": 'print("Hello, World from E2B sandbox!")',
    },
]

TEST_COMMAND = "python main.py"


def main() -> None:
    print("Starting E2B sandbox test...")
    print(f"  Files: {[f['filename'] for f in TEST_FILES]}")
    print(f"  Command: {TEST_COMMAND}")
    print()

    try:
        result = execute_code(files=TEST_FILES, command=TEST_COMMAND)
        print(f"  exit_code: {result['exit_code']}")
        print(f"  stdout:    {result['stdout']!r}")
        print(f"  stderr:    {result['stderr']!r}")
        print()

        if result["exit_code"] == 0 and "Hello, World" in result["stdout"]:
            print("SUCCESS — sandbox executed correctly.")
        else:
            print("FAILURE — unexpected output.")

    except RuntimeError as exc:
        print(f"ERROR: {exc}")


if __name__ == "__main__":
    main()
