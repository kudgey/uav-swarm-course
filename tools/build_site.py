#!/usr/bin/env python3
"""Складання HTML-версії курсу з тих самих джерел, що йдуть у Gamma.

`gamma_course/decks_new/modNN.md` — єдине джерело правди. Звідси:
  · `gen.py`        → колода Gamma (картки, закріплені URL картинок);
  · `build_site.py` → сторінка VitePress (секції, локальні картинки, віджети).

Що робить конвертер:
  · ділить джерело на картки по `---`, поважаючи огорожі ```;
  · картка «Частина N · …» стає розділом `##`, звичайна картка — `###`;
    так права колонка сторінки дає дворівневий зміст замість плаского;
  · `RAWBASE/xxx.png` → локальний `/figs/own/xxx.png`;
  · картинка разом із підписом «Джерело: …» загортається у <Figure>;
  · `> СХЕМА: A -> B -> C` → компонент <Flow> (у Gamma це діаграма, і там
    вона обрізалася до чотирьох вузлів; у HTML обмеження немає);
  · англійські alt-тексти (їх писали як пошукові запити для Gamma)
    замінює на українські з карти `alts.json`;
  · у названі місця вставляє інтерактивні віджети.

  python3 tools/build_site.py            # усі 10
  python3 tools/build_site.py 01 02      # вибірково
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
SRC = os.path.join(os.path.dirname(SITE), "gamma_course", "decks_new")
ALTS = os.path.join(SITE, ".vitepress", "alts.json")
OUTPUTS = os.path.join(SITE, ".vitepress", "outputs.json")

# Куди які віджети ставити: (модуль, точний заголовок картки) → тег компонента.
# Віджет додається в кінець картки, після її тексту.
WIDGETS: dict[tuple[str, str], str] = {
    ("01", "Результат коду: зв'язність залежить від радіуса"): "ConnectivityLab",
    ("02", "Результат коду: топологія проти часу"): "ConsensusLab",
    ("03", "Boids: три правила, з яких виникає рій"): "BoidsLab",
    ("06", "Розподіл штрафів між доданками"): "RewardLab",
    ("07", "Масштабування: навчили на восьми, полетіли сто двадцять вісім"): "ScalingLab",
    ("08", "Числовий приклад: як складаються вектори"): "PotentialFieldLab",
    ("04", "Результат коду: цінність поширюється від цілі"): "GridWorldLab",
    ("10", "Частина 2 · Як чесно показати результат"): "SeedsLab",
    ("05", "Результат коду: усі п'ять ігор одразу"): "MatrixGameLab",
    ("09", "Чого ця схема не гарантує"): "RobustnessLab",
    ("04", "Дослідження проти використання"): "EpsilonLab",
    ("03", "Щільніший граф гірше терпить затримки"): "DelayLab",
    ("08", "Зони відповідальності: розбиття Вороного"): "VoronoiLab",
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

    while i < len(lines):
        line = lines[i]

        if line.startswith("```"):
            closing = fence
            fence = not fence
            out.append(line)
            if closing:
                # Вивід програми вже є в джерелі окремою карткою «Результат…»,
                # тому другий раз його сюди не вставляємо: раніше через це
                # той самий текст друкувався на сторінці двічі поспіль, ще й
                # із службовим рядком збірки (ім'я PNG, розмір), якого код
                # не друкує. Звірку виводу з кодом робить tools/run_examples.py.
                if ctx.get("was_python"):
                    ctx["py"] += 1
                    ctx["was_python"] = False
            else:
                ctx["was_python"] = line.strip().startswith("```python")
            i += 1
            continue

        if fence:
            out.append(line)
            i += 1
            continue

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
            src = f"/figs/own/{name}"

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


def build(num, alts, figs_present, outputs):
    src = os.path.join(SRC, f"mod{num}.md")
    cards = split_cards(open(src, encoding="utf-8").read())
    missing, used_widgets = [], []
    ctx = {"num": num, "py": 0, "was_python": False, "outputs": outputs}

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

    return {
        "num": num, "title": title, "cards": len(cards), "parts": n_parts,
        "widgets": used_widgets, "runs": ctx["py"], "missing": missing, "chars": len(page),
    }


def main(argv):
    alts = json.load(open(ALTS, encoding="utf-8")) if os.path.exists(ALTS) else {}
    figs_dir = os.path.join(SITE, "public", "figs", "own")
    figs_present = {f.rsplit(".", 1)[0] for f in os.listdir(figs_dir) if f.endswith(".png")}
    outputs = json.load(open(OUTPUTS, encoding="utf-8")) if os.path.exists(OUTPUTS) else {}

    nums = argv or [f"{i:02d}" for i in range(1, 11)]
    total_missing, total_cards = [], 0
    for n in nums:
        r = build(n, alts, figs_present, outputs)
        w = ", ".join(sorted(set(r["widgets"]))) or "—"
        print(f"  {r['num']}  {r['cards']:>3} секцій  {r['parts']} частин  "
              f"{r['chars']:>6} симв.  віджети: {w}")
        total_missing += r["missing"]
        total_cards += r["cards"]
    if total_missing:
        print("\n  ВІДСУТНІ рисунки:", ", ".join(sorted(set(total_missing))))
    print(f"\nсторінок зібрано: {len(nums)}, секцій: {total_cards}")


if __name__ == "__main__":
    main(sys.argv[1:])
