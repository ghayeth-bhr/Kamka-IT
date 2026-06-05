"""
RAG Evaluation Dashboard — dynamic version.

Session flow:
  1. User opens the app → new session_id created, stored in gr.State
  2. User uploads files → ingest_and_generate() runs:
       a. Files are chunked + embedded into the session's vectorstore
       b. LLM generates test questions from the ingested chunks
       c. UI shows test count and list
  3. User clicks "Run Retrieval Evaluation" → runs eval against session's vectorstore
  4. User clicks "Run Answer Evaluation" → same

The two eval sections are unchanged from the original evaluator.
"""

import gradio as gr
import pandas as pd
from collections import defaultdict
from dotenv import load_dotenv

from evaluation.eval import evaluate_all_retrieval, evaluate_all_answers
from evaluation.rag_core import ingest_files
from evaluation.session import session_store
from evaluation.test_generator import generate_tests

load_dotenv(override=True)

# ── Color thresholds (unchanged) ─────────────────────────────────────────────

MRR_GREEN, MRR_AMBER = 0.9, 0.75
NDCG_GREEN, NDCG_AMBER = 0.9, 0.75
COVERAGE_GREEN, COVERAGE_AMBER = 90.0, 75.0
ANSWER_GREEN, ANSWER_AMBER = 4.5, 4.0


def get_color(value: float, metric_type: str) -> str:
    """(unchanged from original)"""
    thresholds = {
        "mrr": (MRR_GREEN, MRR_AMBER),
        "ndcg": (NDCG_GREEN, NDCG_AMBER),
        "coverage": (COVERAGE_GREEN, COVERAGE_AMBER),
        "accuracy": (ANSWER_GREEN, ANSWER_AMBER),
        "completeness": (ANSWER_GREEN, ANSWER_AMBER),
        "relevance": (ANSWER_GREEN, ANSWER_AMBER),
    }
    if metric_type not in thresholds:
        return "black"
    green, amber = thresholds[metric_type]
    if value >= green:
        return "green"
    elif value >= amber:
        return "orange"
    return "red"


def format_metric_html(
    label: str,
    value: float,
    metric_type: str,
    is_percentage: bool = False,
    score_format: bool = False,
) -> str:
    """(unchanged from original)"""
    color = get_color(value, metric_type)
    if is_percentage:
        value_str = f"{value:.1f}%"
    elif score_format:
        value_str = f"{value:.2f}/5"
    else:
        value_str = f"{value:.4f}"
    return f"""
    <div style="margin:10px 0;padding:15px;background:#f5f5f5;border-radius:8px;border-left:5px solid {color};">
        <div style="font-size:14px;color:#666;margin-bottom:5px;">{label}</div>
        <div style="font-size:28px;font-weight:bold;color:{color};">{value_str}</div>
    </div>
    """


# ── NEW: Setup callbacks ──────────────────────────────────────────────────────


def init_session() -> str:
    """Create a new session on app load. Bound to `demo.load`."""
    sid, _ = session_store.get_or_create(None)
    return sid


def ingest_and_generate(files, session_id: str, progress=gr.Progress()):
    """
    Called when the user uploads files and clicks 'Load & Generate Tests'.

    Steps:
      1. Ingest files into the session's vectorstore.
      2. Generate test questions from the ingested chunks.
      3. Store tests in the session.
      4. Return status HTML and a dataframe preview of the tests.
    """
    if not files:
        return (
            "<p style='color:red;'>No files uploaded. Please upload at least one PDF or .txt file.</p>",
            pd.DataFrame(),
            session_id,
        )

    file_paths = [f.name for f in files]  # Gradio passes NamedString objects

    # Step 1: Ingest
    progress(0.1, desc="Ingesting documents…")
    try:
        chunks = ingest_files(session_id, file_paths)
    except Exception as exc:
        return (
            f"<p style='color:red;'>Ingestion failed: {exc}</p>",
            pd.DataFrame(),
            session_id,
        )

    # Step 2: Generate tests
    progress(0.4, desc=f"Generating test questions from {len(chunks)} chunks…")
    try:
        new_tests = generate_tests(chunks)
    except Exception as exc:
        return (
            f"<p style='color:orange;'>Ingestion OK but test generation failed: {exc}</p>",
            pd.DataFrame(),
            session_id,
        )

    # Step 3: Append tests to session (accumulate across uploads)
    session = session_store.get(session_id)
    session.tests.extend(new_tests)

    total_tests = len(session.tests)
    doc_names = ", ".join(session.doc_names)

    progress(1.0, desc="Done")

    status_html = f"""
    <div style="padding:15px;background:#d4edda;border-radius:8px;border:1px solid #c3e6cb;">
        <strong style="color:#155724;">✓ Ready for evaluation</strong><br>
        <span style="color:#155724;font-size:13px;">
            Documents: {doc_names}<br>
            Chunks: {len(chunks)} ingested this upload<br>
            Total test questions: <strong>{total_tests}</strong>
        </span>
    </div>
    """

    # Build preview dataframe
    rows = [
        {
            "Category": t.category,
            "Question": t.question[:80] + ("…" if len(t.question) > 80 else ""),
            "Keywords": ", ".join(t.keywords),
        }
        for t in session.tests
    ]
    df = pd.DataFrame(rows)

    return status_html, df, session_id


# ── Eval callbacks (adapted to pass session_id) ───────────────────────────────


def run_retrieval_evaluation(session_id: str, progress=gr.Progress()):
    """Run retrieval evaluation. Identical output shape to original."""
    session = session_store.get(session_id)
    if not session.is_ready:
        empty_html = "<p style='color:red;'>No documents or tests loaded. Complete the Setup step first.</p>"
        return empty_html, pd.DataFrame()

    total_mrr = total_ndcg = total_coverage = 0.0
    category_mrr: dict = defaultdict(list)
    count = 0

    for test, result, prog_value in evaluate_all_retrieval(session_id):
        count += 1
        total_mrr += result.mrr
        total_ndcg += result.ndcg
        total_coverage += result.keyword_coverage
        category_mrr[test.category].append(result.mrr)
        progress(prog_value, desc=f"Evaluating test {count}…")

    avg_mrr = total_mrr / count
    avg_ndcg = total_ndcg / count
    avg_coverage = total_coverage / count

    final_html = f"""
    <div style="padding:0;">
        {format_metric_html("Mean Reciprocal Rank (MRR)", avg_mrr, "mrr")}
        {format_metric_html("Normalized DCG (nDCG)", avg_ndcg, "ndcg")}
        {format_metric_html("Keyword Coverage", avg_coverage, "coverage", is_percentage=True)}
        <div style="margin-top:20px;padding:10px;background:#d4edda;border-radius:5px;text-align:center;border:1px solid #c3e6cb;">
            <span style="font-size:14px;color:#155724;font-weight:bold;">✓ Retrieval Evaluation Complete: {count} tests</span>
        </div>
    </div>
    """

    category_data = [
        {"Category": cat, "Average MRR": sum(scores) / len(scores)}
        for cat, scores in category_mrr.items()
    ]
    df = pd.DataFrame(category_data)
    return final_html, df


def run_answer_evaluation(session_id: str, progress=gr.Progress()):
    """Run answer evaluation. Identical output shape to original."""
    session = session_store.get(session_id)
    if not session.is_ready:
        empty_html = "<p style='color:red;'>No documents or tests loaded. Complete the Setup step first.</p>"
        return empty_html, pd.DataFrame()

    total_accuracy = total_completeness = total_relevance = 0.0
    category_accuracy: dict = defaultdict(list)
    count = 0

    for test, result, prog_value in evaluate_all_answers(session_id):
        count += 1
        total_accuracy += result.accuracy
        total_completeness += result.completeness
        total_relevance += result.relevance
        category_accuracy[test.category].append(result.accuracy)
        progress(prog_value, desc=f"Evaluating test {count}…")

    avg_accuracy = total_accuracy / count
    avg_completeness = total_completeness / count
    avg_relevance = total_relevance / count

    final_html = f"""
    <div style="padding:0;">
        {format_metric_html("Accuracy", avg_accuracy, "accuracy", score_format=True)}
        {format_metric_html("Completeness", avg_completeness, "completeness", score_format=True)}
        {format_metric_html("Relevance", avg_relevance, "relevance", score_format=True)}
        <div style="margin-top:20px;padding:10px;background:#d4edda;border-radius:5px;text-align:center;border:1px solid #c3e6cb;">
            <span style="font-size:14px;color:#155724;font-weight:bold;">✓ Answer Evaluation Complete: {count} tests</span>
        </div>
    </div>
    """

    category_data = [
        {"Category": cat, "Average Accuracy": sum(scores) / len(scores)}
        for cat, scores in category_accuracy.items()
    ]
    df = pd.DataFrame(category_data)
    return final_html, df


# ── UI layout ─────────────────────────────────────────────────────────────────


def main():
    with gr.Blocks(title="RAG Evaluation Dashboard") as app:
        # Hidden state: holds the session_id string for this browser tab
        session_state = gr.State(value=None)

        gr.Markdown("# RAG Evaluation Dashboard")
        gr.Markdown(
            "Upload your documents, generate test questions automatically, "
            "then evaluate retrieval and answer quality."
        )

        # ── STEP 1: SETUP ─────────────────────────────────────────────────────
        with gr.Accordion("Step 1 — Load Documents & Generate Tests", open=True):
            gr.Markdown(
                "Upload the same PDF or .txt files you want to evaluate. "
                "The system will index them and auto-generate test questions. "
                "You can upload additional files later — new questions will be appended."
            )

            file_upload = gr.File(
                label="Upload documents (PDF or .txt)",
                file_count="multiple",
                file_types=[".pdf", ".txt"],
                type="filepath",
            )

            load_btn = gr.Button("Load & Generate Tests", variant="primary", size="lg")

            setup_status = gr.HTML(
                "<p style='color:#999;'>Upload files and click the button to begin.</p>"
            )

            test_preview = gr.DataFrame(
                headers=["Category", "Question", "Keywords"],
                label="Generated Test Questions",
                wrap=True,
                interactive=False,
            )

        # ── STEP 2: RETRIEVAL EVAL ────────────────────────────────────────────
        gr.Markdown("---")
        gr.Markdown("## Step 2 — Retrieval Evaluation")

        retrieval_button = gr.Button(
            "Run Retrieval Evaluation", variant="primary", size="lg"
        )

        with gr.Row():
            with gr.Column(scale=1):
                retrieval_metrics = gr.HTML(
                    "<div style='padding:20px;text-align:center;color:#999;'>"
                    "Complete Step 1 first, then click Run.</div>"
                )
            with gr.Column(scale=1):
                retrieval_chart = gr.BarPlot(
                    x="Category",
                    y="Average MRR",
                    title="Average MRR by Category",
                    y_lim=[0, 1],
                    height=400,
                )

        # ── STEP 3: ANSWER EVAL ───────────────────────────────────────────────
        gr.Markdown("---")
        gr.Markdown("## Step 3 — Answer Evaluation")

        answer_button = gr.Button("Run Answer Evaluation", variant="primary", size="lg")

        with gr.Row():
            with gr.Column(scale=1):
                answer_metrics = gr.HTML(
                    "<div style='padding:20px;text-align:center;color:#999;'>"
                    "Complete Step 1 first, then click Run.</div>"
                )
            with gr.Column(scale=1):
                answer_chart = gr.BarPlot(
                    x="Category",
                    y="Average Accuracy",
                    title="Average Accuracy by Category",
                    y_lim=[1, 5],
                    height=400,
                )

        # ── Event wiring ──────────────────────────────────────────────────────

        # On page load: create a session and store its ID in gr.State
        app.load(fn=init_session, inputs=None, outputs=session_state)

        # Setup: ingest + generate
        load_btn.click(
            fn=ingest_and_generate,
            inputs=[file_upload, session_state],
            outputs=[setup_status, test_preview, session_state],
        )

        # Retrieval eval
        retrieval_button.click(
            fn=run_retrieval_evaluation,
            inputs=[session_state],
            outputs=[retrieval_metrics, retrieval_chart],
        )

        # Answer eval
        answer_button.click(
            fn=run_answer_evaluation,
            inputs=[session_state],
            outputs=[answer_metrics, answer_chart],
        )

    theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])
    app.launch(server_name="0.0.0.0", server_port=7860, theme=theme)


if __name__ == "__main__":
    main()
