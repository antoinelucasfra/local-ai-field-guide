# Companion code — Sovereign Local AI

Runnable companions to the book's recipes. Each file maps to a chapter:

| File | Chapter | What it does |
| --- | --- | --- |
| `finetune_unsloth.py` | 12 · Python path | QLoRA fine-tune → evaluate → export GGUF |
| `eval_gate.py` | 16 · Evaluate | Golden-set regression gate (exit ≠ 0 blocks promotion) |
| `golden_set.template.jsonl` | 16 · Evaluate | Starter schema for your own golden set |
| `rag_minimal.py` | 13 · RAG cookbook | sqlite-vec + bge-m3 minimal retrieval pipeline |
| `Modelfile.example` | 9 · Export & deploy | Ollama persona + sampling wrapper for an exported GGUF |

Requirements: Linux/WSL2, CUDA 12.x, `pip install unsloth sentence-transformers sqlite-vec llama-cpp-python`.

These scripts are starting points, not libraries — read them next to their chapter before running.
