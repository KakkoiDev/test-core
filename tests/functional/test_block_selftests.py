"""Every generated test block passes its self-test against its App Block's demo markup (the fixture copy of Pi
Workbench's kit/blocks), and a control removed from the markup fails loudly."""
from pathlib import Path

import pytest

from functional import StepFailed
from functional import primitives
from functional.blocks.python import BLOCKS
from functional.blocks.selftest import self_test

KIT = Path(__file__).resolve().parents[1] / "fixtures" / "app-blocks"


@pytest.mark.parametrize("name", sorted(BLOCKS))
def test_the_block_passes_its_self_test(page, name):
    world = self_test(page, BLOCKS[name], kit=KIT)
    assert world.level == "e2e"


def test_a_control_removed_from_the_markup_fails_loudly(page, monkeypatch):
    monkeypatch.setattr(primitives.settings, "timeout", 300)
    module = BLOCKS["LogIn"]
    markup = (KIT / module.DEMO[0]).read_text(encoding="utf-8").replace('data-t="login.signup">Sign Up</a>', 'data-t="login.signup"></a>')
    assert "Sign Up" not in markup
    with pytest.raises(StepFailed, match="LogIn: uses a control that no longer exists: link \"Sign Up\""):
        self_test(page, module, markup=markup)
