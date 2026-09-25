#!/usr/bin/env python3
"""Inline scout of revisao-contrato: convert the contract to Markdown and check its numbering.

    python3 docx-scout.py <contrato.md|.txt|.docx> --out <saida>

Every finding anchors on a clause number, and the apply step edits by clause, so a contract
whose numbering did not survive conversion cannot be reviewed. For a `.docx` the numbering
Word renders lives in `w:numPr`, not in the text: when the text lost it, it is rebuilt once
from the paragraph's own `w:numPr` levels. The check then compares the count of
numbered-looking paragraphs in the Markdown against the count of paragraphs carrying `w:numPr`
in the source — directly or through their style. Fewer numbered than carrying means numbering
was lost (a style-numbered list is counted, not rebuilt) and the scout stops.

Exit 0: prints `contrato: <path of the Markdown to review>` and the numbering count.
Exit 3: no clause numbering, or fewer numbered paragraphs than `w:numPr` ones, even after the
rebuild — ask for a Markdown or plain-text export.
Exit 2: usage or read error.
"""

import argparse
import os
import re
import sys

NUMBERED = re.compile(r"^(?:#+\s*)?(?:\*\*)?\d+(?:\.\d+)*[.)]?\s")
MARK = "<!-- revisao-contrato: convertido de "


def count_numbered(lines):
    return sum(1 for line in lines if NUMBERED.match(line.strip()))


def read_text(path):
    with open(path, encoding="utf-8-sig") as fh:
        return fh.read().replace("﻿", "")


def docx_lines(path):
    """Paragraphs and table rows in body order; returns (lines, numbered_by_numPr), where the
    count takes paragraphs carrying a list `w:numPr` directly or through their paragraph style."""
    import docx  # python-docx
    from docx.oxml.ns import qn

    doc = docx.Document(path)
    formats = {}
    numbering = getattr(doc.part, "numbering_part", None)
    if numbering is not None:
        root = numbering.element
        abstract = {}
        for an in root.findall(qn("w:abstractNum")):
            levels = {}
            for lvl in an.findall(qn("w:lvl")):
                fmt = lvl.find(qn("w:numFmt"))
                levels[lvl.get(qn("w:ilvl"))] = fmt.get(qn("w:val")) if fmt is not None else "decimal"
            abstract[an.get(qn("w:abstractNumId"))] = levels
        for num in root.findall(qn("w:num")):
            ref = num.find(qn("w:abstractNumId"))
            if ref is not None:
                formats[num.get(qn("w:numId"))] = abstract.get(ref.get(qn("w:val")), {})

    def is_list(numid, ilvl):
        return numid not in (None, "0") and formats.get(numid, {}).get(str(ilvl), "decimal") not in ("bullet", "none")

    # Styles whose own pPr carries a numPr: their paragraphs render numbered with no numPr of their own.
    style_numbered = set()
    for st in doc.styles.element.findall(qn("w:style")):
        sppr = st.find(qn("w:pPr"))
        snum = sppr.find(qn("w:numPr")) if sppr is not None else None
        if snum is not None:
            sid, silvl = snum.find(qn("w:numId")), snum.find(qn("w:ilvl"))
            if is_list(sid.get(qn("w:val")) if sid is not None else None, silvl.get(qn("w:val")) if silvl is not None else 0):
                style_numbered.add(st.get(qn("w:styleId")))

    lines, numbered, counters = [], 0, []
    body = doc.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:tbl"):
            for row in child.iter(qn("w:tr")):
                cells = ["".join(t.text or "" for t in c.iter(qn("w:t"))).strip() for c in row.iter(qn("w:tc"))]
                lines.append("| " + " | ".join(cells) + " |")
            lines.append("")
            continue
        if child.tag != qn("w:p"):
            continue
        text = "".join(t.text or "" for t in child.iter(qn("w:t"))).strip()
        ppr = child.find(qn("w:pPr"))
        numpr = ppr.find(qn("w:numPr")) if ppr is not None else None
        style = ppr.find(qn("w:pStyle")) if ppr is not None else None
        prefix = ""
        if numpr is not None and text:
            ilvl_el, numid_el = numpr.find(qn("w:ilvl")), numpr.find(qn("w:numId"))
            ilvl = int(ilvl_el.get(qn("w:val"))) if ilvl_el is not None else 0
            numid = numid_el.get(qn("w:val")) if numid_el is not None else None
            if is_list(numid, ilvl):
                numbered += 1
                del counters[ilvl + 1:]
                while len(counters) <= ilvl:
                    counters.append(0)
                counters[ilvl] += 1
                prefix = ".".join(str(c or 1) for c in counters) + ". "
        if numpr is None and text and style is not None and style.get(qn("w:val")) in style_numbered:
            numbered += 1
        heading = ""
        if style is not None:
            m = re.match(r"(?i)heading\s*(\d)|t[ií]tulo\s*(\d)", style.get(qn("w:val")) or "")
            if m:
                heading = "#" * int(m.group(1) or m.group(2)) + " "
        lines.append((heading + (prefix if not NUMBERED.match(text) else "") + text) if text else "")
    return lines, numbered


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("contrato")
    ap.add_argument("--out", required=True, help="the review's output directory")
    opts = ap.parse_args(argv)
    src = opts.contrato
    if not os.path.isfile(src):
        print(f"erro: {src} não é um arquivo regular", file=sys.stderr)
        return 2
    ext = os.path.splitext(src)[1].lower()
    try:
        if ext in (".md", ".txt"):
            lines = read_text(src).splitlines()
            found = count_numbered(lines)
            if not found:
                print(f"sem numeração de cláusulas em {src}: peça um export em Markdown ou texto com a numeração", file=sys.stderr)
                return 3
            print(f"contrato: {src}")
            print(f"numeracao: {found} parágrafos numerados")
            return 0
        if ext != ".docx":
            print(f"erro: formato {ext or '(nenhum)'} fora do escopo; use .md, .txt ou .docx", file=sys.stderr)
            return 2
        lines, by_numpr = docx_lines(src)
    except (OSError, UnicodeDecodeError, ValueError, KeyError) as exc:
        print(f"erro ao ler {src}: {exc}", file=sys.stderr)
        return 2
    except ImportError:
        print("erro: python-docx ausente (pip install python-docx)", file=sys.stderr)
        return 2
    found = count_numbered(lines)
    if not found or found < by_numpr:
        print(f"numeração perdida em {src}: {found} parágrafos numerados, {by_numpr} com w:numPr; "
              f"peça um export em Markdown ou texto com a numeração", file=sys.stderr)
        return 3
    os.makedirs(opts.out, exist_ok=True)
    dest = os.path.join(opts.out, "contrato.md")
    if os.path.exists(dest):
        if not os.path.isfile(dest) or not read_text(dest).startswith(MARK):
            print(f"erro: {dest} existe e não foi escrito por este script; escolha outra --out", file=sys.stderr)
            return 2
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(f"{MARK}{os.path.basename(src)} -->\n\n" + "\n".join(lines) + "\n")
    print(f"contrato: {dest}")
    print(f"numeracao: {found} parágrafos numerados (w:numPr: {by_numpr})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
