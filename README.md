# OpenStack Troubleshooter -- A Grounded ReAct Agent System

This repository implements a **ReAct (Reasoning +
Acting) agent** designed to troubleshoot complex infrastructure systems
using official documentation as its single source of truth.

The primary use case is **OpenStack troubleshooting**, but the
architecture is framework-agnostic and can be adapted to Kubernetes,
Terraform, AWS, internal enterprise platforms, or any system with
structured documentation.

This is not a retrieval-grounded reasoning engine built on a full ingest → index → retrieve → reason
pipeline.

------------------------------------------------------------------------

# Extending Beyond OpenStack

Although OpenStack is the core use case, this architecture can be
adapted to:

-   Kubernetes diagnostics
-   Terraform troubleshooting
-   Cloud provider documentation agents
-   Internal enterprise documentation assistants

To adapt:

1.  Replace the ingest source
2.  Preserve metadata schema
3.  Rebuild the index
4.  Keep the ReAct loop unchanged

------------------------------------------------------------------------

# End-to-End Pipeline Overview

    Ingest (fetch + normalize docs)
            ↓
    Structured JSONL corpus
            ↓
    Embedding + FAISS indexing
            ↓
    Semantic retrieval (search_docs)
            ↓
    ReAct Agent reasoning loop
            ↓
    Grounded final answer

This repository contains the **entire pipeline**, not just the agent.

------------------------------------------------------------------------

# Repository Structure

    .
    ├── ingest/
    │   ├── admin_docs/
    │   │   └── fetch_admin_docs.py
    │   ├── docs/
    │   │   ├── fetch_openstack_docs.py
    │   │   └── convert_docs_jsonl.py
    │   └── releasenotes/
    │       ├── fetch_releasenotes.py
    │       └── normalize_notes.py
    │
    ├── rag/
    │   ├── search.py
    │   └── build_index.py
    │
    ├── agents/
    │   ├── react_agent.py
    │   └── tools.py
    │
    ├── llm/
    │   └── ollama.py
    │
    ├── data/
    │   ├── raw/
    │   └── processed/
    │
    ├── cli.py
    └── README.md

------------------------------------------------------------------------

# Step 1 -- Ingest Documentation

The `ingest/` layer retrieves and normalizes official OpenStack
documentation.

## Fetch Documentation

``` bash
python ingest/docs/fetch_openstack_docs.py
python ingest/admin_docs/fetch_admin_docs.py
python ingest/releasenotes/fetch_releasenotes.py
```

This retrieves:

-   Core documentation
-   Admin documentation
-   Release notes

All stored in `data/raw/`.

------------------------------------------------------------------------

# Step 2 -- Normalize and Convert

Convert documentation into structured JSONL suitable for indexing:

``` bash
python ingest/docs/convert_docs_jsonl.py
python ingest/releasenotes/normalize_notes.py
```

This stage:

-   Cleans formatting
-   Extracts metadata (service, source, heading)
-   Produces structured chunks
-   Outputs to `data/processed/`

------------------------------------------------------------------------

# Step 3 -- Build the FAISS Index

Generate embeddings and build the vector index:

``` bash
python rag/build_index.py
```

This step:

-   Embeds chunks using `sentence-transformers/all-MiniLM-L6-v2`
-   Builds a FAISS index
-   Saves:
    -   `docs.faiss`
    -   `docs_meta.json`

These are loaded once per process at runtime.

------------------------------------------------------------------------

# Step 4 -- Run the Agent

Basic usage:

``` bash
python cli.py --symptom "VM fails to boot"
```

Service-restricted search:

``` bash
python cli.py --symptom "No valid host found" --service nova
```

The agent:

1.  Generates reasoning (Thought)
2.  Calls `search_docs()`
3.  Injects documentation excerpts
4.  Forces grounded synthesis
5.  Returns a final answer strictly based on evidence

------------------------------------------------------------------------

# Grounding Guarantees

The system enforces:

-   Must search before answering
-   Maximum two searches
-   Must reference retrieved evidence
-   Cannot produce Final without evidence
-   Cannot fall back to generic knowledge
-   Cannot invent configuration details

If documentation does not support a conclusion, the agent explicitly
states so.

------------------------------------------------------------------------

# Performance Design

-   Embedding model loads once per process
-   FAISS index loads once
-   No repeated reinitialization
-   Efficient retrieval per query

------------------------------------------------------------------------

# Requirements

-   Python 3.10+
-   FAISS
-   sentence-transformers
-   requests
-   Ollama (local LLM runtime)

Install:

``` bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run Ollama:

``` bash
ollama run qwen2.5:14b
```

------------------------------------------------------------------------

# Design Principles

-   Deterministic over clever
-   Grounded over fluent
-   Transparent reasoning
-   Tool-driven architecture
-   Clean separation of ingest, retrieval, and reasoning layers