#!/usr/bin/env python3
"""カラー理論RAGをChromaDBに投入するスクリプト"""
import json
import os
from pathlib import Path

# chromadb と langchain_community の embedding を使う
import chromadb
from langchain_community.embeddings import OllamaEmbeddings

PERSIST_DIR = "/home/arc_e/nanachi-color/color_rag_db"
COLLECTION_NAME = "nanachi_color_rag"
RAG_DOCS_DIR = "/home/arc_e/nanachi-color/rag_docs"

def ingest():
    # OllamaEmbeddings (nomic-embed-text)
    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url="http://localhost:11434")

    # ChromaDB クライアント
    client = chromadb.PersistentClient(path=PERSIST_DIR)

    # 既存コレクションを削除して再作成
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"既存コレクション削除: {COLLECTION_NAME}")
    except Exception:
        pass

    collection = client.create_collection(COLLECTION_NAME)

    # ドキュメント読み込み
    doc_files = [
        "color_theory_basics.json",
        "color_harmony_rules.json",
        "color_psychology.json",
        "color_usage_guide.json",
    ]

    all_docs = []
    for fname in doc_files:
        fpath = Path(RAG_DOCS_DIR) / fname
        if fpath.exists():
            with open(fpath, encoding="utf-8") as f:
                docs = json.load(f)
                all_docs.extend(docs)
                print(f"読み込み: {fname} ({len(docs)}件)")
        else:
            print(f"ファイルが見つからない: {fpath}")

    if not all_docs:
        print("ドキュメントが見つからない")
        return

    print(f"\n合計 {len(all_docs)} 件のドキュメントを処理する")

    # IDの重複チェック
    ids_seen = set()
    for doc in all_docs:
        doc_id = doc["id"]
        if doc_id in ids_seen:
            print(f"警告: IDが重複している -> {doc_id}")
        ids_seen.add(doc_id)

    # Embedding生成 + ChromaDB投入
    texts = [f"{d.get('title', '')}: {d.get('content', '')}" for d in all_docs]
    ids = [d["id"] for d in all_docs]
    metadatas = [
        {
            "title": d.get("title", ""),
            "theme": d.get("theme", ""),
            "source": "color_rag",
        }
        for d in all_docs
    ]

    # バッチ処理
    batch_size = 10
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        batch_ids = ids[i : i + batch_size]
        batch_meta = metadatas[i : i + batch_size]

        embs = embeddings.embed_documents(batch_texts)
        collection.add(
            embeddings=embs,
            documents=batch_texts,
            ids=batch_ids,
            metadatas=batch_meta,
        )
        print(f"投入: {i + 1}〜{min(i + batch_size, len(texts))}件目")

    print(f"\n完了: 合計{len(all_docs)}件をChromaDB({COLLECTION_NAME})に投入したぜ")
    print(f"保存先: {PERSIST_DIR}")

    # 投入確認
    count = collection.count()
    print(f"コレクション件数確認: {count}件")


if __name__ == "__main__":
    ingest()
