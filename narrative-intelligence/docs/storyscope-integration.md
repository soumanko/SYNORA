# StoryScope Repository Integration Plan

## Goal
Integrate the StoryScope artifacts (`taxonomy.json`, `storyscope_features.parquet`, models) cleanly without duplicating the research pipeline.

## Process
1. Download artifacts from the official repository into `narrative-intelligence/data/storyscope/`.
2. Implement `TaxonomyLoader` to dynamically parse `taxonomy.json` and build `Feature` schemas.
3. Implement `Core30Selector` to ingest the feature importance data or official core feature list to dynamically identify the top 30 narrative features.
4. Adapt the encoding pipeline to strictly match the XGBoost (or similar) model inputs specified by StoryScope.

## Limitations
- We will NOT use the full benchmark generation pipeline, only the feature extraction and classification artifacts.
- We rely on their exact feature types (binary, categorical, ordinal, scale, multi-select).
