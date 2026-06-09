import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.app import AppAgent


DATASET_PATH = ROOT / "storage" / "eval" / "pdf_eval_dataset.jsonl"
REPORT_PATH = ROOT / "storage" / "eval" / "pdf_eval_report.json"


def load_dataset() -> list:
    if not DATASET_PATH.exists():
        raise RuntimeError("评测数据集不存在，请先运行 scripts\\build_sample_pdf_eval_dataset.py")
    rows = []
    for line in DATASET_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def evaluate(top_k: int = 3) -> dict:
    app = AppAgent()
    rows = load_dataset()
    results = []

    for row in rows:
        query_vector = app.embedder.embed_texts([row["question"]])[0]
        retrieved = app.vector_store.query_vectors(query_vector, top_k=top_k)
        retrieved_sources = [item["metadata"].get("source") for item in retrieved]
        retrieved_texts = [item["metadata"].get("text", "") for item in retrieved]
        expected_source = row["source"]
        evidence = row["evidence"]

        source_hit = expected_source in retrieved_sources
        evidence_hit = any(evidence in text for text in retrieved_texts)
        results.append(
            {
                "id": row["id"],
                "question": row["question"],
                "expected_source": expected_source,
                "retrieved_sources": retrieved_sources,
                "source_hit": source_hit,
                "evidence_hit": evidence_hit,
            }
        )

    total = len(results)
    source_hits = sum(1 for item in results if item["source_hit"])
    evidence_hits = sum(1 for item in results if item["evidence_hit"])
    report = {
        "dataset": str(DATASET_PATH.relative_to(ROOT)),
        "top_k": top_k,
        "total": total,
        "source_hit_count": source_hits,
        "evidence_hit_count": evidence_hits,
        "source_hit_rate": source_hits / total if total else 0,
        "evidence_hit_rate": evidence_hits / total if total else 0,
        "results": results,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    top_k = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    report = evaluate(top_k=top_k)
    print(f"评测样本数: {report['total']}")
    print(f"Top-{top_k} 源文档命中率: {report['source_hit_rate']:.2%}")
    print(f"Top-{top_k} 证据片段命中率: {report['evidence_hit_rate']:.2%}")
    print(f"评测报告: {REPORT_PATH}")


if __name__ == "__main__":
    main()
