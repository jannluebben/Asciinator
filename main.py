import json
import os
import sys

COLORS = {
    "red":     "\033[91m",
    "green":   "\033[92m",
    "yellow":  "\033[93m",
    "blue":    "\033[94m",
    "magenta": "\033[95m",
    "cyan":    "\033[96m",
    "white":   "\033[97m",
    "reset":   "\033[0m",
    "bold":    "\033[1m",
    "dim":     "\033[2m",
}

def c(text: str, *styles: str) -> str:
    """Wrap text in ANSI codes. Falls back to plain text if not a TTY."""
    if not sys.stdout.isatty():
        return text
    prefix = "".join(COLORS[s] for s in styles if s in COLORS)
    return f"{prefix}{text}{COLORS['reset']}"


DB_PATH = os.path.join(os.path.dirname(__file__), "db.json")

def load_db(path: str) -> dict:
    if not os.path.exists(path):
        print(c(f"Error: could not find '{path}'.", "red"))
        print(c("Make sure db.json is in the same folder as this script.", "dim"))
        sys.exit(1)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("db.json must contain a JSON object at the top level.")
        return data
    except json.JSONDecodeError as e:
        print(c(f"Error: db.json is not valid JSON — {e}", "red"))
        sys.exit(1)
    except ValueError as e:
        print(c(f"Error: {e}", "red"))
        sys.exit(1)

def build_lookup(db: dict) -> dict[str, list[str]]:
    """Return a flat char→lines mapping (keys like 'a,A' map both variants)."""
    lookup: dict[str, list[str]] = {}
    for key, art in db.items():
        if not isinstance(art, list):
            continue  # skip malformed entries silently
        for alias in key.split(","):
            alias = alias.strip()
            if alias:
                lookup[alias] = art
    return lookup


def render_text(text: str, lookup: dict[str, list[str]]) -> None:
    """Render every character in *text* side-by-side as ASCII art."""
    if not text:
        return

    # Collect the line-lists for each character
    arts: list[tuple[str, list[str]]] = []
    missing: list[str] = []

    for ch in text:
        if ch in lookup:
            arts.append((ch, lookup[ch]))
        else:
            missing.append(repr(ch))

    if missing:
        chars_str = ", ".join(missing)
        print(c(f"⚠  No art found for: {chars_str}", "yellow"))

    if not arts:
        return

    # Normalise heights so we can print side-by-side
    max_height = max(len(lines) for _, lines in arts)
    max_widths  = [max((len(l) for l in lines), default=0) for _, lines in arts]

    SPACING = 2  # blank columns between characters

    padded: list[list[str]] = []
    for (_, lines), width in zip(arts, max_widths):
        col = []
        for i in range(max_height):
            row = lines[i] if i < len(lines) else ""
            col.append(row.ljust(width))
        padded.append(col)

    print()
    for row_idx in range(max_height):
        row = (" " * SPACING).join(col[row_idx] for col in padded)
        print(c(row, "cyan"))
    print()

def print_banner() -> None:
    print(c("═" * 36, "magenta"))
    print(c("  ASCIINATOR  ", "bold", "magenta") + c("v0.5 updated!!", "dim"))
    print(c("  by Joel Ganser & Jann Lübben", "dim"))
    print(c("  Your ASCII Art generator!", "dim"))
    print(c("═" * 36, "magenta"))
    print()

def main() -> None:
    print_banner()

    db     = load_db(DB_PATH)
    lookup = build_lookup(db)

    print(c(f"  {len(lookup)} characters loaded from db.json", "dim"))
    print(c("  Type a letter, word, or sentence.", "dim"))
    print(c("  Enter 'q' or press Ctrl+C to quit.\n", "dim"))

    while True:
        try:
            user_input = input(c("› ", "green")).strip()
        except (KeyboardInterrupt, EOFError):
            print(c("\nBye!", "magenta"))
            break

        if not user_input:
            continue

        if user_input.lower() in {"q", "quit", "exit"}:
            print(c("Bye!", "magenta"))
            break

        render_text(user_input, lookup)


if __name__ == "__main__":
    main()
