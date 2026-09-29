#!/usr/bin/env python3
"""Гейт рисунків: запозичене — лише в figs/ext і з «Джерело», власне — лише з кодом.

Для кожного рисунка ![…](RAWBASE/name.png) у gamma_course/decks_new/modNN.md:
  · файл існує в uav-site/public/figs/ext або figs/own;
  · рисунок із ext (вирізаний із PDF чи взятий з інтернету) має одразу під
    собою рядок «Джерело: …» із посиланням;
  · рисунок з own (власний) має скрипт у gamma_course/viz, де згадано його
    ім'я, — інакше це, найімовірніше, запозичений рисунок, покладений не туди.
    Винятки перелічено в ALLOW з поясненням.

  python3 tools/check_figs.py
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
COURSE = os.path.join(os.path.dirname(SITE), "gamma_course")
IMG = re.compile(r"^!\[[^\]]*\]\(RAWBASE/([\w.-]+)\)\s*$")

# Власні рисунки, чий скрипт не зберігся (середовище відкочувалося), — з поясненням.
ALLOW = {
    "m08-task-allocation.png": "власний рисунок курсу; скрипт утрачено під час відкату середовища",
}


def main():
    viz = "\n".join(open(f, encoding="utf-8", errors="ignore").read()
                    for f in glob.glob(os.path.join(COURSE, "viz", "*.py")))
    bad, n_ext, n_own = [], 0, 0
    for num in range(1, 13):
        lines = open(os.path.join(COURSE, "decks_new", f"mod{num:02d}.md"), encoding="utf-8").read().split("\n")
        for i, line in enumerate(lines):
            m = IMG.match(line)
            if not m:
                continue
            name = m.group(1)
            ext = os.path.exists(os.path.join(SITE, "public", "figs", "ext", name))
            own = os.path.exists(os.path.join(SITE, "public", "figs", "own", name))
            where = f"мод {num:02d}, рядок {i + 1}: {name}"
            if not ext and not own:
                bad.append(f"{where} — файла немає ні в ext, ні в own")
                continue
            if ext and own:
                bad.append(f"{where} — лежить і в ext, і в own")
            if ext:
                n_ext += 1
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                cap = lines[j] if j < len(lines) else ""
                if not cap.startswith("Джерело"):
                    bad.append(f"{where} — запозичений рисунок без рядка «Джерело» під ним")
                elif "](" not in cap:
                    bad.append(f"{where} — у «Джерело» немає посилання")
            else:
                n_own += 1
                if name.rsplit(".", 1)[0] not in viz and name not in ALLOW:
                    bad.append(f"{where} — у figs/own, але жоден скрипт gamma_course/viz його не малює")
    for b in bad:
        print("  " + b)
    print(f"\nвикористань рисунків: запозичених {n_ext}, власних {n_own}; винятків у ALLOW: {len(ALLOW)}")
    print(f"проблем: {len(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
