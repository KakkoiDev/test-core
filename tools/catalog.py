#!/usr/bin/env python3
"""Find a test recipe by name or keyword, read its card, copy its files. Standard library only.

  python3 tools/catalog.py list [--language python|js] [--kind unit|integration|e2e|fixtures|rules]
  python3 tools/catalog.py find WORDS...            # English or Japanese keywords: find "logged in", find ログイン
  python3 tools/catalog.py show NAME --language python|js     # print the card
  python3 tools/catalog.py copy NAME --language python|js --out DIR   # copy the files (and what they need)
  python3 tools/catalog.py check                     # CATALOG.json matches recipes/ (CI runs this)
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "CATALOG.json"


def load() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def fold(text: str) -> str:
    return unicodedata.normalize("NFKC", text).lower()


def score(recipe: dict, words: list[str]) -> int:
    haystack = [recipe["name"], recipe["purpose"], recipe["kind"], recipe["tool"], *recipe["keywords"]["en"], *recipe["keywords"]["ja"]]
    haystack = [fold(h) for h in haystack]
    total = 0
    for word in (fold(w) for w in words if not (w.isascii() and len(w) < 3)):  # skip "in", "a", "of"
        if word == fold(recipe["name"]):
            total += 10
        total += sum(3 if word == h else 1 for h in haystack if word in h)
    return total


def find(catalog: dict, words: list[str], language: str | None = None) -> list[dict]:
    phrase = " ".join(words)
    ranked = [(score(r, [phrase]) * 2 + score(r, words), r) for r in catalog["recipes"] if language in (None, r["language"])]
    best = max((s for s, _ in ranked), default=0)
    return [r for s, r in sorted(ranked, key=lambda pair: -pair[0]) if s > 0 and s * 3 >= best]


def get(catalog: dict, name: str, language: str) -> dict:
    for recipe in catalog["recipes"]:
        if recipe["name"] == name and recipe["language"] == language:
            return recipe
    names = sorted({r["name"] for r in catalog["recipes"]})
    raise SystemExit(f"No recipe {name!r} in {language}. Recipes: {', '.join(names)}")


def copy(recipe: dict, out: Path) -> list[Path]:
    """Copy the recipe's files and the shared files they need into `out`, flat. Never overwrites."""
    sources = [ROOT / f for f in recipe["files"] + recipe["needs"]]
    targets = [out / src.name for src in sources]
    clashes = [t for t in targets if t.exists()]
    if clashes:
        raise SystemExit("Not copied, these files exist already: " + ", ".join(str(c) for c in clashes))
    out.mkdir(parents=True, exist_ok=True)
    for src, target in zip(sources, targets):
        shutil.copy2(src, target)
    return targets


def check(catalog: dict) -> list[str]:
    problems = []
    seen = set()
    for recipe in catalog["recipes"]:
        key = (recipe["name"], recipe["language"])
        if key in seen:
            problems.append(f"duplicate recipe {key}")
        seen.add(key)
        for field in ("name", "language", "kind", "tool", "purpose", "card", "files", "test"):
            if not recipe.get(field):
                problems.append(f"{key}: missing {field}")
        if not recipe.get("keywords", {}).get("en") or not recipe.get("keywords", {}).get("ja"):
            problems.append(f"{key}: needs English and Japanese keywords")
        for path in [recipe["card"], *recipe["files"], *recipe.get("needs", [])]:
            if not (ROOT / path).is_file():
                problems.append(f"{key}: missing file {path}")
        if not any(Path(f).name.startswith("test_") or ".test." in f or ".spec." in f or ".nodetest." in f for f in recipe["files"]):
            problems.append(f"{key}: has no test file of its own")
    for folder in sorted((ROOT / "recipes").glob("*/*/")):
        if folder.parent.name == "shared" or folder.name.startswith(("_", ".")):
            continue
        if (folder.name, folder.parent.name) not in seen:
            problems.append(f"recipes/{folder.parent.name}/{folder.name} is not in CATALOG.json")
        listed = {f for r in catalog["recipes"] if (r["name"], r["language"]) == (folder.name, folder.parent.name) for f in r["files"]}
        for file in folder.iterdir():
            rel = str(file.relative_to(ROOT))
            if file.is_file() and file.name != "README.md" and rel not in listed and file.suffix in (".py", ".js"):
                problems.append(f"{rel} is not listed in its recipe's files")
    names = {name for name, _ in seen}
    for name in names:
        languages = {language for n, language in seen if n == name}
        if languages != {"python", "js"}:
            problems.append(f"{name}: has {sorted(languages)}, both python and js expected")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("list")
    p.add_argument("--language", choices=["python", "js"])
    p.add_argument("--kind")
    p = sub.add_parser("find")
    p.add_argument("words", nargs="+")
    p.add_argument("--language", choices=["python", "js"])
    p = sub.add_parser("show")
    p.add_argument("name")
    p.add_argument("--language", choices=["python", "js"], required=True)
    p = sub.add_parser("copy")
    p.add_argument("name")
    p.add_argument("--language", choices=["python", "js"], required=True)
    p.add_argument("--out", type=Path, required=True)
    sub.add_parser("check")
    args = parser.parse_args(argv)
    catalog = load()

    if args.command == "list":
        for r in catalog["recipes"]:
            if args.language in (None, r["language"]) and args.kind in (None, r["kind"]):
                print(f"{r['name']:<22} {r['language']:<7} {r['kind']:<12} {r['purpose']}")
        return 0
    if args.command == "find":
        found = find(catalog, args.words, args.language)
        for r in found[:6]:
            print(f"{r['name']:<22} {r['language']:<7} {r['purpose']}  ->  {r['card']}")
        if not found:
            print("No recipe matches. `python3 tools/catalog.py list` shows them all.")
        return 0 if found else 1
    if args.command == "show":
        recipe = get(catalog, args.name, args.language)
        print((ROOT / recipe["card"]).read_text(encoding="utf-8"))
        print(f"Run its tests: {recipe['test']}")
        return 0
    if args.command == "copy":
        for target in copy(get(catalog, args.name, args.language), args.out):
            print(f"copied {target}")
        return 0
    problems = check(catalog)
    for problem in problems:
        print(problem)
    print(f"CATALOG.json: {len(catalog['recipes'])} recipes, " + ("all in step." if not problems else f"{len(problems)} problem(s)."))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
