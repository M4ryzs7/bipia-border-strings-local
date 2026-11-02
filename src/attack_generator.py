import json
import random
from pathlib import Path
from nltk.tokenize.punkt import PunktSentenceTokenizer

def load_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows

def load_attacks(path):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    flat = {}
    for category, prompts in raw.items():
        for i, prompt in enumerate(prompts):
            flat[f"{category}-{i}"] = prompt
    return flat

def inject(context, attack, position, seed=2023):
    if position == "start":
        return "\n".join([attack, context])

    if position == "end":
        return "\n".join([context, attack])

    if position == "middle":
        spans = list(PunktSentenceTokenizer().span_tokenize(context))

        if not spans:
            raise ValueError("No sentence boundaries found for middle injection.")

        start, _ = random.Random(seed).sample(spans, k=1)[0]

        return "\n".join([context[:start], attack, context[start:]])

    raise ValueError(f"Unknown position: {position}")

def build_samples(email_path, attack_path, email_count=2, categories=None, prompts_per_category=1):
    emails = load_jsonl(email_path)[:email_count]
    attacks = load_attacks(attack_path)
    if categories is None:
        categories = [
            "Task Automation", "Base Encoding", "Information Dissemination",
            "Scams & Fraud", "Misinformation & Propaganda"
        ]
    selected = {}
    for category in categories:
        for i in range(prompts_per_category):
            key = f"{category}-{i}"
            if key in attacks:
                selected[key] = attacks[key]
    samples = []
    for email_idx, email in enumerate(emails):
        for attack_name, attack_text in selected.items():
            for position in ("start", "middle", "end"):
                samples.append({
                    "email_index": email_idx,
                    "question": email["question"],
                    "ideal": email["ideal"],
                    "original_context": email["context"],
                    "attack_name": attack_name,
                    "attack_text": attack_text,
                    "position": position,
                    "poisoned_context": inject(email["context"], attack_text, position, seed=2023)
                })
    return samples
