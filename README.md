# Editorial Research Assistant — RAG Fix Task

## Task Overview

A digital media company runs a RAG-powered research assistant that helps journalists surface relevant article history and background context. The assistant ingests article chunks nightly into a pgvector database and answers questions through a FastAPI service. Currently, when the system returns wrong or hallucinated answers, engineers have no way to determine whether the fault lies in retrieval (wrong chunks returned) or generation (LLM ignoring good chunks), because no timing or diagnostic data is logged per request. The internal debug endpoint that should help diagnose issues takes over two seconds to respond due to inefficient database access patterns. Additionally, the team has an evaluation dataset but no script to measure retrieval quality, so regressions go undetected.

## Helpful Tips

- Consider what information would let you distinguish a retrieval failure from a generation failure when reading a log line — think about what timestamps and token counts to capture at each stage of the pipeline.
- Review how the debug endpoint loads its data from the database and think about whether all that data needs to be fetched in separate round-trips.
- Explore how recall@5 and MRR are defined and how you would compute them given a CSV of questions with known relevant chunk sources.
- Think about what a safe, informative response should look like when the retriever returns no results above the similarity threshold.

## Objectives

- Each call to POST /api/research/answer produces a structured log line containing retrieval latency, generation latency, prompt token count, and the IDs of the chunks that were selected.
- GET /internal/rag/debug responds in under 500 ms for a request with up to 20 associated chunks and returns paginated results.
- Running python -m app.evaluation against data/eval_queries.csv prints recall@5 and MRR for the current retriever.
- When the retriever finds no chunks above the similarity threshold, the API returns a safe fallback response rather than passing an empty context to the LLM.
- All code follows production standards: typed function signatures, structured exception handling, and no secrets in source files.

## How to Verify

- POST a research question to /api/research/answer and check that the application log (uvicorn.log or stdout) contains a JSON line with keys retrieval_ms, generation_ms, prompt_tokens, and chunk_ids.
- GET /internal/rag/debug?request_id=<id>&page=1&page_size=10 and confirm the response arrives quickly and includes a paginated list of chunk objects.
- Run python -m app.evaluation and confirm it prints recall@5 and MRR values without errors, even if scores are low with the sample data.
- POST a question on a topic not covered by any ingested article and confirm the response contains the fallback message rather than an invented answer.
- Run pytest tests/ and confirm all tests pass.
