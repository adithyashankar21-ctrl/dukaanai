from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm


def generate_invoice_pdf(invoice_data, file_path):
    pdf = canvas.Canvas(file_path, pagesize=A4)

    width, height = A4

    # Header
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(20 * mm, height - 25 * mm, "DUKAANAI")

    pdf.setFont("Helvetica", 10)
    pdf.drawString(
        20 * mm,
        height - 32 * mm,
        "Smart billing for your shop"
    )

    # Invoice information
    y = height - 50 * mm

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(
        20 * mm,
        y,
        f"Invoice: {invoice_data['invoice_number']}"
    )

    pdf.setFont("Helvetica", 10)
    pdf.drawString(
        20 * mm,
        y - 7 * mm,
        f"Date: {invoice_data['created_at']}"
    )

    # Customer
    y -= 20 * mm

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(20 * mm, y, "Customer")

    pdf.setFont("Helvetica", 10)

    customer = invoice_data.get("customer")

    if customer:
        pdf.drawString(
            20 * mm,
            y - 7 * mm,
            customer["name"]
        )

        if customer.get("phone"):
            pdf.drawString(
                20 * mm,
                y - 14 * mm,
                customer["phone"]
            )
    else:
        pdf.drawString(
            20 * mm,
            y - 7 * mm,
            "Walk-in Customer"
        )

    # Items
    y -= 35 * mm

    pdf.setFont("Helvetica-Bold", 10)

    pdf.drawString(20 * mm, y, "Item")
    pdf.drawString(110 * mm, y, "Qty")
    pdf.drawString(135 * mm, y, "Price")
    pdf.drawString(165 * mm, y, "Total")

    y -= 5 * mm

    pdf.line(
        20 * mm,
        y,
        190 * mm,
        y
    )

    y -= 7 * mm

    pdf.setFont("Helvetica", 9)

    for item in invoice_data.get("items", []):

        name_parts = []

        if item.get("brand"):
            name_parts.append(item["brand"])

        if item.get("name"):
            name_parts.append(item["name"])

        if item.get("variant"):
            name_parts.append(item["variant"])

        if item.get("pack_size"):
            name_parts.append(item["pack_size"])

        item_name = " ".join(name_parts)

        pdf.drawString(
            20 * mm,
            y,
            item_name[:45]
        )

        pdf.drawString(
            110 * mm,
            y,
            str(item["quantity"])
        )

        pdf.drawString(
            135 * mm,
            y,
            f"Rs. {item['unit_price']:.2f}"
        )

        pdf.drawString(
            165 * mm,
            y,
            f"Rs. {item['total_price']:.2f}"
        )

        y -= 8 * mm

    # Total
    y -= 5 * mm

    pdf.line(
        120 * mm,
        y,
        190 * mm,
        y
    )

    y -= 10 * mm

    pdf.setFont("Helvetica-Bold", 12)

    pdf.drawString(
        120 * mm,
        y,
        "TOTAL"
    )

    pdf.drawString(
        165 * mm,
        y,
        f"Rs. {invoice_data['total_amount']:.2f}"
    )

    # Payment
    y -= 10 * mm

    pdf.setFont("Helvetica", 10)

    pdf.drawString(
        120 * mm,
        y,
        f"Payment: {invoice_data['payment_method']}"
    )

    # Footer
    pdf.setFont("Helvetica", 9)

    pdf.drawCentredString(
        width / 2,
        15 * mm,
        "Thank you for shopping with us!"
    )

    pdf.save()