# Data directory

Contents here are **git-ignored** — no datasets are committed to the repo.

## Where to put the dataset
Download **Global Superstore** (or Sample Superstore) from Kaggle and save it as:

```
data/raw/global_superstore.csv
```

- Kaggle: https://www.kaggle.com/datasets/apoorvaappz/global-super-store-dataset
- If your column names differ, update `etl.column_map` in `config/config.yaml` — no code changes needed.

## Subfolders
| Folder | Purpose |
|--------|---------|
| `raw/` | Original, untouched source CSVs |
| `interim/` | Partially cleaned intermediates written during ETL |
| `processed/` | Analysis-ready extracts (e.g. monthly series) |
| `external/` | Reference/lookup data (calendars, mappings) |
