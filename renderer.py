import io
import re
from typing import Any, Dict
from PIL import Image, ImageDraw, ImageFont

# ================= 主题色板 =================
# 每个主题提供: bg_canvas / bg_card / border_card / text_title / text_main /
# text_muted / text_sub / primary / primary_bg / primary_border /
# blockquote_bg / blockquote_bar / blockquote_text / code_bg / code_border /
# code_text / line / badge_bg / badge_border / badge_dot

def _hex(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


THEMES: Dict[str, Dict[str, Any]] = {
    "light": {  # 浅色蓝（原主题）
        "bg_canvas": _hex("F5F7FA"), "bg_card": _hex("FFFFFF"), "border_card": _hex("E2E8F0"),
        "text_title": _hex("0F172A"), "text_main": _hex("1E293B"), "text_muted": _hex("475569"),
        "text_sub": _hex("94A3B8"),
        "primary": _hex("2563EB"), "primary_bg": _hex("EFF6FF"), "primary_border": _hex("BFDBFE"),
        "blockquote_bg": _hex("F8FAFC"), "blockquote_bar": _hex("3B82F6"), "blockquote_text": _hex("334155"),
        "code_bg": _hex("F1F5F9"), "code_border": _hex("E2E8F0"), "code_text": _hex("0F172A"),
        "line": _hex("F1F5F9"), "badge_bg": _hex("F1F5F9"), "badge_border": _hex("E2E8F0"),
        "badge_dot": _hex("22C55E"),
    },
    "dark": {  # 暗夜
        "bg_canvas": _hex("0B1020"), "bg_card": _hex("141A2E"), "border_card": _hex("263049"),
        "text_title": _hex("F1F5F9"), "text_main": _hex("CBD5E1"), "text_muted": _hex("94A3B8"),
        "text_sub": _hex("64748B"),
        "primary": _hex("60A5FA"), "primary_bg": _hex("1E293B"), "primary_border": _hex("334155"),
        "blockquote_bg": _hex("1A2138"), "blockquote_bar": _hex("60A5FA"), "blockquote_text": _hex("CBD5E1"),
        "code_bg": _hex("0F172A"), "code_border": _hex("263049"), "code_text": _hex("E2E8F0"),
        "line": _hex("263049"), "badge_bg": _hex("1E293B"), "badge_border": _hex("334155"),
        "badge_dot": _hex("4ADE80"),
    },
    "warm": {  # 暖阳橙
        "bg_canvas": _hex("FBF7F0"), "bg_card": _hex("FFFFFF"), "border_card": _hex("F0E4D4"),
        "text_title": _hex("292524"), "text_main": _hex("44403C"), "text_muted": _hex("78716C"),
        "text_sub": _hex("A8A29E"),
        "primary": _hex("EA580C"), "primary_bg": _hex("FFF7ED"), "primary_border": _hex("FED7AA"),
        "blockquote_bg": _hex("FFFBEB"), "blockquote_bar": _hex("F59E0B"), "blockquote_text": _hex("57534E"),
        "code_bg": _hex("FAF5EE"), "code_border": _hex("EDE0D0"), "code_text": _hex("44403C"),
        "line": _hex("F5EDE3"), "badge_bg": _hex("FFF7ED"), "badge_border": _hex("FED7AA"),
        "badge_dot": _hex("22C55E"),
    },
    "sakura": {  # 樱粉
        "bg_canvas": _hex("FDF4F7"), "bg_card": _hex("FFFFFF"), "border_card": _hex("F5D0DC"),
        "text_title": _hex("3F1D2B"), "text_main": _hex("4A2537"), "text_muted": _hex("8B5A6E"),
        "text_sub": _hex("C48CA2"),
        "primary": _hex("DB2777"), "primary_bg": _hex("FDF2F8"), "primary_border": _hex("FBCFE8"),
        "blockquote_bg": _hex("FDF2F8"), "blockquote_bar": _hex("EC4899"), "blockquote_text": _hex("5B2A42"),
        "code_bg": _hex("FBEEF4"), "code_border": _hex("F5D0DC"), "code_text": _hex("4A2537"),
        "line": _hex("F9E2EB"), "badge_bg": _hex("FDF2F8"), "badge_border": _hex("FBCFE8"),
        "badge_dot": _hex("22C55E"),
    },
    "mint": {  # 薄荷绿
        "bg_canvas": _hex("F0FAF7"), "bg_card": _hex("FFFFFF"), "border_card": _hex("CFE8DF"),
        "text_title": _hex("0F2A22"), "text_main": _hex("1A3A32"), "text_muted": _hex("4B6B62"),
        "text_sub": _hex("8BB0A5"),
        "primary": _hex("0D9488"), "primary_bg": _hex("F0FDFA"), "primary_border": _hex("99F6E4"),
        "blockquote_bg": _hex("F0FDF9"), "blockquote_bar": _hex("14B8A6"), "blockquote_text": _hex("24473F"),
        "code_bg": _hex("ECF8F4"), "code_border": _hex("D2EAE2"), "code_text": _hex("1A3A32"),
        "line": _hex("DEF0EA"), "badge_bg": _hex("F0FDFA"), "badge_border": _hex("99F6E4"),
        "badge_dot": _hex("22C55E"),
    },
    "grape": {  # 葡萄紫
        "bg_canvas": _hex("F6F4FB"), "bg_card": _hex("FFFFFF"), "border_card": _hex("E0D9F0"),
        "text_title": _hex("251B3D"), "text_main": _hex("352B52"), "text_muted": _hex("6B5E8F"),
        "text_sub": _hex("A496C4"),
        "primary": _hex("7C3AED"), "primary_bg": _hex("F5F3FF"), "primary_border": _hex("DDD6FE"),
        "blockquote_bg": _hex("F5F3FF"), "blockquote_bar": _hex("8B5CF6"), "blockquote_text": _hex("403360"),
        "code_bg": _hex("F3F0FA"), "code_border": _hex("E0D9F0"), "code_text": _hex("352B52"),
        "line": _hex("EDE8F6"), "badge_bg": _hex("F5F3FF"), "badge_border": _hex("DDD6FE"),
        "badge_dot": _hex("22C55E"),
    },
}

DEFAULT_THEME = "light"


def get_theme(name: str) -> dict:
    t = THEMES.get(str(name or "").strip().lower())
    return t if t is not None else THEMES[DEFAULT_THEME]


def get_fonts(scale: int = 2):
    font_paths = [
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "msyh.ttc",
        "simhei.ttf",
        "/usr/share/fonts/opentype/unifont/unifont.otf",
    ]
    for p in font_paths:
        try:
            return {
                "title": ImageFont.truetype(p, int(16 * scale)),
                "h2": ImageFont.truetype(p, int(14 * scale)),
                "h3": ImageFont.truetype(p, int(13 * scale)),
                "body": ImageFont.truetype(p, int(12 * scale)),
                "body_bold": ImageFont.truetype(p, int(12 * scale)),
                "code": ImageFont.truetype(p, int(11 * scale)),
                "badge": ImageFont.truetype(p, int(10 * scale)),
                "footer": ImageFont.truetype(p, int(10 * scale)),
            }
        except Exception:
            continue
    def_font = ImageFont.load_default()
    return {k: def_font for k in ["title", "h2", "h3", "body", "body_bold", "code", "badge", "footer"]}


def clean_inline_markdown(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"`(.*?)`", r"\1", text)
    return text


def wrap_text_smart(draw, text: str, font, max_width: int):
    """支持中英文混排的智能折行算法"""
    if not text:
        return []
    lines = []
    for para in text.split("\n"):
        if not para:
            lines.append("")
            continue
        tokens = re.findall(r"[一-龥]|[a-zA-Z0-9_\-\./:\\]+|\s+|[^\s\w]", para)
        if not tokens:
            lines.append(para)
            continue
        cur_str = ""
        for tok in tokens:
            test_str = cur_str + tok
            bbox = draw.textbbox((0, 0), test_str, font=font)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                cur_str = test_str
            else:
                if cur_str.strip():
                    lines.append(cur_str.strip())
                    cur_str = tok.lstrip()
                else:
                    for ch in tok:
                        t2 = cur_str + ch
                        b2 = draw.textbbox((0, 0), t2, font=font)
                        if b2[2] - b2[0] <= max_width:
                            cur_str = t2
                        else:
                            lines.append(cur_str.strip())
                            cur_str = ch
        if cur_str.strip():
            lines.append(cur_str.strip())
    return lines


def parse_markdown_blocks(md_text: str):
    raw_lines = md_text.strip().split("\n")
    blocks = []
    in_code_block = False
    code_lines = []
    in_quote = False
    quote_lines = []

    def flush_quote():
        nonlocal in_quote, quote_lines
        if quote_lines:
            blocks.append({"type": "blockquote", "text": "\n".join(quote_lines)})
            quote_lines = []
        in_quote = False

    for line in raw_lines:
        line_s = line.strip()
        if line_s.startswith("```"):
            if in_code_block:
                blocks.append({"type": "code_block", "text": "\n".join(code_lines)})
                code_lines = []
                in_code_block = False
            else:
                flush_quote()
                in_code_block = True
            continue
        if in_code_block:
            code_lines.append(line)
            continue
        if line_s.startswith(">"):
            in_quote = True
            quote_lines.append(clean_inline_markdown(line_s[1:].strip()))
            continue
        else:
            flush_quote()
        if not line_s:
            blocks.append({"type": "spacing", "height": 6})
            continue
        if re.match(r"^[-*_]{3,}$", line_s):
            blocks.append({"type": "divider"})
            continue
        if line_s.startswith("|") and line_s.count("|") >= 2:
            cells = [c.strip() for c in line_s.strip().strip("|").split("|")]
            if cells and all(re.match(r"^:?-+:?$", c) for c in cells):
                continue
            cells = [clean_inline_markdown(c) for c in cells if c]
            if cells:
                blocks.append({"type": "paragraph", "text": "　·　".join(cells)})
            continue
        if line_s.startswith("## "):
            blocks.append({"type": "h2", "text": clean_inline_markdown(line_s[3:].strip())})
        elif line_s.startswith("### "):
            blocks.append({"type": "h3", "text": clean_inline_markdown(line_s[4:].strip())})
        elif line_s.startswith("#### "):
            blocks.append({"type": "h3", "text": clean_inline_markdown(line_s[5:].strip())})
        elif re.match(r"^\d+[\.、]\s*", line_s):
            m = re.match(r"^(\d+)[\.、]\s*(.*)$", line_s)
            blocks.append({"type": "ordered_list", "num": m.group(1), "text": clean_inline_markdown(m.group(2).strip())})
        elif re.match(r"^[-*•]\s+", line_s):
            m = re.match(r"^[-*•]\s+(.*)$", line_s)
            blocks.append({"type": "unordered_list", "text": clean_inline_markdown(m.group(1).strip())})
        else:
            blocks.append({"type": "paragraph", "text": clean_inline_markdown(line_s)})

    flush_quote()
    if in_code_block and code_lines:
        blocks.append({"type": "code_block", "text": "\n".join(code_lines)})
    return blocks


def render_natural_knowledge_card(
    question: str,
    markdown_content: str,
    model_tag: str = "MaiBot",
    footer_text: str = "麦麦 · 知识看板",
    footer_right_text: str = "智能知识生成 · 仅供参考",
    header_text: str = "",
    theme: str = "light",
) -> bytes:
    T = get_theme(theme)
    SCALE = 2
    WIDTH = 760 * SCALE
    fonts = get_fonts(SCALE)

    dummy_img = Image.new("RGBA", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)

    CARD_PAD_X = 36 * SCALE
    CONTENT_W = WIDTH - 2 * (16 * SCALE) - 2 * CARD_PAD_X

    blocks = parse_markdown_blocks(markdown_content)
    parsed_blocks = []
    body_height = 0

    for b in blocks:
        b_type = b["type"]
        if b_type == "spacing":
            h = b["height"] * SCALE
            parsed_blocks.append({"type": "spacing", "h": h})
            body_height += h
        elif b_type == "divider":
            h = 18 * SCALE
            parsed_blocks.append({"type": "divider", "h": h})
            body_height += h
        elif b_type == "h2":
            lines = wrap_text_smart(dummy_draw, b["text"], fonts["h2"], CONTENT_W - 20 * SCALE)
            h = (len(lines) * 26 + 18) * SCALE
            parsed_blocks.append({"type": "h2", "lines": lines, "h": h})
            body_height += h
        elif b_type == "h3":
            lines = wrap_text_smart(dummy_draw, b["text"], fonts["h3"], CONTENT_W - 16 * SCALE)
            h = (len(lines) * 24 + 14) * SCALE
            parsed_blocks.append({"type": "h3", "lines": lines, "h": h})
            body_height += h
        elif b_type == "paragraph":
            lines = wrap_text_smart(dummy_draw, b["text"], fonts["body"], CONTENT_W)
            h = (len(lines) * 23 + 10) * SCALE
            parsed_blocks.append({"type": "paragraph", "lines": lines, "h": h})
            body_height += h
        elif b_type == "unordered_list":
            lines = wrap_text_smart(dummy_draw, b["text"], fonts["body"], CONTENT_W - 22 * SCALE)
            h = (len(lines) * 23 + 6) * SCALE
            parsed_blocks.append({"type": "unordered_list", "lines": lines, "h": h})
            body_height += h
        elif b_type == "ordered_list":
            lines = wrap_text_smart(dummy_draw, b["text"], fonts["body"], CONTENT_W - 26 * SCALE)
            h = (len(lines) * 23 + 6) * SCALE
            parsed_blocks.append({"type": "ordered_list", "num": b["num"], "lines": lines, "h": h})
            body_height += h
        elif b_type == "blockquote":
            lines = wrap_text_smart(dummy_draw, b["text"], fonts["body"], CONTENT_W - 32 * SCALE)
            h = (len(lines) * 23 + 22) * SCALE
            parsed_blocks.append({"type": "blockquote", "lines": lines, "h": h})
            body_height += h
        elif b_type == "code_block":
            lines = wrap_text_smart(dummy_draw, b["text"], fonts["code"], CONTENT_W - 32 * SCALE)
            h = (len(lines) * 21 + 24) * SCALE
            parsed_blocks.append({"type": "code_block", "lines": lines, "h": h})
            body_height += h

    # Header 测量
    q_font = fonts["title"]
    tag_text = str(model_tag or "MaiBot")
    badge_font = fonts["badge"]
    max_tag_w = 170 * SCALE
    tag_draw = tag_text
    while tag_draw and dummy_draw.textbbox((0, 0), tag_draw + "…", font=badge_font)[2] > max_tag_w:
        tag_draw = tag_draw[:-1]
    if tag_draw != tag_text:
        tag_draw = tag_draw.rstrip() + "…"
    tag_w = dummy_draw.textbbox((0, 0), tag_draw, font=badge_font)[2]
    badge_w = tag_w + 30 * SCALE
    q_avail_w = CONTENT_W - (26 + 10) * SCALE - badge_w - 20 * SCALE
    display_header = (header_text or "").strip() or question
    clean_q = clean_inline_markdown(display_header)
    q_lines = wrap_text_smart(dummy_draw, clean_q, q_font, q_avail_w)
    if len(q_lines) > 3:
        q_lines = q_lines[:3]
        last = q_lines[-1].rstrip()
        while last and dummy_draw.textbbox((0, 0), last + "…", font=q_font)[2] > q_avail_w:
            last = last[:-1].rstrip()
        q_lines[-1] = last + "…"
    if not q_lines:
        q_lines = ["提问与解答"]
    header_h = (max(len(q_lines) * 28 + 24, 52)) * SCALE

    FOOTER_H = 46 * SCALE
    PADDING_OUTER = 16 * SCALE

    TOTAL_HEIGHT = PADDING_OUTER * 2 + header_h + 16 * SCALE + body_height + FOOTER_H + 20 * SCALE

    img = Image.new("RGBA", (WIDTH, TOTAL_HEIGHT), T["bg_canvas"])
    draw = ImageDraw.Draw(img)

    card_rect = [PADDING_OUTER, PADDING_OUTER, WIDTH - PADDING_OUTER, TOTAL_HEIGHT - PADDING_OUTER]
    draw.rounded_rectangle(card_rect, radius=14 * SCALE, fill=T["bg_card"], outline=T["border_card"], width=1 * SCALE)

    curr_y = PADDING_OUTER + 24 * SCALE
    card_left = PADDING_OUTER + CARD_PAD_X
    card_right = WIDTH - PADDING_OUTER - CARD_PAD_X

    # 1. Header
    q_tag_w = 26 * SCALE
    q_tag_h = 24 * SCALE
    draw.rounded_rectangle([card_left, curr_y, card_left + q_tag_w, curr_y + q_tag_h],
                           radius=5 * SCALE, fill=T["primary_bg"], outline=T["primary_border"], width=1 * SCALE)
    draw.text((card_left + 7 * SCALE, curr_y + 3 * SCALE), "Q", fill=T["primary"], font=fonts["h3"])

    q_text_x = card_left + q_tag_w + 10 * SCALE
    t_y = curr_y + 1 * SCALE
    for ql in q_lines:
        draw.text((q_text_x, t_y), ql, fill=T["text_title"], font=q_font)
        t_y += 28 * SCALE

    # Badge（宽度自适应文字，超长截断）
    badge_x0 = card_right - badge_w
    badge_rect = [badge_x0, curr_y + 2 * SCALE, card_right, curr_y + 26 * SCALE]
    draw.rounded_rectangle(badge_rect, radius=12 * SCALE, fill=T["badge_bg"], outline=T["badge_border"], width=1 * SCALE)
    draw.ellipse([badge_rect[0] + 8 * SCALE, curr_y + 11 * SCALE, badge_rect[0] + 14 * SCALE, curr_y + 17 * SCALE],
                 fill=T["badge_dot"])
    draw.text((badge_rect[0] + 19 * SCALE, curr_y + 5 * SCALE), tag_draw, fill=T["text_muted"], font=fonts["badge"])

    curr_y += header_h
    draw.line([(card_left, curr_y), (card_right, curr_y)], fill=T["line"], width=1 * SCALE)
    curr_y += 20 * SCALE

    # 2. Body
    for b in parsed_blocks:
        b_type = b["type"]
        if b_type == "spacing":
            curr_y += b["h"]
        elif b_type == "divider":
            draw.line([(card_left, curr_y + 8 * SCALE), (card_right, curr_y + 8 * SCALE)], fill=T["line"], width=1 * SCALE)
            curr_y += b["h"]
        elif b_type == "h2":
            draw.rounded_rectangle([card_left, curr_y + 4 * SCALE, card_left + 4 * SCALE, curr_y + 20 * SCALE],
                                   radius=2 * SCALE, fill=T["primary"])
            h_y = curr_y
            for l in b["lines"]:
                draw.text((card_left + 12 * SCALE, h_y), l, fill=T["text_title"], font=fonts["h2"])
                h_y += 26 * SCALE
            curr_y += b["h"]
        elif b_type == "h3":
            draw.rounded_rectangle([card_left, curr_y + 3 * SCALE, card_left + 3 * SCALE, curr_y + 17 * SCALE],
                                   radius=2 * SCALE, fill=T["primary"])
            h_y = curr_y
            for l in b["lines"]:
                draw.text((card_left + 10 * SCALE, h_y), l, fill=T["text_main"], font=fonts["h3"])
                h_y += 24 * SCALE
            curr_y += b["h"]
        elif b_type == "paragraph":
            p_y = curr_y
            for l in b["lines"]:
                draw.text((card_left, p_y), l, fill=T["text_main"], font=fonts["body"])
                p_y += 23 * SCALE
            curr_y += b["h"]
        elif b_type == "unordered_list":
            dot_r = 2.5 * SCALE
            dot_cx = card_left + 6 * SCALE
            dot_cy = curr_y + 10 * SCALE
            draw.ellipse([dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r], fill=T["primary"])
            l_y = curr_y
            for l in b["lines"]:
                draw.text((card_left + 18 * SCALE, l_y), l, fill=T["text_main"], font=fonts["body"])
                l_y += 23 * SCALE
            curr_y += b["h"]
        elif b_type == "ordered_list":
            num_str = b["num"]
            n_w = 16 * SCALE
            n_h = 16 * SCALE
            draw.rounded_rectangle([card_left, curr_y + 3 * SCALE, card_left + n_w, curr_y + 3 * SCALE + n_h],
                                   radius=4 * SCALE, fill=T["primary_bg"], outline=T["primary_border"], width=1 * SCALE)
            draw.text((card_left + 4 * SCALE, curr_y + 2 * SCALE), num_str, fill=T["primary"], font=fonts["badge"])
            l_y = curr_y
            for l in b["lines"]:
                draw.text((card_left + 24 * SCALE, l_y), l, fill=T["text_main"], font=fonts["body"])
                l_y += 23 * SCALE
            curr_y += b["h"]
        elif b_type == "blockquote":
            bq_h = b["h"] - 8 * SCALE
            draw.rounded_rectangle([card_left, curr_y, card_right, curr_y + bq_h],
                                   radius=6 * SCALE, fill=T["blockquote_bg"])
            draw.rounded_rectangle([card_left, curr_y, card_left + 4 * SCALE, curr_y + bq_h],
                                   radius=2 * SCALE, fill=T["blockquote_bar"])
            bq_y = curr_y + 10 * SCALE
            for l in b["lines"]:
                draw.text((card_left + 16 * SCALE, bq_y), l, fill=T["blockquote_text"], font=fonts["body"])
                bq_y += 23 * SCALE
            curr_y += b["h"]
        elif b_type == "code_block":
            cb_h = b["h"] - 8 * SCALE
            draw.rounded_rectangle([card_left, curr_y, card_right, curr_y + cb_h],
                                   radius=8 * SCALE, fill=T["code_bg"], outline=T["code_border"], width=1 * SCALE)
            cb_y = curr_y + 10 * SCALE
            for l in b["lines"]:
                draw.text((card_left + 14 * SCALE, cb_y), l, fill=T["code_text"], font=fonts["code"])
                cb_y += 21 * SCALE
            curr_y += b["h"]

    # 3. Footer
    curr_y = TOTAL_HEIGHT - PADDING_OUTER - FOOTER_H + 6 * SCALE
    draw.line([(card_left, curr_y), (card_right, curr_y)], fill=T["line"], width=1 * SCALE)
    curr_y += 14 * SCALE

    draw.text((card_left, curr_y), footer_text, fill=T["text_sub"], font=fonts["footer"])

    right_text = footer_right_text
    r_bbox = draw.textbbox((0, 0), right_text, font=fonts["footer"])
    r_w = r_bbox[2] - r_bbox[0]
    draw.text((card_right - r_w, curr_y), right_text, fill=T["text_sub"], font=fonts["footer"])

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def render_qa_card(question: str, summary: str, points: list, footer: str = "麦麦 · 知识看板",
                   theme: str = "light") -> bytes:
    """旧接口适配"""
    md_parts = []
    if summary:
        md_parts.append(f"> {summary.strip()}\n")
    for pt in points or []:
        t = pt.get("title", "").strip()
        d = pt.get("desc", "").strip()
        if t:
            md_parts.append(f"## {t}")
        if d:
            md_parts.append(f"{d}\n")
    md_content = "\n".join(md_parts) if md_parts else (summary or "暂无详细内容")
    return render_natural_knowledge_card(question=question, markdown_content=md_content,
                                        footer_text=footer, theme=theme)
