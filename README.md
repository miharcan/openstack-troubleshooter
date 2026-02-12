# Grounded ReAct Framework

A production-grade **retrieval-grounded reasoning framework** built on a
full:

**ingest → index → retrieve → reason** pipeline.

This system implements a deterministic ReAct (Reasoning + Acting) agent
that uses official documentation as its single source of truth.

------------------------------------------------------------------------

## 🚀 Primary Use Case

The current showcase implementation is applied to OpenStack troubleshooting, combining:
- Official OpenStack documentation
- Nova/Neutron admin guides
- GitHub issues and PR discussions

It is capable of:

-   Troubleshooting Nova scheduler failures
-   Diagnosing Placement synchronization issues
-   Explaining Neutron networking misconfigurations
-   Resolving cross-service allocation errors
-   Performing multi-service reasoning across Nova ↔ Neutron ↔ Placement

OpenStack serves as a complex, multi-service validation environment
proving the framework's ability to reason across distributed
infrastructure systems.

However, the architecture is fully framework-agnostic and can be applied to:
-Kubernetes
-Terraform
-AWS
-Internal enterprise platforms
-Any GitHub-backed engineering system
-Any documentation-based software framework

------------------------------------------------------------------------

## 🧠 Framework Capabilities

### 1️⃣ Structured Ingestion

-   Fetch official documentation (HTML, JSON, release notes, admin
    guides)
-   Normalize into chunked, indexed format
-   Preserve service metadata for cross-service reasoning

### 2️⃣ Deterministic Semantic Retrieval

-   FAISS vector search
-   Service-aware ranking
-   Lexical + semantic hybrid boosting
-   Multi-service detection
-   Cross-service evidence grouping

### 3️⃣ ReAct Agent Execution

-   Explicit Thought → Action → Observation → Final loop
-   Tool-restricted reasoning
-   Strict grounding (no hallucinated configs)
-   Multi-hop retrieval capability
-   Cross-service causal explanation enforcement

------------------------------------------------------------------------

## 🏗 Architecture Overview

    ingest/
        fetch → normalize → structure
            ↓
    index/
        embeddings → FAISS index
            ↓
    rag/
        semantic retrieval + ranking intelligence
            ↓
    agents/
        ReAct reasoning engine
            ↓
    cli.py
        grounded troubleshooting interface

------------------------------------------------------------------------

# Architecture

1.  Data ingestion (docs + GitHub)
2.  Embedding generation (SentenceTransformers)
3.  FAISS vector indexing
4.  Intelligent service-aware retrieval
5.  ReAct reasoning loop grounded strictly in retrieved evidence

------------------------------------------------------------------------

# Installation

## 1. Clone Repository

``` bash
git clone https://github.com/<your-username>/grounded-react.git
cd grounded-react
```

## 2. Create Virtual Environment

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install Dependencies

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

# Data Ingestion

## Ingest Official Documentation

Example (OpenStack):

``` bash
python ingest/docs/fetch_openstack_docs.py     --output data/raw/openstack_docs.jsonl
```

Normalize:

``` bash
python ingest/docs/convert_docs_jsonl.py     --input data/raw/openstack_docs.jsonl     --output data/processed/docs_clean.jsonl
```

## Ingest GitHub Issues

Example:

``` bash
python ingest/github/fetch_issues.py     --repo openstack/nova     --output data/raw/github_nova.jsonl
```

Optional: Avoid GitHub rate limits

``` bash
export GITHUB_TOKEN=your_token_here
```

------------------------------------------------------------------------

# Indexing

## Index Documentation

``` bash
python index_docs.py     --input data/processed/docs_clean.jsonl     --index data/processed/index/docs.faiss     --meta data/processed/index/docs_meta.json
```

## Index GitHub Issues

``` bash
python ingest/github/index_github.py     --input data/raw/github_nova.jsonl     --index data/processed/index/docs.faiss     --meta data/processed/index/docs_meta.json
```

The system supports incremental indexing. Documentation and GitHub data
merge into the same FAISS index.

------------------------------------------------------------------------

# Running the Agent

``` bash
python cli.py --symptom "allocation candidates not found"
```

Examples:

``` bash
python cli.py --symptom "OperationalError instance_actions DROP COLUMN"
python cli.py --symptom "how to create security group"
python cli.py --symptom "nova scheduler exception during instance boot"
```

Optional service constraint:

``` bash
python cli.py --symptom "VM fails to boot" --service nova
```

------------------------------------------------------------------------

## 🎯 Design Principles

-   Deterministic behavior over "creative" LLM output
-   Evidence-first explanations
-   Strict retrieval grounding
-   Explicit reasoning trace
-   Framework neutrality
-   Scalable multi-service reasoning

------------------------------------------------------------------------

# License

MIT License