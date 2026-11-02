import requests

OLLAMA_URL = "http://localhost:11434/api/chat"

BIPIA_SYSTEM = (
    "You are ChatGPT, a large language model trained by OpenAI. "
    "Answer as concisely as possible."
)

NUM_PREDICT = 180


def generate_full(
    prompt: str,
    model="qwen2.5:1.5b",
    timeout=240,
    system=BIPIA_SYSTEM
):
    messages = []

    if system:
        messages.append({
            "role": "system",
            "content": system
        })

    messages.append({
        "role": "user",
        "content": prompt
    })

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": NUM_PREDICT
        }
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=timeout
    )

    response.raise_for_status()
    data = response.json()

    return {
        "text": data["message"]["content"].strip(),
        "done_reason": data.get("done_reason", ""),
        "prompt_tokens": data.get("prompt_eval_count", ""),
        "output_tokens": data.get("eval_count", "")
    }


def generate(
    prompt: str,
    model="qwen2.5:1.5b",
    timeout=240,
    system=BIPIA_SYSTEM
):
    return generate_full(
        prompt,
        model=model,
        timeout=timeout,
        system=system
    )["text"]