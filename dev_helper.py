#!/usr/bin/env python3
"""
Dev Helper CLI

Tool sederhana untuk membantu pekerjaan harian bidang informatika:
- Todo list (prioritas, status)
- Pomodoro timer (fokus kerja)
- Snippet/command notebook (catatan command penting)

Data disimpan di file JSON lokal: dev_helper_data.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List

DATA_FILE = "dev_helper_data.json"


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def default_data() -> Dict[str, Any]:
    return {
        "todos": [],
        "snippets": [],
        "sessions": [],
        "next_todo_id": 1,
        "next_snippet_id": 1,
    }


def load_data(path: str = DATA_FILE) -> Dict[str, Any]:
    if not os.path.exists(path):
        data = default_data()
        save_data(data, path)
        return data
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data: Dict[str, Any], path: str = DATA_FILE) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_todo(data: Dict[str, Any], title: str, priority: str) -> None:
    todo = {
        "id": data["next_todo_id"],
        "title": title,
        "priority": priority,
        "done": False,
        "created_at": now_str(),
        "completed_at": None,
    }
    data["todos"].append(todo)
    data["next_todo_id"] += 1
    print(f"[OK] Todo ditambahkan: #{todo['id']} - {todo['title']}")


def list_todos(data: Dict[str, Any], all_items: bool = False) -> None:
    todos = data["todos"]
    if not all_items:
        todos = [t for t in todos if not t["done"]]

    if not todos:
        print("Belum ada todo.")
        return

    todos = sorted(todos, key=lambda t: (t["done"], priority_order(t["priority"]), t["id"]))
    print("=== TODO LIST ===")
    for t in todos:
        status = "DONE" if t["done"] else "OPEN"
        print(f"#{t['id']:>3} [{status}] [{t['priority'].upper():^6}] {t['title']}")


def priority_order(priority: str) -> int:
    mapping = {"high": 0, "medium": 1, "low": 2}
    return mapping.get(priority, 3)


def complete_todo(data: Dict[str, Any], todo_id: int) -> None:
    for t in data["todos"]:
        if t["id"] == todo_id:
            if t["done"]:
                print(f"[INFO] Todo #{todo_id} sudah selesai sebelumnya.")
                return
            t["done"] = True
            t["completed_at"] = now_str()
            print(f"[OK] Todo #{todo_id} ditandai selesai.")
            return
    print(f"[ERR] Todo #{todo_id} tidak ditemukan.")


def delete_todo(data: Dict[str, Any], todo_id: int) -> None:
    before = len(data["todos"])
    data["todos"] = [t for t in data["todos"] if t["id"] != todo_id]
    if len(data["todos"]) == before:
        print(f"[ERR] Todo #{todo_id} tidak ditemukan.")
    else:
        print(f"[OK] Todo #{todo_id} dihapus.")


def add_snippet(data: Dict[str, Any], title: str, content: str, tags: List[str]) -> None:
    snippet = {
        "id": data["next_snippet_id"],
        "title": title,
        "content": content,
        "tags": tags,
        "created_at": now_str(),
    }
    data["snippets"].append(snippet)
    data["next_snippet_id"] += 1
    print(f"[OK] Snippet ditambahkan: #{snippet['id']} - {snippet['title']}")


def list_snippets(data: Dict[str, Any], keyword: str | None = None) -> None:
    snippets = data["snippets"]
    if keyword:
        k = keyword.lower()
        snippets = [
            s
            for s in snippets
            if k in s["title"].lower()
            or k in s["content"].lower()
            or any(k in tag.lower() for tag in s["tags"])
        ]
    if not snippets:
        print("Snippet tidak ditemukan.")
        return

    print("=== SNIPPETS ===")
    for s in snippets:
        tag_text = ", ".join(s["tags"]) if s["tags"] else "-"
        print(f"#{s['id']:>3} {s['title']} | tags: {tag_text}")
        print(f"      {s['content']}")


def pomodoro(minutes: int, note: str | None, data: Dict[str, Any]) -> None:
    if minutes <= 0:
        print("[ERR] Menit harus lebih besar dari 0.")
        return
    total_seconds = minutes * 60
    print(f"Mulai fokus {minutes} menit. Tetap semangat.")
    start = time.time()
    try:
        while True:
            elapsed = int(time.time() - start)
            remaining = total_seconds - elapsed
            if remaining <= 0:
                break
            mins, secs = divmod(remaining, 60)
            sys.stdout.write(f"\rSisa waktu: {mins:02d}:{secs:02d}")
            sys.stdout.flush()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Timer dibatalkan.")
        return

    print("\n[OK] Sesi fokus selesai. Saatnya istirahat singkat.")
    data["sessions"].append(
        {
            "minutes": minutes,
            "note": note or "",
            "finished_at": now_str(),
        }
    )


def stats(data: Dict[str, Any]) -> None:
    todos = data["todos"]
    total = len(todos)
    done = sum(1 for t in todos if t["done"])
    open_items = total - done

    sessions = data["sessions"]
    today = datetime.now().strftime("%Y-%m-%d")
    today_sessions = [s for s in sessions if s["finished_at"].startswith(today)]
    today_minutes = sum(s["minutes"] for s in today_sessions)

    print("=== RINGKASAN ===")
    print(f"Todo total : {total}")
    print(f"Todo open  : {open_items}")
    print(f"Todo done  : {done}")
    print(f"Sesi fokus hari ini : {len(today_sessions)}")
    print(f"Total menit fokus hari ini : {today_minutes}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dev_helper",
        description="Asisten CLI harian untuk pekerja informatika.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Tambah todo")
    p_add.add_argument("title", help="Judul todo")
    p_add.add_argument("--priority", choices=["low", "medium", "high"], default="medium")

    p_list = sub.add_parser("list", help="Lihat todo")
    p_list.add_argument("--all", action="store_true", help="Tampilkan semua termasuk yang selesai")

    p_done = sub.add_parser("done", help="Tandai todo selesai")
    p_done.add_argument("id", type=int, help="ID todo")

    p_del = sub.add_parser("delete", help="Hapus todo")
    p_del.add_argument("id", type=int, help="ID todo")

    p_pomo = sub.add_parser("focus", help="Mulai timer fokus (pomodoro)")
    p_pomo.add_argument("--minutes", type=int, default=25, help="Durasi fokus (default: 25)")
    p_pomo.add_argument("--note", type=str, default="", help="Catatan sesi")

    p_sadd = sub.add_parser("snippet-add", help="Tambah snippet/command")
    p_sadd.add_argument("title", help="Judul snippet")
    p_sadd.add_argument("content", help="Isi snippet")
    p_sadd.add_argument("--tags", default="", help="Tag dipisah koma, contoh: git,deploy,db")

    p_slist = sub.add_parser("snippet-list", help="Lihat snippet")
    p_slist.add_argument("--q", default="", help="Kata kunci pencarian")

    sub.add_parser("stats", help="Lihat ringkasan produktivitas")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    data = load_data()

    if args.command == "add":
        add_todo(data, args.title, args.priority)
    elif args.command == "list":
        list_todos(data, args.all)
    elif args.command == "done":
        complete_todo(data, args.id)
    elif args.command == "delete":
        delete_todo(data, args.id)
    elif args.command == "focus":
        pomodoro(args.minutes, args.note, data)
    elif args.command == "snippet-add":
        tags = [x.strip() for x in args.tags.split(",") if x.strip()]
        add_snippet(data, args.title, args.content, tags)
    elif args.command == "snippet-list":
        list_snippets(data, args.q or None)
    elif args.command == "stats":
        stats(data)
    else:
        parser.print_help()
        return

    save_data(data)


if __name__ == "__main__":
    main()
