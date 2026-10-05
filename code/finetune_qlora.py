#!/usr/bin/env python3
"""Chap. 12 — production-shaped QLoRA run: dataset hash in, evaluated adapter out.

The five steps are trainer-independent (hash → train → export → gate → promote).
Unsloth is the backend used here; the same loop is a YAML config in Axolotl
(`axolotl train config.yml`), a CLI in LLaMA-Factory
(`llamafactory-cli train args.yaml`) or a recipe in torchtune
(`tune run lora_finetune_single_device --config ...`).
Swap the three Unsloth calls for the equivalent ones and the rest is unchanged.

Usage:
    python finetune_qlora.py --data internal_corpus.jsonl --base unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit
"""

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path


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

    model.save_pretrained_gguf(args.out, tokenizer)

    # --- evaluation gate (chap. 16): score the export, block promotion on regression ---
    exports = sorted(Path(args.out).rglob("*.gguf"))
    if not exports:
        sys.exit(f"no GGUF under {args.out} — nothing to gate")
    gate = subprocess.run(
        [sys.executable, "eval_gate.py", "--gguf", str(exports[0])],
        check=False,
    )
    if gate.returncode != 0:
        sys.exit(f"evaluation gate FAILED — not promoted (dataset {data_hash})")

    print(f"[done] promoted {exports[0]} · dataset sha256={data_hash}")


if __name__ == "__main__":
    main()
