import argparse
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, List

import requests
import yaml
from git import Repo
from pdfminer.high_level import extract_text


ALLOWED_EXTENSIONS = {".md", ".py", ".java", ".go", ".rs", ".php", ".tf"}


def load_config(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("resources", []) if isinstance(data, dict) else []


def clone_repo(url: str, dest: Path) -> Path:
    logging.info("Cloning repo %s to %s", url, dest)
    Repo.clone_from(url, dest)
    return dest


def download_pdf(url: str, dest: Path) -> Path:
    logging.info("Downloading PDF %s to %s", url, dest)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    dest.write_bytes(response.content)
    return dest


def extract_text_from_repo(repo_path: Path) -> str:
    texts = []
    for file in repo_path.rglob("*"):
        if file.suffix.lower() in ALLOWED_EXTENSIONS and file.is_file():
            try:
                texts.append(file.read_text(encoding="utf-8", errors="ignore"))
            except Exception as exc:  # pragma: no cover - log and skip
                logging.error("Failed to read %s: %s", file, exc)
    return "\n".join(texts)


def extract_text_from_pdf(pdf_path: Path) -> str:
    try:
        return extract_text(str(pdf_path))
    except Exception as exc:
        logging.error("Failed to extract text from %s: %s", pdf_path, exc)
        return ""


def process_resource(resource: Dict[str, str], output_dir: Path) -> bool:
    category_dir = output_dir / resource.get("category", "uncategorized")
    os.makedirs(category_dir, exist_ok=True)
    name = resource.get("name") or Path(resource.get("url", "")).stem
    output_file = category_dir / f"{name}.txt"

    try:
        if resource.get("type") == "github":
            with tempfile.TemporaryDirectory() as tmpdir:
                clone_repo(resource["url"], Path(tmpdir))
                text = extract_text_from_repo(Path(tmpdir))
        elif resource.get("type") == "pdf":
            with tempfile.TemporaryDirectory() as tmpdir:
                pdf_path = Path(tmpdir) / "file.pdf"
                download_pdf(resource["url"], pdf_path)
                text = extract_text_from_pdf(pdf_path)
        else:
            logging.error("Unknown resource type: %s", resource)
            return False
        output_file.write_text(text, encoding="utf-8")
        logging.info("Saved text to %s", output_file)
        return True
    except Exception as exc:
        logging.error("Failed processing %s: %s", resource, exc)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Load resources and extract text")
    parser.add_argument("--config", required=True, help="Path to resources_config.yml")
    parser.add_argument("--output-dir", required=True, help="Directory to save extracted text")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s [%(levelname)s] %(message)s")

    resources = load_config(args.config)
    output_dir = Path(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    success = True
    for resource in resources:
        if not process_resource(resource, output_dir):
            success = False
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
