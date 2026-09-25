#!/usr/bin/env python3
"""Запускає блоки коду лекцій і звіряє фактичний вивід із написаним у джерелі.

Блок ```python на картці — самодостатня програма: те, що бачить студент,
і є те, що запускається. Вивід стоїть у джерелі блоком ```text одразу під
кодом; сайт показує його як «код запущено, вивід не редагувався», тому
будь-яка розбіжність між ним і фактичним прогоном — помилка.

Правила:
  · кожен блок виконується в ЧИСТОМУ процесі;
  · спільний стан — лише за явним маркером: перший рядок блоку
    `# продовження попереднього блоку`. Тоді блок виконується разом із
    попереднім ланцюжком, а у вивід іде лише його власна частина;
  · ```python fragment — не виконується (на сторінці позначений як фрагмент);
  · ```python ext — потрібен пакет поза базовим стеком (lbforaging).
    Виконується інтерпретатором зі змінної UAV_EXT_PYTHON; без неї береться
    збережений вивід того самого коду (ключ — хеш коду);
  · помилка, таймаут, порожній вивід, розбіжність із джерелом — код повернення 1.

Фактичний вивід і час виконання пишуться в .vitepress/outputs/NN.json:
звідти build_site.py бере «N с» для шапки блоку.

  python3 tools/run_examples.py              # усі модулі
  python3 tools/run_examples.py 07 10        # вибірково
  python3 tools/run_examples.py 07 --fix     # переписати ```text у джерелі фактичним виводом
  UAV_EXT_PYTHON=/path/to/venv/bin/python python3 tools/run_examples.py 09 12
"""
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_site import CONTINUATION, FRAGMENT, OUTPUTS, SRC, block_hash, code_blocks  # noqa: E402

TIMEOUT = 180

RUNNER = r'''
import contextlib, io, json, os, sys, warnings
os.environ.setdefault("MPLBACKEND", "Agg")
warnings.filterwarnings("ignore")
pieces = json.load(open(sys.argv[1], encoding="utf-8"))
ns = {"__name__": "__main__"}
outs = []
for code in pieces:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(code, "<блок>", "exec"), ns)
    outs.append(buf.getvalue())
json.dump(outs, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False)
'''


def chains(blocks):
    """Для кожного блоку, що виконується, — ланцюжок кодів (попередні + свій)."""
    res, chain = [], []
    for lang, code, out, note, title in blocks:
        if lang == FRAGMENT:
            chain = []
            continue
        first = code.strip().split("\n", 1)[0].strip()
        chain = chain + [code] if first == CONTINUATION and chain else [code]
        res.append((lang, code, out, title, list(chain)))
    return res


def run_chain(pieces, python):
    with tempfile.TemporaryDirectory() as tmp:
        runner, src, dst = (os.path.join(tmp, n) for n in ("runner.py", "in.json", "out.json"))
        open(runner, "w", encoding="utf-8").write(RUNNER)
        json.dump(pieces, open(src, "w", encoding="utf-8"), ensure_ascii=False)
        env = dict(os.environ, PYTHONHASHSEED="0", MPLBACKEND="Agg")
        t0 = time.time()
        try:
            p = subprocess.run([python, runner, src, dst], capture_output=True, text=True,
                               timeout=TIMEOUT, cwd=tmp, env=env)
        except subprocess.TimeoutExpired:
            return None, f"таймаут {TIMEOUT} с", time.time() - t0
        dt = time.time() - t0
        if p.returncode != 0:
            tail = "\n".join(p.stderr.strip().split("\n")[-4:])
            return None, f"помилка виконання:\n{tail}", dt
        return json.load(open(dst, encoding="utf-8"))[-1], None, dt


def same(a, b):
    """Вивід збігається посимвольно — з точністю до кінцевих пробілів і порожніх рядків по краях."""
    norm = lambda s: "\n".join(ln.rstrip() for ln in s.strip("\n").split("\n"))  # noqa: E731
    return norm(a) == norm(b)


def fix_source(num, code, actual):
    """Переписує ```text під блоком із цим кодом фактичним виводом."""
    path = os.path.join(SRC, f"mod{num}.md")
    text = open(path, encoding="utf-8").read()
    body = actual.strip("\n")
    pat = re.compile(re.escape(code) + r"\n```\n(\s*)```text\n.*?\n```", re.S)
    new, n = pat.subn(lambda m: code + "\n```\n" + m.group(1) + "```text\n" + body + "\n```", text, count=1)
    if n:
        open(path, "w", encoding="utf-8").write(new)
    return bool(n)


def run_module(num, fix):
    path = os.path.join(SRC, f"mod{num}.md")
    blocks = code_blocks(open(path, encoding="utf-8").read())
    f = os.path.join(OUTPUTS, f"{num}.json")
    prev = json.load(open(f, encoding="utf-8")) if os.path.exists(f) else {}
    new, errors = {}, []
    frags = sum(1 for b in blocks if b[0] == FRAGMENT)
    for k, (lang, code, declared, title, chain) in enumerate(chains(blocks), 1):
        h = block_hash(code)
        name = f"блок {k} «{title or code.strip().split(chr(10))[0][:40]}»"
        python = sys.executable
        if lang == "python ext":
            python = os.environ.get("UAV_EXT_PYTHON")
            if not python:
                if h in prev and declared is not None and same(prev[h]["out"], "\n".join(declared)):
                    new[h] = prev[h]
                    print(f"    {k:>2} [{h}] ext — збережений вивід ({prev[h].get('sec', '?')} с)")
                else:
                    errors.append(f"{name}: ext без збереженого виводу — задайте UAV_EXT_PYTHON")
                continue
        out, err, dt = run_chain(chain, python)
        if err:
            errors.append(f"{name}: {err}")
            print(f"    {k:>2} [{h}] ✗ {dt:5.1f} с")
            continue
        if not out.strip():
            errors.append(f"{name}: порожній вивід — друкуйте результат або позначте ```python fragment")
        mark = "✓"
        if declared is None or not same(out, "\n".join(declared)):
            if fix and declared is not None and fix_source(num, code, out):
                mark = "✎ вивід у джерелі оновлено"
            else:
                mark = "✗ РОЗБІЖНІСТЬ із джерелом"
                errors.append(f"{name}: вивід у джерелі не збігається з фактичним прогоном")
                a = out.strip("\n").split("\n")
                b = declared or ["«виводу в джерелі немає»"]
                for i in range(max(len(a), len(b))):
                    x = a[i].rstrip() if i < len(a) else "«рядка немає»"
                    y = b[i].rstrip() if i < len(b) else "«рядка немає»"
                    if x != y:
                        print(f"          факт:    {x}\n          джерело: {y}")
        new[h] = {"out": out, "sec": round(dt, 1), "ran": datetime.date.today().isoformat(),
                  "python": sys.version.split()[0] if python == sys.executable else "ext"}
        print(f"    {k:>2} [{h}] {mark} {dt:5.1f} с")
    os.makedirs(OUTPUTS, exist_ok=True)
    if new:
        json.dump(new, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    elif os.path.exists(f):
        os.remove(f)
    return len(new), frags, errors


def main(argv):
    fix = "--fix" in argv
    nums = [a for a in argv if not a.startswith("--")] or [f"{i:02d}" for i in range(1, 13)]
    total = frags = 0
    errors = []
    for num in nums:
        print(f"  мод {num}")
        n, fr, err = run_module(num, fix)
        total += n
        frags += fr
        errors += [f"мод {num}: {e}" for e in err]
    print(f"\nблоків із виводом: {total}, фрагментів: {frags}, помилок: {len(errors)}")
    for e in errors:
        print("  " + e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
