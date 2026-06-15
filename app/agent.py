from __future__ import annotations

import time
from dataclasses import dataclass

from . import metrics
from .mock_llm import FakeLLM
from .mock_rag import retrieve
from .pii import hash_user_id, summarize_text
from .tracing import langfuse_context, observe


@dataclass
class AgentResult:
    answer: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float


@observe(name="rag.retrieve")
def traced_retrieve(message: str) -> list[str]:
    docs = retrieve(message)

    langfuse_context.update_current_observation(
        metadata={
            "doc_count": len(docs),
            "query_preview": summarize_text(message),
        }
    )

    return docs


@observe(name="llm.generate")
def traced_llm_generate(llm: FakeLLM, prompt: str):
    response = llm.generate(prompt)

    langfuse_context.update_current_observation(
        metadata={
            "prompt_preview": summarize_text(prompt),
        },
        usage_details={
            "input": response.usage.input_tokens,
            "output": response.usage.output_tokens,
        },
    )

    return response


class LabAgent:
    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.model = model
        self.llm = FakeLLM(model=model)

    @observe(name="agent.run")
    def run(
        self,
        user_id: str,
        feature: str,
        session_id: str,
        message: str,
    ) -> AgentResult:
        started = time.perf_counter()

        langfuse_context.update_current_trace(
            user_id=hash_user_id(user_id),
            session_id=session_id,
            tags=["lab", feature, self.model],
            metadata={
                "feature": feature,
                "model": self.model,
                "message_preview": summarize_text(message),
            },
        )

        docs = traced_retrieve(message)

        prompt = f"Feature={feature}\nDocs={docs}\nQuestion={message}"

        response = traced_llm_generate(self.llm, prompt)

        quality_score = self._heuristic_quality(
            message,
            response.text,
            docs,
        )

        latency_ms = int((time.perf_counter() - started) * 1000)

        cost_usd = self._estimate_cost(
            response.usage.input_tokens,
            response.usage.output_tokens,
        )

        langfuse_context.update_current_observation(
            metadata={
                "doc_count": len(docs),
                "query_preview": summarize_text(message),
                "quality_score": quality_score,
                "latency_ms": latency_ms,
                "cost_usd": cost_usd,
            },
            usage_details={
                "input": response.usage.input_tokens,
                "output": response.usage.output_tokens,
            },
        )

        metrics.record_request(
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            quality_score=quality_score,
        )

        return AgentResult(
            answer=response.text,
            latency_ms=latency_ms,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            cost_usd=cost_usd,
            quality_score=quality_score,
        )

    def _estimate_cost(
        self,
        tokens_in: int,
        tokens_out: int,
    ) -> float:
        input_cost = (tokens_in / 1_000_000) * 3
        output_cost = (tokens_out / 1_000_000) * 15
        return round(input_cost + output_cost, 6)

    def _heuristic_quality(
        self,
        question: str,
        answer: str,
        docs: list[str],
    ) -> float:
        score = 0.5

        if docs:
            score += 0.2

        if len(answer) > 40:
            score += 0.1

        question_tokens = question.lower().split()

        if question_tokens and any(
            token in answer.lower()
            for token in question_tokens[:3]
        ):
            score += 0.1

        if "[REDACTED" in answer:
            score -= 0.2

        return round(max(0.0, min(1.0, score)), 2)