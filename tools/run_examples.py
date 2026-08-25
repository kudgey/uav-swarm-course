#!/usr/bin/env python3
"""Запускає приклади коду з лекцій і звіряє фактичний вивід із написаним.

Мета не в тому, щоб «показати вивід» — його вже написано на картці. Мета в тому,
щоб довести, що написане число справді виходить із цього коду. Розбіжність
означає одне з двох: або код на слайді неповний, або число ніхто не перевіряв.

Блок ```python на картці — скорочений для слайда фрагмент; повна програма
лежить у `gamma_course/viz/mNN_code.py`. Запускаємо саме її і звіряємо stdout
із блоком ```text на картці «Результат …».

  python3 tools/run_examples.py            # усі модулі
  python3 tools/run_examples.py 01 04      # вибірково
  python3 tools/run_examples.py --write    # записати фактичний вивід у outputs.json
"""
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
COURSE = os.path.join(os.path.dirname(SITE), "gamma_course")
SRC = os.path.join(COURSE, "decks_new")
VIZ = os.path.join(COURSE, "viz")
OUTPUTS = os.path.join(SITE, ".vitepress", "outputs.json")

# Модуль → скрипт, який друкує вивід для картки «Результат …».
SCRIPTS = {
    "01": "m01_code.py", "02": "m02_code.py", "03": "m03_code.py",
    "04": "m04_code.py", "05": "m05_code.py", "06": "m06_code.py",
    "07": "m07_code.py", "08": "m08_metrics.py", "09": "m09_residual.py",
}
# Модуль 10 показує фрагменти архітектури мережі й кроку навчання —
# це ілюстрація форми коду, а не самодостатня програма.

PREFIX = (
    "import matplotlib\n"
    "matplotlib.use('Agg')\n"          # інакше на macOS спробує відкрити вікно
    "import matplotlib.pyplot as _plt\n"
    "_plt.show = lambda *a, **k: None\n"
)


def declared_of(mod):
    """Блоки ```text із карток «Результат …» — те, що написано на слайді."""
    text = open(os.path.join(SRC, f"mod{mod}.md"), encoding="utf-8").read()
    return re.findall(r"```text\n(.*?)```", text, re.S)


def run_script(name):
    """Запускає скрипт із viz/ у його ж теці; повертає (ok, stdout, stderr)."""
    path = os.path.join(VIZ, name)
    if not os.path.exists(path):
        return False, "", f"немає файлу {name}"
    try:
        r = subprocess.run([sys.executable, name], cwd=VIZ, capture_output=True,
                           text=True, timeout=600, env={**os.environ, "MPLBACKEND": "Agg"})
        return r.returncode == 0, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "перевищено ліміт 600 с"


# Рядок, який style.save() друкує про збережений PNG, — це журнал збірки
# рисунка, а не результат обчислення; на картку він не йде.
SAVED = re.compile(r"^\S+\.png\s+\d+x\d+\s+\d+\s*KB$")


def norm(s):
    """Рядки для порівняння: без кінцевих пробілів, порожніх і журналу збереження.

    Кратні пробіли всередині рядка стискаємо: на картці вирівнювання могли
    підправити руками, і це не привід вважати числа розбіжними.
    """
    out = []
    for ln in s.strip().split("\n"):
        ln = ln.rstrip()
        if not ln or SAVED.match(ln.strip()):
            continue
        out.append(re.sub(r"[ \t]{2,}", " ", ln))
    return out


def main(argv):
    write = "--write" in argv
    nums = [a for a in argv if a != "--write"] or [f"{i:02d}" for i in range(1, 11)]
    outputs = json.load(open(OUTPUTS, encoding="utf-8")) if os.path.exists(OUTPUTS) else {}

    total = ok_n = skip_n = fail_n = diff_n = 0
    for mod in nums:
        script = SCRIPTS.get(mod)
        if not script:
            skip_n += 1
            print(f"  мод {mod}  пропущено — на картках фрагменти, а не програма")
            continue
        total += 1
        ok, out, err = run_script(script)
        if not ok:
            fail_n += 1
            print(f"  мод {mod}  ПОМИЛКА ВИКОНАННЯ {script}")
            print("          " + (err.split("\n")[-1] if err else "без повідомлення"))
            continue
        outputs[f"{mod}.0"] = out
        declared = declared_of(mod)
        if not declared:
            ok_n += 1
            print(f"  мод {mod}  {script} виконано, на картці виводу немає")
            continue
        a, b = norm(out), norm(declared[0])
        if a == b:
            ok_n += 1
            print(f"  мод {mod}  {script}: збігається з карткою ({len(a)} рядків)")
        else:
            diff_n += 1
            print(f"  мод {mod}  {script}: РОЗБІЖНІСТЬ із карткою")
            for i in range(max(len(a), len(b))):
                x = a[i] if i < len(a) else "«рядка немає»"
                y = b[i] if i < len(b) else "«рядка немає»"
                if x != y:
                    print(f"          факт:   {x}")
                    print(f"          картка: {y}")

    if write:
        json.dump(outputs, open(OUTPUTS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\nзаписано {OUTPUTS}")

    print(f"\nскриптів {total}: збіглося {ok_n}, розбіжностей {diff_n}, "
          f"помилок {fail_n}, пропущено модулів {skip_n}")
    return 1 if (diff_n or fail_n) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
