# Resource Loader

This project provides a script to load resources from GitHub repositories or PDF files,
extract their text contents and store them as `.txt` files organised by categories.

## Installation

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

Prepare a YAML configuration file `resources_config.yml`:

```yaml
resources:
  - type: github
    url: https://github.com/example/repo.git
    category: code
    name: repo
  - type: pdf
    url: https://example.com/file.pdf
    category: docs
    name: file
```

Run the loader:

```bash
python load_resources.py --config resources_config.yml --output-dir output
```

Extracted text will appear under the `output/` directory in subdirectories for each
category.

## Testing

Run tests with coverage:

```bash
pytest -v --cov=load_resources tests/
```
