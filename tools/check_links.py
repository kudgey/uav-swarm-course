#!/usr/bin/env python3
"""Перевіряє, що кожне посилання зі зібраного сайту справді відкривається.

Клас помилок, заради якого це написано: сторінка віддає 200, опис на місці,
а файла за посиланням немає. Ані читання коду, ані консоль браузера цього
не ловлять — тільки запит за кожним посиланням.

  python3 tools/check_links.py                     # локальна збірка dist/
  python3 tools/check_links.py https://...         # живий сайт
"""
import concurrent.futures
import glob
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(os.path.dirname(HERE), ".vitepress", "dist")

UA = {"User-Agent": "Mozilla/5.0 (course link checker)"}
# Видавці ставлять антибот-захист: 403 від них не означає, що посилання мертве.
TOLERATED = {403, 202}


def internal_targets():
    """Файли, на які посилаються сторінки: PDF, архіви, зображення."""
    out = set()
    for f in glob.glob(os.path.join(DIST, "**", "*.html"), recursive=True):
        html = open(f, encoding="utf-8").read()
        for m in re.findall(r'(?:href|src)="(/[^"]+\.(?:pdf|zip|ipynb|png|jpg|svg))"', html):
            out.add(m)
    return sorted(out)


def external_links():
    out = set()
    for f in glob.glob(os.path.join(DIST, "**", "*.html"), recursive=True):
        html = open(f, encoding="utf-8").read()
        for m in re.findall(r'href="(https?://[^"]+)"', html):
            out.add(m.rstrip("."))
    return sorted(out)


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers=UA, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return f"{type(e).__name__}"


def main(argv):
    base = argv[0].rstrip("/") if argv else None
    bad = 0

    targets = internal_targets()
    if base:
        print(f"внутрішні файли на {base}: {len(targets)}")
        with concurrent.futures.ThreadPoolExecutor(8) as ex:
            for path, code in zip(targets, ex.map(lambda p: fetch(base + p), targets)):
                if code != 200:
                    print(f"  {code}  {path}")
                    bad += 1
    else:
        print(f"внутрішні файли у dist/: {len(targets)}")
        for path in targets:
            if not os.path.exists(os.path.join(DIST, path.lstrip("/"))):
                print(f"  НЕМАЄ ФАЙЛУ  {path}")
                bad += 1

    ext = external_links()
    print(f"зовнішні посилання: {len(ext)}")
    with concurrent.futures.ThreadPoolExecutor(8) as ex:
        for url, code in zip(ext, ex.map(fetch, ext)):
            if code != 200 and code not in TOLERATED:
                print(f"  {code}  {url}")
                bad += 1

    print(f"\nпроблем: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
