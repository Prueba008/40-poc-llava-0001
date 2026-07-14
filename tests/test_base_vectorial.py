from pathlib import Path

import pytest

from base_vectorial import PromptRepository


def test_upsert_get_search_delete(tmp_path: Path):
    repository = PromptRepository(tmp_path / "prompts.db")
    repository.upsert("p1", "Analizar arquitectura", {"categoria": "arquitectura"}, ["uml", "ia"])
    assert repository.count() == 1
    record = repository.get("p1")
    assert record is not None
    assert record.tags == ("ia", "uml")

    results = repository.search("ARQUITECTURA")
    assert results[0].id == "p1"
    assert results[0].tags == ("ia", "uml")

    assert repository.delete("p1") is True
    assert repository.delete("p1") is False


def test_upsert_replaces_tags(tmp_path: Path):
    repository = PromptRepository(tmp_path / "prompts.db")
    repository.upsert("p1", "Uno", tags=["a", "b"])
    repository.upsert("p1", "Dos", tags=["c"])
    record = repository.get("p1")
    assert record is not None
    assert record.text == "Dos"
    assert record.tags == ("c",)
    assert repository.search("Dos")[0].tags == ("c",)


def test_invalid_values(tmp_path: Path):
    repository = PromptRepository(tmp_path / "prompts.db")
    with pytest.raises(ValueError):
        repository.upsert("", "texto")
    with pytest.raises(ValueError):
        repository.search("x", limit=0)
