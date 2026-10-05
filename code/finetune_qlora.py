#!/usr/bin/env python3
"""Chap. 12 — production-shaped QLoRA run: dataset hash in, evaluated adapter out.

Usage:
    python finetune_unsloth.py --data internal_corpus.jsonl --base unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit
"""

import argparse
import hashlib
import subprocess
import sys


def sha256(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
    except OSError as e:
        raise SystemExit(f"cannot read dataset {path}: {e}") from e
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="JSONL with instruction/output pairs")
    ap.add_argument("--base", default="unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit")
    ap.add_argument("--out", default="gguf/")
    args = ap.parse_args()

    from datasets import load_dataset
    from trl import SFTTrainer
    from unsloth import FastLanguageModel

    data_hash = sha256(args.data)
    print(f"[config] dataset={args.data} sha256={data_hash}")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.base,
        max_seq_length=2048,
        load_in_4bit=True,  # QLoRA
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=load_dataset("json", data_files=args.data)["train"],
        max_seq_length=2048,
    )
    trainer.train()

    # --- evaluation gate (chap. 16): block promotion on regression ---
    gate = subprocess.run(
        [sys.executable, "eval_gate.py", "--adapter-out", args.out],
        check=False,
    )
    if gate.returncode != 0:
        sys.exit(f"evaluation gate FAILED — adapter not promoted (dataset {data_hash})")

    model.save_pretrained_gguf(args.out, tokenizer)
    print(f"[done] GGUF in {args.out} · dataset sha256={data_hash}")


if __name__ == "__main__":
    main()
