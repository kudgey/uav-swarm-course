#!/usr/bin/env python3
"""Складання HTML-версії курсу з тих самих джерел, що йдуть у Gamma.

`gamma_course/decks_new/modNN.md` — єдине джерело правди. Звідси:
  · `gen.py`        → колода Gamma (картки, закріплені URL картинок);
  · `build_site.py` → сторінка VitePress (секції, локальні картинки, віджети).

Що робить конвертер:
  · ділить джерело на картки по `---`, поважаючи огорожі ```;
  · картка «Частина N · …» стає розділом `##`, звичайна картка — `###`;
    так права колонка сторінки дає дворівневий зміст замість плаского;
  · `RAWBASE/xxx.png` → локальний `/figs/own/xxx.png` або `/figs/ext/xxx.png`
    (запозичені рисунки — в `ext`, власні — в `own`);
  · картинка разом із підписом «Джерело: …» загортається у <Figure>;
  · `> СХЕМА: A -> B -> C` → компонент <Flow> (у Gamma це діаграма, і там
    вона обрізалася до чотирьох вузлів; у HTML обмеження немає);
  · англійські alt-тексти (їх писали як пошукові запити для Gamma)
    замінює на українські з карти `alts.json`;
  · у названі місця вставляє інтерактивні віджети;
  · блок ```python → <CodeFold> (код згорнутий, у шапці — що робить код,
    скільки рядків і скільки виконувався) + <RunOutput> (вивід видний завжди
    й під ним «На що дивитися»). Конвенція джерела:
        <!-- code: що робить код -->        ← обов'язково, рядком перед блоком
        ```python | ```python ext | ```python fragment
        ```text                             ← вивід (крім fragment)
        *На що дивитися: …*                 ← обов'язково для блоку з виводом
    Вивід у джерелі має збігатися з фактичним прогоном (tools/run_examples.py
    пише його в .vitepress/outputs/NN.json); інакше — помилка збірки.

  python3 tools/build_site.py            # усі 10
  python3 tools/build_site.py 01 02      # вибірково
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
SRC = os.path.join(os.path.dirname(SITE), "gamma_course", "decks_new")
ALTS = os.path.join(SITE, ".vitepress", "alts.json")
OUTPUTS = os.path.join(SITE, ".vitepress", "outputs")   # NN.json: фактичний вивід блоків

# Куди які віджети ставити: (модуль, точний заголовок картки) → тег компонента.
# Віджет додається в кінець картки, після її тексту.
WIDGETS: dict[tuple[str, str], str] = {
    ("01", "Результат коду: зв'язність залежить від радіуса"): "ConnectivityLab",
    ("02", "Результат коду: топологія проти часу"): "ConsensusLab",
    ("03", "Boids: три правила, з яких виникає рій"): "BoidsLab",
    ("06", "Внесок доданків у двох режимах польоту"): "RewardLab",
    ("08", "Масштабування: навчили на восьми, полетіли сто двадцять вісім"): "ScalingLab",
    ("10", "Числовий приклад: як складаються вектори"): "PotentialFieldLab",
    ("04", "Результат коду: цінність поширюється від цілі"): "GridWorldLab",
    ("12", "Частина 2 · Як чесно показати результат"): "SeedsLab",
    ("05", "Результат коду: усі п'ять ігор одразу"): "MatrixGameLab",
    ("11", "Чого ця схема не гарантує"): "RobustnessLab",
    ("04", "Дослідження проти використання"): "EpsilonLab",
    ("03", "Щільніший граф гірше терпить затримки"): "DelayLab",
    ("10", "Зони відповідальності: розбиття Вороного"): "VoronoiLab",
}


def split_cards(text):
    """Ділить на картки по рядку `---`, ігноруючи роздільники всередині ```-блоків."""
    cards, buf, fence = [], [], False
    for line in text.split("\n"):
        if line.startswith("```"):
            fence = not fence
        if line.strip() == "---" and not fence:
            cards.append("\n".join(buf).strip())
            buf = []
        else:
            buf.append(line)
    cards.append("\n".join(buf).strip())
    return [c for c in cards if c]


IMG = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$")
SOURCE = re.compile(r"^(Джерело[^:]*:.*)$")
SCHEMA = re.compile(r"^>\s*СХЕМА:\s*(.+)$")


TITLE = re.compile(r"^<!--\s*code:\s*(.+?)\s*-->\s*$")
LOOK = re.compile(r"^\*На що дивитися:.+\*\s*$")
CONTINUATION = "# продовження попереднього блоку"
NOTE_CONT = "*Продовження блоку вище: цей код виконується разом із попереднім.*"
RUNNABLE = ("python", "python ext")      # ext — потрібен пакет поза базовим стеком
FRAGMENT = "python fragment"             # не виконується, позначений як фрагмент
MAX_OUT_LINES = 25
RAW_DICT = re.compile(r"\{'[^']*':|\{\"[^\"]*\":")


def block_hash(code):
    """Хеш коду блоку — ключ в outputs/NN.json (спільний із run_examples.py)."""
    return hashlib.sha1(code.strip().encode("utf-8")).hexdigest()[:12]


def read_block(lines, i):
    """Блок коду з рядка i (```python…) разом із виводом і «На що дивитися».

    Повертає (lang, code, out, note, наступний індекс). out — рядки блоку
    ```text одразу після коду (через порожні рядки) або None; note — рядок
    «*На що дивитися: …*» одразу після виводу чи коду, або None.
    """
    lang = lines[i][3:].strip()
    j = i + 1
    while j < len(lines) and not lines[j].startswith("```"):
        j += 1
    code, nxt = lines[i + 1:j], j + 1

    def skip(k):
        while k < len(lines) and not lines[k].strip():
            k += 1
        return k

    out = None
    k = skip(nxt)
    if k < len(lines) and lines[k].strip() == "```text":
        e = k + 1
        while e < len(lines) and not lines[e].startswith("```"):
            e += 1
        out, nxt = lines[k + 1:e], e + 1
        k = skip(nxt)
    note = None
    if k < len(lines) and LOOK.match(lines[k].strip()):
        note, nxt = lines[k].strip(), k + 1
    return lang, code, out, note, nxt


def code_blocks(text):
    """Усі блоки python* джерела по порядку: [(lang, code, out, note, title)]."""
    lines, res, i, title = text.split("\n"), [], 0, None
    while i < len(lines):
        m = TITLE.match(lines[i])
        if m:
            title, i = m.group(1), i + 1
            continue
        if lines[i].startswith("```python"):
            lang, code, out, note, i = read_block(lines, i)
            res.append((lang, "\n".join(code), out, note, title))
            title = None
            continue
        if lines[i].startswith("```"):          # інші огорожі пропускаємо цілком
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                i += 1
        if lines[i if i < len(lines) else -1].strip():
            title = None
        i += 1
    return res


def attr(s):
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def emit_block(lang, code, out, note, title, ctx):
    """Блок python → <CodeFold> (згорнутий код) + <RunOutput> (вивід і «На що дивитися»)."""
    errs, head = ctx["errors"], (code[0][:50] if code else "(порожній)")
    res = []
    if code and code[0].strip() == CONTINUATION:
        res += ["", NOTE_CONT]
    if not title:
        errs.append(f"блок без «<!-- code: що робить код -->» перед ним: {head}")
        title = "Код"
    if lang not in RUNNABLE + (FRAGMENT,):
        errs.append(f"невідома мітка блоку «{lang}»: {head}")
    frag = lang == FRAGMENT
    rec = None
    if frag:
        ctx["fragments"] += 1
        if out is not None:
            errs.append(f"фрагмент «{title}» має вивід — фрагменти не виконуються")
    else:
        ctx["runnable"] += 1
        rec = ctx["outputs"].get(block_hash("\n".join(code)))
        if rec is None:
            errs.append(f"«{title}»: немає прогону — запустіть tools/run_examples.py {ctx['num']}")
        if out is None:
            errs.append(f"«{title}»: після коду немає блоку ```text із виводом")
        elif rec is not None and rec["out"].strip("\n") != "\n".join(out).strip("\n"):
            errs.append(f"«{title}»: вивід у джерелі не збігається з фактичним прогоном")
        if out is not None:
            if len(out) > MAX_OUT_LINES:
                errs.append(f"«{title}»: вивід {len(out)} рядків (> {MAX_OUT_LINES})")
            if RAW_DICT.search("\n".join(out)):
                errs.append(f"«{title}»: у виводі сирий dict — друкуйте таблицею")
        if not note:
            errs.append(f"«{title}»: після виводу немає рядка «*На що дивитися: …*»")
    sec = f' sec="{rec["sec"]}"' if rec and "sec" in rec else ""
    res += ["", f'<CodeFold title="{attr(title)}" :lines="{len(code)}"{sec}{" fragment" if frag else ""}>',
            "", "```python", *code, "```", "", "</CodeFold>", ""]
    if not frag and out is not None:
        res += ["<RunOutput>", "", "```text:no-line-numbers", *out, "```", ""]
        if note:
            res += ["<template #note>", "", note, "", "</template>", ""]
        res += ["</RunOutput>", ""]
    return res


def parse_flow(spec):
    """`A -> B -> C | підписи: x; y; z` → (вузли, підписи)."""
    labels = []
    if "|" in spec:
        spec, tail = spec.split("|", 1)
        tail = tail.strip()
        if ":" in tail:
            tail = tail.split(":", 1)[1]
        labels = [s.strip() for s in tail.split(";") if s.strip()]
    nodes = [s.strip() for s in re.split(r"->|→", spec) if s.strip()]
    return nodes, labels


def convert_card(card, alts, figs_present, missing, ctx):
    """Одна картка → секція сторінки."""
    lines = card.split("\n")
    out, i, fence = [], 0, False
    is_part = False
    title = None

    while i < len(lines):
        line = lines[i]

        m = TITLE.match(line) if not fence else None
        if m:
            title = m.group(1)
            i += 1
            continue

        if line.startswith("```python") and not fence:
            lang, code, got, note, i = read_block(lines, i)
            out += emit_block(lang, code, got, note, title, ctx)
            title = None
            continue

        if line.startswith("```"):
            fence = not fence
            out.append(line)
            i += 1
            continue

        if fence:
            out.append(line)
            i += 1
            continue

        if title is not None and line.strip():
            ctx["errors"].append(f"«<!-- code: {title} -->» стоїть не безпосередньо перед блоком коду")
            title = None

        m = SCHEMA.match(line.strip())
        if m:
            nodes, labels = parse_flow(m.group(1))
            attrs = json.dumps(nodes, ensure_ascii=False).replace('"', "&quot;")
            tag = f'<Flow :nodes="{attrs}"'
            if labels:
                lab = json.dumps(labels, ensure_ascii=False).replace('"', "&quot;")
                tag += f' :labels="{lab}"'
            out += ["", tag + " />", ""]
            i += 1
            continue

        m = IMG.match(line)
        if m:
            alt, src = m.group(1), m.group(2)
            name = src.rsplit("/", 1)[-1]
            if name.rsplit(".", 1)[0] not in figs_present:
                missing.append(name)
            # Запозичені рисунки лежать у figs/ext, власні — у figs/own.
            # Тека визначається наявністю файла, а не назвою.
            sub = "ext" if os.path.exists(
                os.path.join(SITE, "public", "figs", "ext", name)) else "own"
            src = f"/figs/{sub}/{name}"

            # підпис «Джерело: …» одразу під картинкою (можливо через порожній рядок)
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            caption = None
            if j < len(lines):
                c = SOURCE.match(lines[j].strip())
                if c:
                    caption = c.group(1)
                    i = j

            ua = alts.get(name)
            if ua:
                alt = ua
            body = caption if caption else alt
            alt_esc = alt.replace('"', "&quot;")
            out += ["", f'<Figure src="{src}" alt="{alt_esc}">', "", body, "", "</Figure>", ""]
            i += 1
            continue

        # заголовок картки стає заголовком секції
        if line.startswith("# "):
            head = line[2:].strip()
            is_part = head.startswith("Частина")
            out.append(("## " if is_part else "### ") + head)
            i += 1
            continue

        out.append(line)
        i += 1

    return "\n".join(out).strip(), is_part


def heading_of(card):
    for line in card.split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def build(num, alts, figs_present, errors):
    src = os.path.join(SRC, f"mod{num}.md")
    cards = split_cards(open(src, encoding="utf-8").read())
    missing, used_widgets = [], []
    f = os.path.join(OUTPUTS, f"{num}.json")
    outputs = json.load(open(f, encoding="utf-8")) if os.path.exists(f) else {}
    ctx = {"num": num, "runnable": 0, "fragments": 0, "outputs": outputs, "errors": []}

    first = cards[0]
    title = heading_of(first)
    body_first, _ = convert_card(first, alts, figs_present, missing, ctx)
    # титульна картка: заголовок лишається єдиним h1 сторінки
    body_first = body_first.replace("### " + title, "# " + title, 1)

    parts, n_parts = [body_first], 0
    for card in cards[1:]:
        head = heading_of(card)
        section, is_part = convert_card(card, alts, figs_present, missing, ctx)
        n_parts += is_part
        tag = WIDGETS.get((num, head))
        if tag:
            section += f"\n\n<{tag} />"
            used_widgets.append(tag)
        parts.append(section)

    page = "\n\n".join(parts) + "\n"
    front = "---\n" f'title: "{title}"\n' "outline: [2, 3]\n" "---\n\n"
    dst = os.path.join(SITE, "lectures", f"{num}.md")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "w", encoding="utf-8").write(front + page)

    errors += [f"мод {num}: {e}" for e in ctx["errors"]]
    return {
        "num": num, "title": title, "cards": len(cards), "parts": n_parts,
        "widgets": used_widgets, "runs": ctx["runnable"], "frags": ctx["fragments"],
        "missing": missing, "chars": len(page),
    }


def main(argv):
    alts = json.load(open(ALTS, encoding="utf-8")) if os.path.exists(ALTS) else {}
    # Рисунки живуть у двох теках: own — власні, ext — запозичені з джерел.
    figs_present = set()
    for sub in ("own", "ext"):
        d = os.path.join(SITE, "public", "figs", sub)
        if os.path.isdir(d):
            figs_present |= {f.rsplit(".", 1)[0]
                             for f in os.listdir(d) if f.endswith(".png")}
    nums = argv or [f"{i:02d}" for i in range(1, 13)]
    total_missing, total_cards, errors = [], 0, []
    for n in nums:
        r = build(n, alts, figs_present, errors)
        w = ", ".join(sorted(set(r["widgets"]))) or "—"
        code = f"код {r['runs']}+{r['frags']}ф" if r["runs"] + r["frags"] else "код —"
        print(f"  {r['num']}  {r['cards']:>3} секцій  {r['parts']} частин  "
              f"{r['chars']:>6} симв.  {code:10s} віджети: {w}")
        total_missing += r["missing"]
        total_cards += r["cards"]
    if total_missing:
        print("\n  ВІДСУТНІ рисунки:", ", ".join(sorted(set(total_missing))))
    print(f"\nсторінок зібрано: {len(nums)}, секцій: {total_cards}")
    if errors:
        print(f"\nПОМИЛКИ ({len(errors)}):")
        for e in errors:
            print("  " + e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
