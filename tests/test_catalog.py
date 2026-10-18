"""tools/catalog.py: CATALOG.json matches recipes/, keywords find recipes in English and Japanese, copy never
overwrites."""
import pytest

from tools_path import ROOT
import catalog


def test_the_catalog_is_in_step_with_the_recipes():
    assert catalog.check(catalog.load()) == []


def test_every_recipe_has_both_languages_and_its_own_test():
    recipes = catalog.load()["recipes"]
    assert len(recipes) == 24
    assert {r["name"] for r in recipes if r["language"] == "python"} == {r["name"] for r in recipes if r["language"] == "js"}


@pytest.mark.parametrize(("words", "expected"), [
    (["logged", "in"], "fixtures"), (["ログイン済み"], "fixtures"), (["phone"], "offline-phone"),
    (["スマホ"], "offline-phone"), (["given", "when", "then"], "scenario-e2e"), (["日本語"], "japanese-text"),
    (["table-driven"], "unit-table"), (["一時データベース"], "integration-route-db"), (["sleep"], "flaky-rules"),
    (["mock"], "network-stub"), (["アクセシビリティ"], "a11y-smoke"), (["page", "object"], "e2e-journey"),
    (["factory"], "data-builders"), (["no", "dependencies"], "unit-nodeps"),
])
def test_keywords_find_the_recipe(words, expected):
    assert catalog.find(catalog.load(), words)[0]["name"] == expected


def test_copy_brings_the_files_and_what_they_need_and_never_overwrites(tmp_path):
    recipe = catalog.get(catalog.load(), "e2e-journey", "python")

    copied = {p.name for p in catalog.copy(recipe, tmp_path / "e2e")}

    assert {"tasks_page.py", "test_task_journey.py", "conftest.py", "live_server.py"} <= copied
    with pytest.raises(SystemExit, match="exist already"):
        catalog.copy(recipe, tmp_path / "e2e")


def test_markdown_links_resolve():
    import re
    for md in [*ROOT.glob("*.md"), *ROOT.glob("recipes/**/*.md")]:
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", md.read_text(encoding="utf-8")):
            if "://" not in target and not target.startswith("#"):
                assert (md.parent / target.split("#")[0]).exists(), f"{md}: {target}"
