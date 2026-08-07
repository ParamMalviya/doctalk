import json
import sys
from pathlib import Path

from doctalk.config.configuration import ConfigurationManager
from doctalk.pipelines.stage_01_ingestion import IngestionPipeline
from doctalk.pipelines.stage_02_chat import ChatPipeline
from doctalk.components.vector_store import VectorStore
from doctalk.components.retriever import RetrieverBuilder
from doctalk.logger import setup_logging, logger
from doctalk.exception import CustomException


QA_PATH = Path("eval/qa_pairs.json")
DOC_PATH = Path("eval/test_document.pdf")
RESULTS_PATH = Path("eval/results.json")
EVAL_SESSION = "eval_session"


def check_keywords(answer: str, keywords: list) -> bool:
    '''true if ANY expected keyword appears in the answer (case-insensitive)'''
    low = answer.lower()
    return any(kw.lower() in low for kw in keywords)


def check_retrieval_hit(retriever, question: str, source_page) -> bool:
    '''true if the retriever returned a chunk from the expected page'''
    if source_page is None:
        return None  # not applicable (summarize / github questions)

    docs = retriever.invoke(question)
    pages = [d.metadata.get("page") for d in docs]
    return source_page in pages


def main():
    try:
        setup_logging()
        logger.info(">>>>>> eval started <<<<<<")

        qa_pairs = json.loads(QA_PATH.read_text(encoding="utf-8"))
        logger.info(f"loaded {len(qa_pairs)} qa pairs")

        # ingest the fixed test doc into a dedicated eval session
        chunks = IngestionPipeline().run(DOC_PATH)
        cm = ConfigurationManager()
        store = VectorStore(cm.get_vector_store_config()).build(
            chunks=chunks, session_id=EVAL_SESSION
        )
        retriever = RetrieverBuilder(cm.get_retriever_config()).build(store)

        # one chat pipeline, reused for every question
        chat = ChatPipeline(session_id=EVAL_SESSION, chunks=chunks)

        results = []
        for i, pair in enumerate(qa_pairs, start=1):
            question = pair["question"]
            logger.info(f"[{i}/{len(qa_pairs)}] {question}")

            hit = check_retrieval_hit(retriever, question, pair["source_page"])
            # unique thread_id per question -- keeps eval questions independent
            # even though they all share one cached ChatPipeline/agent
            answer = chat.ask(question, thread_id=f"{EVAL_SESSION}_{i}")
            correct = check_keywords(answer, pair["expected_keywords"])

            results.append({
                "question": question,
                "tool": pair["tool"],
                "retrieval_hit": hit,
                "answer_correct": correct,
                "answer": answer,
            })

        # ---- score it ----
        retrieval_cases = [r for r in results if r["retrieval_hit"] is not None]
        hits = sum(1 for r in retrieval_cases if r["retrieval_hit"])
        correct = sum(1 for r in results if r["answer_correct"])

        print("\n" + "=" * 60)
        print("DOCTALK EVAL RESULTS")
        print("=" * 60)
        for r in results:
            hit_mark = {True: "HIT ", False: "MISS", None: "n/a "}[r["retrieval_hit"]]
            ans_mark = "PASS" if r["answer_correct"] else "FAIL"
            print(f"[retrieval {hit_mark}] [answer {ans_mark}] {r['question'][:55]}")

        print("-" * 60)
        if retrieval_cases:
            print(f"Retrieval hit-rate: {hits}/{len(retrieval_cases)} "
                  f"({100 * hits / len(retrieval_cases):.0f}%)")
        print(f"Answer accuracy:    {correct}/{len(results)} "
              f"({100 * correct / len(results):.0f}%)")
        print("=" * 60)

        RESULTS_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
        logger.info(f">>>>>> eval complete, results saved to {RESULTS_PATH} <<<<<<")

    except Exception as e:
        logger.exception(e)
        raise CustomException(e, sys) from e


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()