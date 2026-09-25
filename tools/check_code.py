#!/usr/bin/env python3
"""Гейт блоків коду лекцій: оформлення, лінтер, розміри, підписи.

Для кожного блоку ```python* у gamma_course/decks_new/modNN.md:
  · `ruff format --check` (88 символів) — блок відформатований;
  · `ruff check --select E,F,W,I,B,UP` — 0 зауважень. Блок-продовження
    перевіряється разом із попередніми блоками ланцюжка, щоб імена з них
    були відомі; у фрагментів не вважаються помилкою невизначені й
    невикористані імена та вираз-«заглушка» `...`;
  · блок > 60 рядків — помилка, > 40 — зауваження;
  · перед блоком «<!-- code: що робить код -->», після виводу — «*На що дивитися: …*»;
  · вивід > 25 рядків або сирий dict — помилка.

  python3 tools/check_code.py            # усі модулі
  python3 tools/check_code.py 07 10
"""
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_site import (  # noqa: E402
    CONTINUATION, FRAGMENT, MAX_OUT_LINES, RAW_DICT, SRC, code_blocks,
)

RUFF_RULES = "E,F,W,I,B,UP"
RUFF = [sys.executable, "-m", "ruff"]


def check_module(num, tmp):
    blocks = code_blocks(open(os.path.join(SRC, f"mod{num}.md"), encoding="utf-8").read())
    err, warn = [], []
    fmt_files, lint_files, frag_files, chain = [], [], [], []
    for k, (lang, code, out, note, title) in enumerate(blocks, 1):
        name = f"мод {num} блок {k}"
        n = len(code.split("\n"))
        if not title:
            err.append(f"{name}: перед блоком немає «<!-- code: що робить код -->»")
        if n > 60:
            err.append(f"{name}: {n} рядків (межа 60, ціль ≤ 40)")
        elif n > 40:
            warn.append(f"{name}: {n} рядків (ціль ≤ 40)")
        if lang != FRAGMENT:
            if out is None:
                err.append(f"{name}: немає виводу ```text під кодом")
            elif len(out) > MAX_OUT_LINES:
                err.append(f"{name}: вивід {len(out)} рядків (> {MAX_OUT_LINES})")
            elif RAW_DICT.search("\n".join(out)):
                err.append(f"{name}: у виводі сирий dict")
            if not note:
                err.append(f"{name}: немає рядка «*На що дивитися: …*»")
        f = os.path.join(tmp, f"m{num}_b{k:02d}.py")
        open(f, "w", encoding="utf-8").write(code + "\n")
        fmt_files.append(f)
        if lang == FRAGMENT:
            chain = []
            frag_files.append(f)
            continue
        first = code.strip().split("\n", 1)[0].strip()
        chain = chain + [code] if first == CONTINUATION and chain else [code]
        g = os.path.join(tmp, f"c{num}_b{k:02d}.py")
        open(g, "w", encoding="utf-8").write("\n\n\n".join(chain) + "\n")
        lint_files.append(g)
    return err, warn, fmt_files, lint_files, frag_files


def main(argv):
    nums = argv or [f"{i:02d}" for i in range(1, 13)]
    err, warn, total = [], [], 0
    with tempfile.TemporaryDirectory() as tmp:
        fmt, lint, frag = [], [], []
        for num in nums:
            e, w, f, li, fr = check_module(num, tmp)
            err += e
            warn += w
            fmt += f
            lint += li
            frag += fr
        total = len(fmt)
        if fmt:
            r = subprocess.run(RUFF + ["format", "--check", "--line-length", "88", *fmt],
                               capture_output=True, text=True)
            for f in re.findall(r"(m\d\d_b\d\d)\.py", r.stdout + r.stderr):
                err.append(f"{f.replace('_', ' ')}: не відформатовано `ruff format`")
        for files, extra in ((lint, []), (frag, ["--ignore", "F821,F841,F401,B018"])):
            if not files:
                continue
            r = subprocess.run(RUFF + ["check", "--select", RUFF_RULES, "--line-length", "88",
                                       "--output-format", "concise", "--no-cache", *extra, *files],
                               capture_output=True, text=True)
            for line in r.stdout.splitlines():
                m = re.match(r".*[cm](\d\d)_b(\d\d)\.py:(\d+):\d+: (.+)$", line)
                if m:
                    err.append(f"мод {m.group(1)} блок {int(m.group(2))}: ruff — {m.group(4)} "
                               f"(рядок {m.group(3)} ланцюжка)")
    for w in warn:
        print("  зауваження: " + w)
    for e in err:
        print("  ПОМИЛКА: " + e)
    print(f"\nблоків перевірено: {total}, помилок: {len(err)}, зауважень: {len(warn)}")
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
