"""deliverables/final_report.md → docx, presentation_slides.md → pptx 변환 스크립트.

사용법 (저장소 루트에서):
    backend/.venv/Scripts/python.exe tools/generate_deliverables.py
"""

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor
from pptx import Presentation
from pptx.dml.color import RGBColor as PPTColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches
from pptx.util import Pt as PPt

ROOT = Path(__file__).resolve().parents[1]
REPORT_MD = ROOT / "deliverables" / "final_report.md"
SLIDES_MD = ROOT / "deliverables" / "presentation_slides.md"
REPORT_OUT = ROOT / "deliverables" / "P6_Schedule_Recovery_Copilot_Final_Report.docx"
SLIDES_OUT = ROOT / "deliverables" / "P6_Schedule_Recovery_Copilot_Presentation.pptx"

KOREAN_FONT = "맑은 고딕"
MONO_FONT = "Consolas"

BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


# ---------------------------------------------------------------- 공통 파싱


def strip_inline(text: str) -> str:
    """백틱 제거 + 링크는 텍스트만 남긴다."""
    text = text.replace("`", "")
    return LINK_RE.sub(r"\1", text)


def split_bold(text: str) -> list[tuple[str, bool]]:
    """**bold** 구간을 (텍스트, bold여부) 리스트로 분해."""
    parts: list[tuple[str, bool]] = []
    pos = 0
    for m in BOLD_RE.finditer(text):
        if m.start() > pos:
            parts.append((text[pos : m.start()], False))
        parts.append((m.group(1), True))
        pos = m.end()
    if pos < len(text):
        parts.append((text[pos:], False))
    return parts or [("", False)]


def parse_blocks(lines: list[str]) -> list[dict]:
    """마크다운 라인들을 블록(heading/para/bullet/number/quote/table/code/hr)으로 파싱."""
    blocks: list[dict] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("```"):
            code: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            blocks.append({"type": "code", "lines": code})
            continue

        if stripped == "---":
            blocks.append({"type": "hr"})
            i += 1
            continue

        if stripped.startswith("|"):
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            blocks.append({"type": "table", "rows": rows})
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            blocks.append({"type": "heading", "level": len(m.group(1)), "text": m.group(2)})
            i += 1
            continue

        if stripped.startswith("> "):
            quote: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            blocks.append({"type": "quote", "text": " ".join(q for q in quote if q)})
            continue

        bm = re.match(r"^(\s*)-\s+(.*)$", line)
        if bm:
            blocks.append({"type": "bullet", "level": 1 if len(bm.group(1)) >= 2 else 0, "text": bm.group(2)})
            i += 1
            continue

        nm = re.match(r"^\s*(\d+)[.)]\s+(.*)$", line)
        if nm:
            blocks.append({"type": "number", "text": nm.group(2)})
            i += 1
            continue

        blocks.append({"type": "para", "text": stripped})
        i += 1
    return blocks


# ---------------------------------------------------------------- DOCX


def set_run_font(run, name: str = KOREAN_FONT, size: float | None = None) -> None:
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn("w:eastAsia"), name)
    if size:
        run.font.size = Pt(size)


def add_formatted(paragraph, text: str, size: float | None = None, italic: bool = False) -> None:
    for chunk, bold in split_bold(strip_inline(text)):
        run = paragraph.add_run(chunk)
        run.bold = bold
        run.italic = italic
        set_run_font(run, size=size)


def build_docx() -> None:
    md = REPORT_MD.read_text(encoding="utf-8")
    blocks = parse_blocks(md.splitlines())

    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Mm(210), Mm(297)  # A4
    section.left_margin = section.right_margin = Mm(22)
    section.top_margin = section.bottom_margin = Mm(20)

    normal = doc.styles["Normal"]
    normal.font.name = KOREAN_FONT
    normal.font.size = Pt(10.5)
    normal.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), KOREAN_FONT)

    first_heading_seen = False
    for b in blocks:
        t = b["type"]
        if t == "hr":
            continue
        if t == "heading":
            level = b["level"]
            if level == 1 and not first_heading_seen:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_formatted(p, b["text"], size=20)
                for run in p.runs:
                    run.bold = True
                first_heading_seen = True
                continue
            sizes = {1: 18, 2: 15, 3: 12.5, 4: 11.5}
            p = doc.add_paragraph()
            p.space_before = Pt(10)
            add_formatted(p, b["text"], size=sizes.get(level, 11))
            for run in p.runs:
                run.bold = True
                if level <= 2:
                    run.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
        elif t == "para":
            text = b["text"]
            whole_italic = text.startswith("*") and text.endswith("*") and not text.startswith("**")
            if whole_italic:
                text = text.strip("*")
            p = doc.add_paragraph()
            add_formatted(p, text, italic=whole_italic)
        elif t == "quote":
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Mm(6)
            add_formatted(p, b["text"], italic=True)
            for run in p.runs:
                run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
        elif t == "bullet":
            p = doc.add_paragraph(style="List Bullet" + (" 2" if b["level"] else ""))
            add_formatted(p, b["text"])
        elif t == "number":
            p = doc.add_paragraph(style="List Number")
            add_formatted(p, b["text"])
        elif t == "code":
            for line in b["lines"]:
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(0)
                run = p.add_run(line)
                set_run_font(run, MONO_FONT, size=8.5)
        elif t == "table":
            rows = b["rows"]
            if not rows:
                continue
            cols = max(len(r) for r in rows)
            table = doc.add_table(rows=len(rows), cols=cols)
            table.style = "Table Grid"
            for ri, row in enumerate(rows):
                for ci in range(cols):
                    cell = table.cell(ri, ci)
                    cell.paragraphs[0].text = ""
                    add_formatted(cell.paragraphs[0], row[ci] if ci < len(row) else "", size=9)
                    if ri == 0:
                        for run in cell.paragraphs[0].runs:
                            run.bold = True
            doc.add_paragraph()

    doc.save(REPORT_OUT)
    print(f"[docx] {REPORT_OUT.name} 생성 완료")


# ---------------------------------------------------------------- PPTX

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
MARGIN = Inches(0.55)
BODY_W = SLIDE_W - MARGIN * 2

BG = PPTColor(0x10, 0x1A, 0x2E)
TITLE_C = PPTColor(0x7D, 0xD3, 0xFC)
TEXT_C = PPTColor(0xE6, 0xEC, 0xF5)
ACCENT = PPTColor(0xFB, 0xBF, 0x24)
TBL_HDR = PPTColor(0x1E, 0x3A, 0x5F)
TBL_ROW1 = PPTColor(0x16, 0x24, 0x3E)
TBL_ROW2 = PPTColor(0x1B, 0x2C, 0x4A)


def parse_slides() -> list[dict]:
    md = SLIDES_MD.read_text(encoding="utf-8")
    lines = md.splitlines()
    slides: list[dict] = []
    current: dict | None = None
    buf: list[str] = []

    def flush():
        nonlocal current, buf
        if current is not None:
            current["blocks"] = parse_blocks(buf)
            slides.append(current)
        buf = []

    for line in lines:
        m = re.match(r"^##\s+Slide\s+(\d+)\s+—\s+(.*)$", line.strip())
        if m:
            flush()
            current = {"num": int(m.group(1)), "title": m.group(2).strip(), "blocks": []}
        elif current is not None:
            buf.append(line)
    flush()
    return slides


def pp_set(run, size: float, bold: bool = False, color=TEXT_C, font: str = KOREAN_FONT, italic: bool = False):
    run.font.name = font
    run.font.size = PPt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    rpr = run._r.get_or_add_rPr()
    ea = rpr.makeelement(qn("a:ea"), {"typeface": font})
    for old in rpr.findall(qn("a:ea")):
        rpr.remove(old)
    rpr.append(ea)


def add_text_par(tf, text: str, size: float, bullet: bool = False, level: int = 0,
                 color=TEXT_C, italic: bool = False, first: bool = False):
    p = tf.paragraphs[0] if first and not tf.paragraphs[0].runs else tf.add_paragraph()
    p.level = level
    p.space_after = PPt(4)
    prefix = ("• " if level == 0 else "– ") if bullet else ""
    parts = split_bold(strip_inline(text))
    if prefix:
        r = p.add_run()
        r.text = prefix
        pp_set(r, size, color=color)
    for chunk, bold in parts:
        r = p.add_run()
        r.text = chunk
        pp_set(r, size, bold=bold, color=ACCENT if bold else color, italic=italic)
    return p


def estimate_height(block: dict, body_size: float) -> float:
    """블록 렌더링 높이(inch) 추정."""
    line_h = body_size / 72 * 1.5
    t = block["type"]
    if t == "table":
        return (len(block["rows"])) * 0.335 + 0.12
    if t == "code":
        return len(block["lines"]) * 0.155 + 0.1
    if t == "heading":
        return line_h * 1.5
    if t in ("bullet", "number", "para", "quote"):
        chars = len(block.get("text", ""))
        lines = max(1, (chars // 95) + 1)
        return line_h * lines
    return 0.0


def render_table(slide, rows: list[list[str]], top: float, font_size: float) -> float:
    n_rows, n_cols = len(rows), max(len(r) for r in rows)
    height = Inches(0.32 * n_rows)
    shape = slide.shapes.add_table(n_rows, n_cols, MARGIN, Inches(top), BODY_W, height)
    table = shape.table
    for ri, row in enumerate(rows):
        table.rows[ri].height = Inches(0.32)
        for ci in range(n_cols):
            cell = table.cell(ri, ci)
            cell.fill.solid()
            cell.fill.fore_color.rgb = TBL_HDR if ri == 0 else (TBL_ROW1 if ri % 2 else TBL_ROW2)
            cell.margin_top = cell.margin_bottom = Emu(18000)
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            for chunk, bold in split_bold(strip_inline(row[ci] if ci < len(row) else "")):
                r = p.add_run()
                r.text = chunk
                pp_set(r, font_size, bold=(ri == 0) or bold,
                       color=TITLE_C if ri == 0 else (ACCENT if bold else TEXT_C))
    return 0.32 * n_rows + 0.12


def build_pptx() -> None:
    slides_data = parse_slides()
    prs = Presentation()
    prs.slide_width, prs.slide_height = SLIDE_W, SLIDE_H
    blank = prs.slide_layouts[6]

    for sd in slides_data:
        slide = prs.slides.add_slide(blank)
        # 배경
        bg = slide.background.fill
        bg.solid()
        bg.fore_color.rgb = BG

        blocks = [b for b in sd["blocks"] if b["type"] != "hr"]
        # 발표 멘트 → 스피커 노트
        notes: list[str] = []
        content: list[dict] = []
        for b in blocks:
            text = b.get("text", "")
            plain = text.replace("**", "").strip()
            if plain.startswith("[발표 멘트]"):
                notes.append(strip_inline(plain.replace("[발표 멘트]", "").strip()))
            else:
                content.append(b)

        is_title_slide = sd["num"] == 1

        # 제목
        title_box = slide.shapes.add_textbox(MARGIN, Inches(0.28), BODY_W, Inches(0.85))
        tf = title_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        r = p.add_run()
        if is_title_slide:
            heading1 = next((b for b in content if b["type"] == "heading" and b["level"] == 1), None)
            r.text = strip_inline(heading1["text"]) if heading1 else sd["title"]
            pp_set(r, 34, bold=True, color=TITLE_C)
            content = [b for b in content if b is not heading1]
        else:
            r.text = f"{sd['num'] - 1}. {strip_inline(sd['title'])}" if sd["num"] > 1 else sd["title"]
            pp_set(r, 25, bold=True, color=TITLE_C)

        # 본문 사이즈 자동 조정: 총 추정 높이가 공간을 넘으면 축소
        avail = 7.5 - 1.25 - 0.3
        for body_size, tbl_size in ((15, 11), (13.5, 10), (12, 9), (11, 8.5), (10, 8)):
            total = sum(
                estimate_height(b, body_size) if b["type"] != "table" else len(b["rows"]) * 0.335 + 0.12
                for b in content
            )
            if total <= avail:
                break

        top = 1.25
        text_box = None
        tfb = None

        def new_textbox(at_top: float):
            box = slide.shapes.add_textbox(MARGIN, Inches(at_top), BODY_W, Inches(0.4))
            f = box.text_frame
            f.word_wrap = True
            return box, f

        for b in content:
            t = b["type"]
            if t == "table":
                text_box, tfb = None, None
                top += render_table(slide, b["rows"], top, tbl_size)
                continue
            if t == "code":
                text_box, tfb = None, None
                h = len(b["lines"]) * 0.155 + 0.1
                box = slide.shapes.add_textbox(MARGIN, Inches(top), BODY_W, Inches(h))
                f = box.text_frame
                f.word_wrap = False
                first = True
                for line in b["lines"]:
                    p = f.paragraphs[0] if first else f.add_paragraph()
                    first = False
                    p.space_after = PPt(0)
                    r = p.add_run()
                    r.text = line
                    pp_set(r, 9.5, color=PPTColor(0xB8, 0xE0, 0x9C), font=MONO_FONT)
                top += h
                continue

            if tfb is None:
                text_box, tfb = new_textbox(top)
                first_par = True
            else:
                first_par = False

            if t == "heading":
                size = 20 if b["level"] <= 2 else 16
                add_text_par(tfb, b["text"], size, color=TEXT_C if b["level"] > 2 else ACCENT, first=first_par)
                top += estimate_height(b, body_size)
            elif t == "quote":
                add_text_par(tfb, "❝ " + b["text"] + " ❞", body_size + 2, italic=True, color=ACCENT, first=first_par)
                top += estimate_height(b, body_size) * 1.3
            elif t == "bullet":
                add_text_par(tfb, b["text"], body_size, bullet=True, level=b["level"], first=first_par)
                top += estimate_height(b, body_size)
            elif t == "number":
                add_text_par(tfb, b["text"], body_size, bullet=True, first=first_par)
                top += estimate_height(b, body_size)
            else:
                add_text_par(tfb, b["text"], body_size, first=first_par)
                top += estimate_height(b, body_size)

        # 페이지 번호
        pn = slide.shapes.add_textbox(SLIDE_W - Inches(1.0), SLIDE_H - Inches(0.42), Inches(0.7), Inches(0.3))
        r = pn.text_frame.paragraphs[0].add_run()
        r.text = str(sd["num"])
        pp_set(r, 11, color=PPTColor(0x64, 0x74, 0x8B))
        pn.text_frame.paragraphs[0].alignment = PP_ALIGN.RIGHT

        if notes:
            slide.notes_slide.notes_text_frame.text = "\n\n".join(notes)

    prs.save(SLIDES_OUT)
    print(f"[pptx] {SLIDES_OUT.name} 생성 완료 ({len(slides_data)}장)")


if __name__ == "__main__":
    build_docx()
    build_pptx()
