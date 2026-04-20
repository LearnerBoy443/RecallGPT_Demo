import sys
from types import SimpleNamespace
import KE


def test_main_text_quiet(monkeypatch):
    # Monkeypatch model loader to avoid heavy model download during tests
    class DummyModel:
        def extract_keywords(self, text, **kwargs):
            return [("ai", 0.95), ("machine learning", 0.9)]

    monkeypatch.setattr(KE, "load_models", lambda model_name=None: DummyModel())

    # Basic smoke test: should return 0 and not raise
    rc = KE.main(["--text", "This is a test document about machine learning and AI.", "--top-n", "5", "--quiet"])
    assert rc == 0
