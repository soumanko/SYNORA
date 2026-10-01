# Narrative Intelligence Engine - Architecture

## Overview
The Narrative Intelligence Engine is a two-agent system powered by a unified core for narrative analysis, based on the research from StoryScope. 

## System Components
1. **Narrative Intelligence Core**: Shared engine for taxonomy parsing, feature extraction, classification, and diagnostics.
2. **Narrative Forge**: An agent for generating and iteratively revising text based on core diagnostic signals.
3. **Narrative Lens**: An agent for transparent narrative profiling and authorship analysis.

## Core Design Principles
- ONE reusable core engine (no duplication between agents).
- The taxonomy and StoryScope artifacts form the source of truth.
- Core 30 feature fast-path for iterative generation, Full 304 feature path for deep reporting.
- Evidence-backed extraction with exact document offsets.
- Classification is presented probabilistically and comparatively, never as an absolute truth.
