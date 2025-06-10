import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
import os

import pytest

import load_resources as lr


def test_load_config(tmp_path):
    cfg = tmp_path / "config.yml"
    cfg.write_text("""
resources:
  - type: github
    url: https://example.com/repo.git
    category: code
""")
    res = lr.load_config(str(cfg))
    assert res == [{"type": "github", "url": "https://example.com/repo.git", "category": "code"}]


def test_process_resource_repo_success(tmp_path, monkeypatch):
    repo_dir = tmp_path / "repo"

    def fake_clone(url, dest):
        Path(dest).mkdir(parents=True, exist_ok=True)
        (Path(dest) / "file.py").write_text("print('hi')", encoding="utf-8")

    monkeypatch.setattr(lr, "clone_repo", fake_clone)

    out_dir = tmp_path / "out"
    resource = {"type": "github", "url": "https://x/repo.git", "category": "cat", "name": "repo"}
    success = lr.process_resource(resource, out_dir)
    assert success
    output_file = out_dir / "cat" / "repo.txt"
    assert output_file.exists()
    assert "print('hi')" in output_file.read_text(encoding="utf-8")


def test_process_resource_pdf_success(tmp_path, monkeypatch):
    class FakeResponse:
        status_code = 200
        content = b"%PDF-1.4 test pdf"

        def raise_for_status(self):
            pass

    def fake_get(url, timeout=30):
        return FakeResponse()

    monkeypatch.setattr(lr.requests, "get", fake_get)
    monkeypatch.setattr(lr, "extract_text_from_pdf", lambda p: "pdf text")

    out_dir = tmp_path / "out"
    resource = {"type": "pdf", "url": "https://x/doc.pdf", "category": "docs", "name": "doc"}
    success = lr.process_resource(resource, out_dir)
    assert success
    output_file = out_dir / "docs" / "doc.txt"
    assert output_file.exists()
    assert output_file.read_text(encoding="utf-8") == "pdf text"


def test_process_resource_failure(monkeypatch, tmp_path):
    def fake_clone(url, dest):
        raise Exception("clone fail")

    monkeypatch.setattr(lr, "clone_repo", fake_clone)
    resource = {"type": "github", "url": "https://x/repo.git", "category": "c", "name": "r"}
    assert not lr.process_resource(resource, tmp_path)

def test_main_success(tmp_path, monkeypatch):
    cfg = tmp_path / "cfg.yml"
    cfg.write_text("""
resources:
  - type: github
    url: https://example.com/repo.git
    category: cat
    name: repo
""")
    out = tmp_path / "out"

    def fake_process(resource, output_dir):
        return True

    monkeypatch.setattr(lr, "process_resource", fake_process)
    monkeypatch.setattr(sys, "argv", ["prog", "--config", str(cfg), "--output-dir", str(out)])
    assert lr.main() == 0


def test_main_failure(tmp_path, monkeypatch):
    cfg = tmp_path / "cfg.yml"
    cfg.write_text("""
resources:
  - type: github
    url: https://example.com/repo.git
    category: cat
    name: repo
""")
    out = tmp_path / "out"

    def fake_process(resource, output_dir):
        return False

    monkeypatch.setattr(lr, "process_resource", fake_process)
    monkeypatch.setattr(sys, "argv", ["prog", "--config", str(cfg), "--output-dir", str(out)])
    assert lr.main() == 1
