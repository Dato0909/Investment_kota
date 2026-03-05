#!/usr/bin/env python3
"""
投資メモ管理スクリプト
Usage:
  python scripts/investment_note.py list
  python scripts/investment_note.py add --ticker 7203.T --title "投資テーゼ" --body "..."
  python scripts/investment_note.py view --ticker 7203.T
  python scripts/investment_note.py search --keyword "配当"
"""

import argparse
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


NOTES_DIR = Path("data/notes")


def _note_path(ticker: str) -> Path:
    return NOTES_DIR / f"{ticker.upper()}.md"


def _list_notes():
    """メモ一覧を表示"""
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    notes = sorted(NOTES_DIR.glob("*.md"))
    if not notes:
        print("投資メモはまだありません。`investment_note.py add` で追加してください。")
        return

    print(f"# 投資メモ一覧 ({len(notes)}件)\n")
    for note_path in notes:
        ticker = note_path.stem
        lines = note_path.read_text(encoding="utf-8").splitlines()
        # 最初の非空行をタイトルとして使用
        title = next((l.lstrip("# ") for l in lines if l.strip()), ticker)
        mtime = date.fromtimestamp(note_path.stat().st_mtime)
        print(f"- **{ticker}**: {title} (更新: {mtime})")


def _add_note(ticker: str, title: str, body: str, tags: list):
    """メモを追加・更新"""
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    path = _note_path(ticker)
    today = date.today()

    content = f"# {ticker} — {title}\n\n"
    content += f"**更新日:** {today}  \n"
    if tags:
        content += f"**タグ:** {', '.join(tags)}  \n"
    content += "\n---\n\n"

    if path.exists():
        # 既存のメモに追記
        existing = path.read_text(encoding="utf-8")
        content = existing + f"\n## {today}: {title}\n\n{body}\n"
    else:
        content += body + "\n"

    path.write_text(content, encoding="utf-8")
    print(f"✅ {ticker} のメモを保存しました: {path}")


def _view_note(ticker: str):
    """メモを表示"""
    path = _note_path(ticker)
    if not path.exists():
        print(f"{ticker} のメモはありません。")
        return
    print(path.read_text(encoding="utf-8"))


def _search_notes(keyword: str):
    """メモ内をキーワード検索"""
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for note_path in NOTES_DIR.glob("*.md"):
        content = note_path.read_text(encoding="utf-8")
        if keyword.lower() in content.lower():
            ticker = note_path.stem
            # マッチした行を抽出
            matching_lines = [
                f"  > {line.strip()}"
                for line in content.splitlines()
                if keyword.lower() in line.lower()
            ][:3]
            results.append((ticker, matching_lines))

    if not results:
        print(f"'{keyword}' を含むメモが見つかりませんでした。")
        return

    print(f"# 検索結果: '{keyword}' ({len(results)}件)\n")
    for ticker, lines in results:
        print(f"## {ticker}")
        for line in lines:
            print(line)
        print()


def main():
    parser = argparse.ArgumentParser(description="投資メモ管理")
    subparsers = parser.add_subparsers(dest="action")

    subparsers.add_parser("list", help="メモ一覧を表示")

    add_p = subparsers.add_parser("add", help="メモを追加")
    add_p.add_argument("--ticker", "-t", required=True, help="ティッカーシンボル")
    add_p.add_argument("--title", required=True, help="メモタイトル")
    add_p.add_argument("--body", "-b", required=True, help="メモ本文")
    add_p.add_argument("--tags", nargs="+", default=[], help="タグ (スペース区切り)")

    view_p = subparsers.add_parser("view", help="メモを表示")
    view_p.add_argument("--ticker", "-t", required=True, help="ティッカーシンボル")

    search_p = subparsers.add_parser("search", help="メモを検索")
    search_p.add_argument("--keyword", "-k", required=True, help="検索キーワード")

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        return

    if args.action == "list":
        _list_notes()
    elif args.action == "add":
        _add_note(args.ticker.upper(), args.title, args.body, args.tags)
    elif args.action == "view":
        _view_note(args.ticker.upper())
    elif args.action == "search":
        _search_notes(args.keyword)


if __name__ == "__main__":
    main()
