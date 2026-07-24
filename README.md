# Every Bottle Back — Customer Growth Dashboard

A lightweight, interactive dashboard built with Streamlit, Pandas, and Plotly,
showing customer growth trends for Every Bottle Back (July 2025 – May 2026),
with a separate historical context panel covering 2022–2025.

## Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints (usually http://localhost:8501).

## Deploy it as a hosted web app (free)

1. Push this folder to a GitHub repo (public or private).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **New app**, pick the repo/branch, and set the main file to `app.py`.
4. Deploy — you'll get a public URL you can share or open on your phone.

The app is responsive by default: on a phone, the column layouts stack
vertically automatically.

## Project structure

```
ebb-dashboard/
├── app.py                          # Streamlit app (sidebar filters + live charts)
├── requirements.txt
├── data/
│   ├── enriched_transactions.csv   # Row-level, filterable: Jul 2025 - May 2026
│   │                                 (material type, segment, region joined in)
│   └── historical_context.csv      # Legacy system, 2022 - Jun 2025 (unfiltered panel)
```

## Filters

The sidebar lets you filter the whole dashboard live by:
- **Month range** — any window within Jul 2025–May 2026
- **Material type** — PET, HDPE, LDPE, Aluminium, Tetra Pak, Glass, Other
- **Customer segment** — Corporate, School, Hobby, Occasional Recycler, etc.
- **Region** — only affects the charts that use matched contact records (~27% coverage)

All KPIs, charts, and the segment/material breakdowns update live from these filters.
The historical context panel intentionally ignores filters since it's a separate,
non-comparable data source.

## Known data limitations (for your report)

- **System migration**: Every Bottle Back's tracking moved from a manual log
  (Simple Count, 2022–mid 2025) to an accounting/collection system (Jul 2025
  onward). The two are not directly comparable, so growth KPIs are scoped to
  the reliable Jul 2025–May 2026 window; the older data is shown separately
  as historical context.
- **Missing recent months**: source data available at build time ran through
  May 2026 — June/July 2026 were not yet exported.
- **Partial region/channel coverage**: only ~27% of active customers in the
  main window have a matching contact record with region/acquisition-channel
  data, so those two charts are directional rather than complete.
- **Name-based matching**: customers are joined across files by normalized
  name (lowercase, trimmed). This achieved a 98.5% match rate against the
  customer master list, but is not a guaranteed-unique identifier.
