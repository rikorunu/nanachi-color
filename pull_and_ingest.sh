#!/bin/bash
# ナナチカラー weekly pull + ChromaDB re-ingest
set -e
LOG_DIR="/home/arc_e/nanachi-color/logs"
LOG_FILE="$LOG_DIR/weekly_update_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$LOG_DIR"

{
  echo "=== ナナチカラー weekly ingest start: $(date) ==="
  cd /home/arc_e/nanachi-color
  
  # GitHubからpull (CCRがpushした新コンテンツを取得)
  git pull origin main
  echo "=== git pull 完了 ==="
  
  # ChromaDB再投入
  /home/arc_e/ollama-agent-venv/bin/python3 ingest_color_rag.py
  echo "=== ChromaDB ingest 完了 ==="
  
  echo "=== 完了: $(date) ==="
} >> "$LOG_FILE" 2>&1
