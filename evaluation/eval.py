import os
import sys
import math
from pydantic import BaseModel, Field
from litellm import completion
from dotenv import load_dotenv

from evaluation.test import TestQuestion, load_tests
from evaluation.rag_core import fetch_context, answer_question
from evaluation.session import session_store

load_dotenv(override=True)

# Ensure litellm's OpenAI provider finds credentials
api_key = os.getenv("OPENROUTER_API_KEY")
base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
if api_key:
    os.environ.setdefault("OPENAI_API_KEY", api_key)
    os.environ.setdefault("OPENAI_BASE_URL", base_url)

MODEL = "gpt-4.1-nano"


class RetrievalEval(BaseModel):
    """Evaluation metrics for retrieval performance."""

    mrr: float = Field(description="Mean Reciprocal Rank")
    ndcg: float = Field(description="Normalized Discounted Cumulative Gain")
    keywords_found: int = Field(description="Keywords found in top-k results")
    total_keywords: int = Field(description="Total keywords to find")
    keyword_coverage: float = Field(description="Percentage of keywords found")


class AnswerEval(BaseModel):
    """LLM-as-a-judge evaluation of answer quality."""

    feedback: str = Field(description="Concise feedback on answer quality")
    accuracy: float = Field(description="Factual correctness 1–5")
    completeness: float = Field(description="Coverage of reference answer 1–5")
    relevance: float = Field(description="Direct relevance to question 1–5")


# ── Metric math (unchanged from original) ─────────────────────────────────────


def calculate_mrr(keyword: str, retrieved_docs: list) -> float:
    keyword_lower = keyword.lower()
    for rank, doc in enumerate(retrieved_docs, start=1):
        if keyword_lower in doc.page_content.lower():
            return 1.0 / rank
    return 0.0


def calculate_dcg(relevances: list[int], k: int) -> float:
    dcg = 0.0
    for i in range(min(k, len(relevances))):
        dcg += relevances[i] / math.log2(i + 2)
    return dcg


def calculate_ndcg(keyword: str, retrieved_docs: list, k: int = 10) -> float:
    keyword_lower = keyword.lower()
    relevances = [
        1 if keyword_lower in doc.page_content.lower() else 0
        for doc in retrieved_docs[:k]
    ]
    dcg = calculate_dcg(relevances, k)
    ideal_relevances = sorted(relevances, reverse=True)
    idcg = calculate_dcg(ideal_relevances, k)
    return dcg / idcg if idcg > 0 else 0.0


# ── Evaluation functions (adapted to accept session_id) ───────────────────────


def evaluate_retrieval(
    test: TestQuestion, session_id: str, k: int = 10
) -> RetrievalEval:
    """
    Evaluate retrieval performance for one test question.
    session_id routes to the correct user vectorstore.
    """
    session = session_store.get(session_id)
    retrieved_docs = fetch_context(test.question, session)

    mrr_scores = [calculate_mrr(kw, retrieved_docs) for kw in test.keywords]
    ndcg_scores = [calculate_ndcg(kw, retrieved_docs, k) for kw in test.keywords]

    avg_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0
    avg_ndcg = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0

    keywords_found = sum(1 for s in mrr_scores if s > 0)
    total_keywords = len(test.keywords)
    keyword_coverage = (
        (keywords_found / total_keywords * 100) if total_keywords > 0 else 0.0
    )

    return RetrievalEval(
        mrr=avg_mrr,
        ndcg=avg_ndcg,
        keywords_found=keywords_found,
        total_keywords=total_keywords,
        keyword_coverage=keyword_coverage,
    )


def evaluate_answer(
    test: TestQuestion, session_id: str
) -> tuple[AnswerEval, str, list]:
    """
    Evaluate answer quality using LLM-as-a-judge.
    session_id routes to the correct user vectorstore.
    """
    session = session_store.get(session_id)
    generated_answer, retrieved_docs = answer_question(test.question, session)

    judge_messages = [
        {
            "role": "system",
            "content": (
                "You are an expert evaluator assessing the quality of RAG answers. "
                "Evaluate the generated answer against the reference answer. "
                "Only give 5/5 scores for perfect answers."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question:\n{test.question}\n\n"
                f"Generated Answer:\n{generated_answer}\n\n"
                f"Reference Answer:\n{test.reference_answer}\n\n"
                "Evaluate on:\n"
                "1. Accuracy (1–5): factual correctness vs reference. Wrong = 1.\n"
                "2. Completeness (1–5): covers all aspects of the reference answer.\n"
                "3. Relevance (1–5): directly answers the question, no off-topic content.\n"
                "Provide feedback and scores."
            ),
        },
    ]

    judge_response = completion(
        model=MODEL,
        messages=judge_messages,
        response_format=AnswerEval,
    )
    answer_eval = AnswerEval.model_validate_json(
        judge_response.choices[0].message.content
    )
    return answer_eval, generated_answer, retrieved_docs


# ── Generator functions (adapted to pass session_id) ──────────────────────────


def evaluate_all_retrieval(session_id: str):
    """Yield (test, RetrievalEval, progress) for all tests in the session."""
    tests = load_tests(session_id)
    total = len(tests)
    for i, test in enumerate(tests):
        result = evaluate_retrieval(test, session_id)
        yield test, result, (i + 1) / total


def evaluate_all_answers(session_id: str):
    """Yield (test, AnswerEval, progress) for all tests in the session."""
    tests = load_tests(session_id)
    total = len(tests)
    for i, test in enumerate(tests):
        result = evaluate_answer(test, session_id)[0]
        yield test, result, (i + 1) / total
