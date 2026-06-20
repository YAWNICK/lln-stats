# LLN Dataset Exploration

This folder contains notebooks for exploring the extracted Lange Laufnacht dataset.

Start Jupyter from the repository root with:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --with jupyter jupyter lab notebooks
```

Open `explore_extracted_dataset.ipynb` for a general overview, or `explore_missing_bib_numbers.ipynb` to inspect the 27 rows where `bib_number` is missing.

The notebook loads the raw source files through `lln_stats.extract.extract_all()` and caches the resulting table at `data/extracted/results.parquet`. Delete that parquet file to force a fresh extraction after changing extractor code or source data.
