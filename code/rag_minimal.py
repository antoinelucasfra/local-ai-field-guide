#!/usr/bin/env python3
"""Chap. 13 — minimal local RAG: sqlite-vec store + bge-m3 embeddings.

Usage:
    python rag_minimal.py index ./docs/*.md
    python rag_minimal.py ask "How do I reset my VPN token?"
"""

import argparse
import glob
import sqlite3
import sys

import sqlite_vec  # type: ignore[import-not-found]
from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]

MODEL = "BAAI/bge-m3"
DB = "docs.db"


def embed(db, model, text):
    return model.encode(text).tolist()


def cmd_index(paths):
    model = SentenceTransformer(MODEL)
    db = sqlite3.connect(DB)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING vec0(embedding float[1024], text text)"
    )
    n = 0
    for pattern in paths:
        for path in glob.glob(pattern):
            # ponytail: whole-file chunks; split on headings if docs exceed ~800 tokens
            try:
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
            except OSError as e:
                print(f"skip {path}: {e}")
                continue
            db.execute(
                "INSERT INTO chunks(embedding, text) VALUES (?, ?)",
                (embed(db, model, text), text),
            )
            n += 1
    db.commit()
    print(f"indexed {n} documents into {DB}")


def cmd_ask(question, k=4):
    model = SentenceTransformer(MODEL)
    db = sqlite3.connect(DB)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    rows = db.execute(
        """SELECT text, distance FROM chunks WHERE embedding MATCH ?
           ORDER BY distance LIMIT ?""",
        (embed(db, model, question), k),
    ).fetchall()
    context = "\n---\n".join(t for t, _ in rows)

    # llama-cpp-python is an optional runtime dep (see code/README.md); the
    # lazy import keeps sqlite-vec retrieval usable without it.
    from llama_cpp import Llama  # type: ignore[import-not-found]

    llm = Llama.from_pretrained(
        repo_id="unsloth/Qwen3-8B-GGUF",
        filename="*UD-Q4_K_XL.gguf",
        n_ctx=8192,
        verbose=False,
    )
    out = llm.create_chat_completion(
        messages=[
            {
                "role": "system",
                "content": "Answer ONLY from the context. Cite which passage. Say 'not in the documents' otherwise.",
            },
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
        temperature=0.2,
    )
    print(out["choices"][0]["message"]["content"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("index")
    p1.add_argument("paths", nargs="+")
    p2 = sub.add_parser("ask")
    p2.add_argument("question")
    args = ap.parse_args()

    if args.cmd == "index":
        cmd_index(args.paths)
    else:
        try:
            cmd_ask(args.question)
        except FileNotFoundError:
            sys.exit(f"no index at {DB} — run `rag_minimal.py index` first")
