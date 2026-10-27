import sys
import time
import pytest

from openportbench.runtime import run_hard_deadline


def sleep_solver(instance, tools, seconds):
    time.sleep(2)
    return {"noop": True}


def instant_solver(instance, tools, seconds):
    return {"noop": True}


class ToySpec:
    def tools(self, instance):
        return {"is_feasible": lambda sol: (True, None),
                "objective": lambda sol: 7.5}


@pytest.mark.skipif(sys.platform == "win32", reason="Uses fork")
def test_strict_timeout():
    r = run_hard_deadline(ToySpec(), {}, sleep_solver, 0.15)
    assert r["status"] == "TIMEOUT"
    assert r["solution"] is None
    assert r["wall_s"] < 1.5


@pytest.mark.skipif(sys.platform == "win32", reason="Uses fork")
def test_strict_success():
    r = run_hard_deadline(ToySpec(), {}, instant_solver, 1)
    assert r["status"] == "FEASIBLE"
    assert r["objective"] == 7.5
    assert r["solution"] == {"noop": True}


def test_strict_rejects_nonpositive_budget():
    with pytest.raises(ValueError):
        run_hard_deadline(ToySpec(), {}, instant_solver, 0)
