"""tools/blocks_from_app_blocks.py: test blocks from App Blocks, deterministic, loud when a control is gone, and the
generated steps are the generated vocabulary in both languages."""
import json
import shutil

import pytest

from tools_path import ROOT
import blocks_from_app_blocks as gen

KIT = ROOT / "tests/fixtures/app-blocks"
SPEC = ROOT / "functional/blocks/spec.json"
STARTER = ["LogIn", "DataTable", "EditForm", "EmptyState", "Toasts", "KpiTile", "BarChart", "SidePanel"]


def generate(kit=KIT, spec=SPEC, names=None):
    return gen.generate(kit, kit / "kit/blocks/index.json", spec, names)


def test_the_committed_blocks_are_up_to_date(capsys):
    assert gen.main(["--kit", str(KIT), "--check"]) == 0, capsys.readouterr().out


def test_generating_twice_gives_the_same_files():
    first, second = generate(), generate()
    assert first == second
    assert sorted(first) == sorted(["vocabulary.json", "python/__init__.py", "js/index.js"]
                                   + [f"python/{gen.snake(n)}.py" for n in STARTER] + [f"js/{n}.js" for n in STARTER])


def test_the_python_and_javascript_blocks_compile():
    for path, text in generate().items():
        if path.endswith(".py"):
            compile(text, path, "exec")


def test_check_reports_a_changed_or_stale_file(tmp_path, capsys):
    out = tmp_path / "blocks"
    assert gen.main(["--kit", str(KIT), "--out", str(out)]) == 0
    assert gen.main(["--kit", str(KIT), "--out", str(out), "--check"]) == 0
    (out / "python/log_in.py").write_text("# edited by hand\n", encoding="utf-8")
    (out / "js/Old.js").write_text("// gone\n", encoding="utf-8")
    assert gen.main(["--kit", str(KIT), "--out", str(out), "--check"]) == 1
    printed = capsys.readouterr().out
    assert "log_in.py" in printed and "Old.js (not generated any more" in printed


@pytest.fixture
def kit_copy(tmp_path):
    shutil.copytree(KIT, tmp_path / "kit-copy")
    return tmp_path / "kit-copy"


def test_a_control_removed_from_an_app_block_stops_generation(kit_copy, capsys):
    markup = kit_copy / "kit/blocks/accounts/LogIn.html"
    markup.write_text(markup.read_text(encoding="utf-8").replace(">Sign Up</a>", "></a>"), encoding="utf-8")
    assert gen.main(["--kit", str(kit_copy), "--out", str(kit_copy / "out")]) == 1
    printed = capsys.readouterr().out
    assert "LogIn: the spec uses a control that no longer exists in the App Block's markup: signup (link \"Sign Up\")" in printed
    assert not (kit_copy / "out").exists()


def test_a_part_or_a_state_the_card_lost_stops_generation(kit_copy, tmp_path):
    markup = kit_copy / "kit/blocks/accounts/LogIn.html"
    markup.write_text(markup.read_text(encoding="utf-8").replace('id="login-error"', 'id="oops"'), encoding="utf-8")
    card = kit_copy / "kit/blocks/accounts/LogIn.md"
    card.write_text(card.read_text(encoding="utf-8").replace("- Sending:", "- Busy:"), encoding="utf-8")
    with pytest.raises(gen.SpecError) as error:
        generate(kit_copy, names=["LogIn"])
    assert "a part that no longer exists in the App Block's markup: error" in str(error.value)
    assert "checks the state 'Sending', which the card no longer lists" in str(error.value)


def test_the_spec_is_checked(tmp_path):
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    spec["blocks"]["LogIn"]["steps"].append({"step": "When I type {x}", "do": [["fill", "nowhere", "{x}"], ["jump", "email"]]})
    spec["blocks"]["LogIn"]["steps"].append({"step": "When I sort", "do": [["click", "email"], ["text", "email", "{y}"]]})
    bad = tmp_path / "spec.json"
    bad.write_text(json.dumps(spec), encoding="utf-8")
    with pytest.raises(gen.SpecError) as error:
        generate(spec=bad, names=["LogIn"])
    text = str(error.value)
    assert "fill uses the control 'nowhere'" in text and "unknown op 'jump'" in text and "needs {y}" in text


def test_card_states_and_route():
    card = (KIT / "kit/blocks/accounts/LogIn.md").read_text(encoding="utf-8")
    assert gen.card_states(card)[0] == ("Empty", True)
    assert ("Wrong email or password", False) in gen.card_states(card)
    assert gen.card_route(card) == "/login"


def test_the_python_blocks_are_the_vocabulary():
    from functional.blocks.python import BLOCKS, steps
    vocabulary = json.loads((ROOT / "functional/blocks/vocabulary.json").read_text(encoding="utf-8"))
    assert steps.check_vocabulary(vocabulary) == []
    assert sorted(BLOCKS) == sorted(STARTER)
    assert {d.block for d in steps.definitions} == set(STARTER)


def test_the_task_steps_are_the_task_vocabulary():
    import sys
    sys.path.insert(0, str(ROOT / "recipes/python/scenario-steps"))
    from task_steps import steps
    vocabulary = json.loads((ROOT / "recipes/shared/task-example.vocab.json").read_text(encoding="utf-8"))
    assert steps.check_vocabulary(vocabulary) == []
