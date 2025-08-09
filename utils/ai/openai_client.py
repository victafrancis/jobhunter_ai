# utils/ai/openai_client.py
import os, time
from typing import Dict, Any, List, Tuple
from openai import OpenAI
from utils.ai.model_router import choose_model, Task
from utils.config.pricing import compute_cost
from utils.ai.cost_logger import log_call

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def call_gpt(
    task: Task,
    messages: List[Dict[str, str]],
    **kwargs
) -> Tuple[str, Dict[str, Any]]:
    """
    Returns (text, meta). meta includes model, tokens, cost, latency.
    """
    model = choose_model(task)
    t0 = time.time()

    resp = _client.chat.completions.create(
        model=model,
        messages=messages,
        **kwargs
    )

    text = resp.choices[0].message.content or ""
    usage = getattr(resp, "usage", None)
    prompt_toks = getattr(usage, "prompt_tokens", 0) if usage else 0
    completion_toks = getattr(usage, "completion_tokens", 0) if usage else 0
    total_toks = getattr(usage, "total_tokens", prompt_toks + completion_toks)
    cost = compute_cost(model, prompt_toks, completion_toks)
    latency = round(time.time() - t0, 3)

    meta = {
        "model": model,
        "prompt_tokens": prompt_toks,
        "completion_tokens": completion_toks,
        "total_tokens": total_toks,
        "cost_usd": cost,
        "latency_s": latency,
    }

    # Console log for quick dev feedback
    print(f"[GPT] task={task} model={model} tokens={total_toks} cost=${cost} latency={latency}s")
    # Persist to CSV
    log_call(task, meta)

    return text, meta
