"""Renders a DukaanAI invoice as a polished, single-page PDF straight into an
in-memory buffer (no temp files on disk). Layout/colours mirror the web
app's own design system (see frontend/src/index.css) so a printed invoice
looks like it came from the same product as the dashboard.
"""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

# --- brand palette (matches frontend/src/index.css :root) -------------------
INK = HexColor("#211d2b")
INK_SOFT = HexColor("#5f5870")
INK_FAINT = HexColor("#9b94a8")
LINE = HexColor("#e6e2ee")
CARD = white
ZEBRA = HexColor("#f6f4fb")
NOTE_BG = HexColor("#f3effc")

LAVENDER_DEEP = HexColor("#7c5cf0")
BLUE_DEEP = HexColor("#2b54d4")
MINT_DEEP = HexColor("#0fa776")
CORAL_DEEP = HexColor("#e8563a")
YELLOW_DEEP = HexColor("#b47d08")

STATUS_STYLE = {
    "paid": MINT_DEEP,
    "unpaid": CORAL_DEEP,
    "partial": YELLOW_DEEP,
}

F_REG = "Helvetica"
F_BOLD = "Helvetica-Bold"
F_ITALIC = "Helvetica-Oblique"

MARGIN = 16 * mm
PAGE_W, PAGE_H = A4
CONTENT_W = PAGE_W - 2 * MARGIN

# --- Unicode font for the rupee sign -----------------------------------------
# ReportLab's built-in Helvetica is a base-14 PDF font limited to
# WinAnsiEncoding, which has no glyph for ₹ (U+20B9) — drawing it would show
# a blank/"tofu" box. macOS's own "Arial Unicode.ttf" predates the 2010
# Unicode release that added the Rupee sign and doesn't have it either
# (confirmed by inspecting its cmap). Bundle a real, current Unicode font
# instead of depending on whatever happens to be installed on the machine
# running the backend.
_CURRENCY_FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "NotoSans-Regular.ttf"
_CURRENCY_FONT = None


def _currency_font() -> str:
    global _CURRENCY_FONT
    if _CURRENCY_FONT is not None:
        return _CURRENCY_FONT

    if _CURRENCY_FONT_PATH.exists():
        try:
            pdfmetrics.registerFont(TTFont("InvoiceCurrency", str(_CURRENCY_FONT_PATH)))
            _CURRENCY_FONT = "InvoiceCurrency"
            return _CURRENCY_FONT
        except Exception:
            pass

    _CURRENCY_FONT = ""  # falls back to "Rs." text in plain Helvetica
    return _CURRENCY_FONT


def rupee(amount) -> str:
    amount = amount or 0
    if _currency_font():
        return f"₹{amount:,.2f}"
    return f"Rs. {amount:,.2f}"


def _currency_draw_font(bold: bool) -> str:
    """The font to actually draw a rupee-formatted string with."""
    cf = _currency_font()
    if cf:
        return cf
    return F_BOLD if bold else F_REG


def _draw_string(pdf, x, y, text, font, size, bold=False, right=False, center=False):
    """Draws text, faux-bolding it (a slightly offset second pass) when the
    font itself has no separate bold weight registered — used for the one
    Unicode currency font, which is only bundled at a single (regular)
    weight."""
    pdf.setFont(font, size)
    draw = pdf.drawRightString if right else pdf.drawCentredString if center else pdf.drawString
    draw(x, y, text)
    if bold and font not in (F_BOLD,):
        draw(x + 0.35, y, text)


# --- small drawing helpers ---------------------------------------------------

def _hex_to_rgb(color):
    return color.red, color.green, color.blue


def _gradient_rect(pdf, x, y, w, h, color_start, color_end, steps=48, horizontal=True):
    r1, g1, b1 = _hex_to_rgb(color_start)
    r2, g2, b2 = _hex_to_rgb(color_end)
    seg = (w if horizontal else h) / steps
    for i in range(steps):
        t = i / (steps - 1) if steps > 1 else 0
        pdf.setFillColorRGB(r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t)
        if horizontal:
            pdf.rect(x + i * seg, y, seg + 0.6, h, stroke=0, fill=1)
        else:
            pdf.rect(x, y + i * seg, w, seg + 0.6, stroke=0, fill=1)


def _sparkle(pdf, cx, cy, size, color):
    """A tiny 4-point sparkle glyph, echoing the app's AI/sparkle icon."""
    pdf.saveState()
    pdf.setFillColor(color)
    p = pdf.beginPath()
    p.moveTo(cx, cy + size)
    p.curveTo(cx + size * 0.15, cy + size * 0.15, cx + size * 0.15, cy + size * 0.15, cx + size, cy)
    p.curveTo(cx + size * 0.15, cy - size * 0.15, cx + size * 0.15, cy - size * 0.15, cx, cy - size)
    p.curveTo(cx - size * 0.15, cy - size * 0.15, cx - size * 0.15, cy - size * 0.15, cx - size, cy)
    p.curveTo(cx - size * 0.15, cy + size * 0.15, cx - size * 0.15, cy + size * 0.15, cx, cy + size)
    p.close()
    pdf.drawPath(p, stroke=0, fill=1)
    pdf.restoreState()


def _wrap(text: str, font: str, size: float, max_width: float) -> list[str]:
    words = (text or "").split()
    if not words:
        return [""]
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if stringWidth(trial, font, size) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _item_name(item: dict) -> str:
    return " ".join(p for p in [item.get("brand"), item.get("name"), item.get("variant"), item.get("pack_size")] if p) or "Item"


def _round_card(pdf, x, y, w, h, radius=3 * mm, fill=CARD, stroke=LINE):
    pdf.saveState()
    pdf.setFillColor(fill)
    pdf.setStrokeColor(stroke)
    pdf.setLineWidth(0.6)
    pdf.roundRect(x, y, w, h, radius, stroke=1, fill=1)
    pdf.restoreState()


def _status_pill(pdf, x, y, text: str, color):
    pdf.saveState()
    pdf.setFont(F_BOLD, 9)
    label = text.upper()
    pad_x = 3 * mm
    w = stringWidth(label, F_BOLD, 9) + pad_x * 2
    h = 6.4 * mm
    pdf.setFillColor(color)
    pdf.roundRect(x, y, w, h, h / 2, stroke=0, fill=1)
    pdf.setFillColor(white)
    pdf.drawString(x + pad_x, y + h / 2 - 3, label)
    pdf.restoreState()
    return w


# --- main entry point ---------------------------------------------------------

def generate_invoice_pdf(invoice_data: dict, buffer, note: str | None = None) -> None:
    """Draws the full invoice into `buffer` (a path or a writable/seekable
    file-like object such as io.BytesIO). Nothing here talks to the network
    or a database — invoice_data is a plain dict from
    invoice_service.serialize_invoice, and `note` is a pre-generated string
    (see invoice_ai_service) so a slow/unavailable AI call never blocks or
    breaks PDF rendering itself.
    """
    pdf = canvas.Canvas(buffer, pagesize=A4)

    shop = invoice_data.get("shop") or {}
    shop_name = shop.get("name") or "DukaanAI"
    status = (invoice_data.get("status") or "paid").lower()
    status_color = STATUS_STYLE.get(status, INK_SOFT)

    # --- header banner ------------------------------------------------------
    banner_h = 46 * mm
    banner_y = PAGE_H - banner_h
    _gradient_rect(pdf, 0, banner_y, PAGE_W, banner_h, LAVENDER_DEEP, BLUE_DEEP)

    # wordmark badge
    badge = 11 * mm
    badge_x, badge_y = MARGIN, PAGE_H - 15 * mm - badge
    pdf.setFillColor(white)
    pdf.roundRect(badge_x, badge_y, badge, badge, 3 * mm, stroke=0, fill=1)
    pdf.setFillColor(LAVENDER_DEEP)
    pdf.setFont(F_BOLD, 13)
    pdf.drawCentredString(badge_x + badge / 2, badge_y + badge / 2 - 4.5, "D")

    pdf.setFillColor(white)
    pdf.setFont(F_BOLD, 19)
    pdf.drawString(badge_x + badge + 4 * mm, PAGE_H - 21 * mm, "DukaanAI")
    pdf.setFont(F_REG, 9)
    pdf.setFillColor(HexColor("#ece7fb"))
    pdf.drawString(badge_x + badge + 4 * mm, PAGE_H - 26.5 * mm, "Smart billing for your shop")

    # shop identity, right-aligned in the banner
    right_x = PAGE_W - MARGIN
    pdf.setFillColor(white)
    pdf.setFont(F_BOLD, 13)
    pdf.drawRightString(right_x, PAGE_H - 19 * mm, shop_name)
    pdf.setFont(F_REG, 8.5)
    pdf.setFillColor(HexColor("#ece7fb"))
    detail_bits = [b for b in [shop.get("owner_name"), shop.get("phone"), shop.get("location")] if b]
    pdf.drawRightString(right_x, PAGE_H - 24.5 * mm, "  ·  ".join(detail_bits) or " ")

    pdf.setFont(F_REG, 8)
    pdf.drawRightString(right_x, banner_y + 6 * mm, "INVOICE")

    # --- meta row: invoice # card + status/payment card ----------------------
    y = banner_y - 10 * mm
    card_h = 24 * mm
    card_w = (CONTENT_W - 6 * mm) / 2

    _round_card(pdf, MARGIN, y - card_h, card_w, card_h)
    pdf.setFont(F_BOLD, 8)
    pdf.setFillColor(INK_FAINT)
    pdf.drawString(MARGIN + 5 * mm, y - 7 * mm, "INVOICE NUMBER")
    pdf.setFont(F_BOLD, 15)
    pdf.setFillColor(INK)
    pdf.drawString(MARGIN + 5 * mm, y - 14.5 * mm, invoice_data.get("invoice_number", "—"))
    pdf.setFont(F_REG, 8.5)
    pdf.setFillColor(INK_SOFT)
    pdf.drawString(MARGIN + 5 * mm, y - 20 * mm, f"Date: {(invoice_data.get('created_at') or '')[:10]}")

    right_card_x = MARGIN + card_w + 6 * mm
    _round_card(pdf, right_card_x, y - card_h, card_w, card_h)
    pdf.setFont(F_BOLD, 8)
    pdf.setFillColor(INK_FAINT)
    pdf.drawString(right_card_x + 5 * mm, y - 7 * mm, "STATUS")
    _status_pill(pdf, right_card_x + 5 * mm, y - 15.5 * mm, status, status_color)
    pdf.setFont(F_REG, 8.5)
    pdf.setFillColor(INK_SOFT)
    pdf.drawString(right_card_x + 5 * mm, y - 20.5 * mm, f"Payment: {invoice_data.get('payment_method', 'cash').title()}")

    # --- bill to card ---------------------------------------------------------
    y -= card_h + 7 * mm
    bill_h = 20 * mm
    _round_card(pdf, MARGIN, y - bill_h, CONTENT_W, bill_h)
    pdf.setFont(F_BOLD, 8)
    pdf.setFillColor(INK_FAINT)
    pdf.drawString(MARGIN + 5 * mm, y - 7 * mm, "BILL TO")

    customer = invoice_data.get("customer")
    if customer:
        pdf.setFont(F_BOLD, 11)
        pdf.setFillColor(INK)
        pdf.drawString(MARGIN + 5 * mm, y - 13.5 * mm, customer["name"])
        if customer.get("phone"):
            pdf.setFont(F_REG, 9)
            pdf.setFillColor(INK_SOFT)
            pdf.drawString(MARGIN + 5 * mm, y - 18 * mm, customer["phone"])
    else:
        pdf.setFont(F_ITALIC, 10.5)
        pdf.setFillColor(INK_SOFT)
        pdf.drawString(MARGIN + 5 * mm, y - 13.5 * mm, "Walk-in customer")

    # --- items table ------------------------------------------------------
    y -= bill_h + 9 * mm

    col_item_x = MARGIN + 4 * mm
    col_item_w = 88 * mm
    col_qty_x = MARGIN + 108 * mm
    col_price_right = MARGIN + 148 * mm
    col_total_right = MARGIN + CONTENT_W - 4 * mm

    header_h = 8.5 * mm
    pdf.setFillColor(INK)
    pdf.rect(MARGIN, y - header_h, CONTENT_W, header_h, stroke=0, fill=1)
    pdf.setFont(F_BOLD, 8.5)
    pdf.setFillColor(white)
    pdf.drawString(col_item_x, y - header_h + 3 * mm, "ITEM")
    pdf.drawCentredString(col_qty_x, y - header_h + 3 * mm, "QTY")
    pdf.drawRightString(col_price_right, y - header_h + 3 * mm, "PRICE")
    pdf.drawRightString(col_total_right, y - header_h + 3 * mm, "TOTAL")
    y -= header_h

    items = invoice_data.get("items") or []
    line_h = 4.6 * mm
    row_pad = 3.4 * mm

    if items:
        for idx, item in enumerate(items):
            lines = _wrap(_item_name(item), F_REG, 9.5, col_item_w)
            row_h = max(9 * mm, row_pad * 2 + line_h * len(lines) - line_h)

            if idx % 2 == 1:
                pdf.setFillColor(ZEBRA)
                pdf.rect(MARGIN, y - row_h, CONTENT_W, row_h, stroke=0, fill=1)

            text_top = y - row_pad - 2.6
            pdf.setFont(F_REG, 9.5)
            pdf.setFillColor(INK)
            for li, line in enumerate(lines):
                pdf.drawString(col_item_x, text_top - li * line_h, line)

            mid_y = y - row_h / 2 - 2.6
            pdf.setFont(F_REG, 9.5)
            pdf.setFillColor(INK_SOFT)
            pdf.drawCentredString(col_qty_x, mid_y, str(item.get("quantity", 0)))

            pdf.setFillColor(INK_SOFT)
            _draw_string(pdf, col_price_right, mid_y, rupee(item.get("unit_price")), _currency_draw_font(False), 9.5, right=True)

            pdf.setFillColor(INK)
            _draw_string(pdf, col_total_right, mid_y, rupee(item.get("total_price")), _currency_draw_font(True), 9.5, bold=True, right=True)

            y -= row_h
            pdf.setStrokeColor(LINE)
            pdf.setLineWidth(0.4)
            pdf.line(MARGIN, y, MARGIN + CONTENT_W, y)
    else:
        row_h = 14 * mm
        pdf.setFont(F_ITALIC, 9.5)
        pdf.setFillColor(INK_SOFT)
        pdf.drawString(col_item_x, y - row_h / 2 - 2, "No itemised breakdown available for this invoice.")
        y -= row_h
        pdf.setStrokeColor(LINE)
        pdf.line(MARGIN, y, MARGIN + CONTENT_W, y)

    # --- totals -------------------------------------------------------------
    y -= 8 * mm
    items_total = sum((i.get("total_price") or 0) for i in items)
    total_amount = invoice_data.get("total_amount") or 0

    box_w = 74 * mm
    box_x = MARGIN + CONTENT_W - box_w

    if items and abs(items_total - total_amount) > 0.01:
        pdf.setFont(F_REG, 9.5)
        pdf.setFillColor(INK_SOFT)
        pdf.drawString(box_x, y, "Items total")
        _draw_string(pdf, box_x + box_w, y, rupee(items_total), _currency_draw_font(False), 9.5, right=True)
        y -= 7 * mm

    total_box_h = 14 * mm
    _gradient_rect(pdf, box_x, y - total_box_h, box_w, total_box_h, LAVENDER_DEEP, BLUE_DEEP)
    pdf.setFont(F_BOLD, 9)
    pdf.setFillColor(white)
    pdf.drawString(box_x + 4 * mm, y - total_box_h / 2 - 1, "GRAND TOTAL")
    pdf.setFillColor(white)
    _draw_string(
        pdf, box_x + box_w - 4 * mm, y - total_box_h / 2 - 2.5, rupee(total_amount),
        _currency_draw_font(True), 14, bold=True, right=True,
    )
    y -= total_box_h

    # --- AI thank-you note ----------------------------------------------------
    y -= 10 * mm
    note_h = 14 * mm
    _round_card(pdf, MARGIN, y - note_h, CONTENT_W, note_h, fill=NOTE_BG, stroke=NOTE_BG)
    _sparkle(pdf, MARGIN + 7 * mm, y - note_h / 2, 2.2 * mm, LAVENDER_DEEP)
    pdf.setFont(F_ITALIC, 10)
    pdf.setFillColor(INK_SOFT)
    note_text = note or "Thank you for shopping with us — we hope to see you again soon!"
    note_lines = _wrap(note_text, F_ITALIC, 10, CONTENT_W - 22 * mm)[:2]
    ny = y - note_h / 2 + (line_h * (len(note_lines) - 1)) / 2 - 1
    for nl in note_lines:
        pdf.drawString(MARGIN + 13 * mm, ny, nl)
        ny -= line_h

    # --- footer ---------------------------------------------------------------
    pdf.setStrokeColor(LINE)
    pdf.setLineWidth(0.5)
    pdf.line(MARGIN, 16 * mm, PAGE_W - MARGIN, 16 * mm)
    pdf.setFont(F_REG, 7.5)
    pdf.setFillColor(INK_FAINT)
    pdf.drawCentredString(PAGE_W / 2, 11.5 * mm, f"Generated by DukaanAI for {shop_name}")
    pdf.drawCentredString(PAGE_W / 2, 7.5 * mm, "This is a computer-generated invoice and does not require a signature.")

    pdf.showPage()
    pdf.save()
