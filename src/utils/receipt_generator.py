import datetime
import os
import sys
from PIL import Image, ImageDraw, ImageFont


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller executable binaries."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# Updated path pointing to the new assets/fonts directory
FONT_PATH = resource_path(os.path.join("assets", "fonts", "DejaVuSansMono.ttf"))
IMG_WIDTH = 400
LEFT_MARGIN = 10
LINE_HEIGHT = 15

COMPANY_INFO = {
    "name": "PHARMACY STORE 01",
    "tax_id": "00.291.485/0001-10",
    "reg_num": "1312431",
    "address": "5446 PARANA ST, DOWNTOWN, CASCAVEL, PR",
    "phone": "(45) 3226-1243",
}


def create_receipt_image(sale_data: dict) -> str:
    """Generates an image receipt for a completed sale transaction."""
    try:
        font_regular = ImageFont.truetype(FONT_PATH, 10)
        font_bold = ImageFont.truetype(FONT_PATH, 11)
    except IOError:
        print(f"Error: Font file '{FONT_PATH}' was not found.")
        return ""

    num_items = len(sale_data.get("items", []))
    img_height = 280 + (num_items * LINE_HEIGHT)

    image = Image.new("RGB", (IMG_WIDTH, img_height), color="white")
    draw = ImageDraw.Draw(image)
    y_pos = 10

    # Header section
    draw.text(
        (IMG_WIDTH / 2, y_pos),
        COMPANY_INFO["name"],
        font=font_bold,
        fill="black",
        anchor="ms",
    )
    y_pos += LINE_HEIGHT

    draw.text(
        (IMG_WIDTH / 2, y_pos),
        f"TAX ID: {COMPANY_INFO['tax_id']} REG: {COMPANY_INFO['reg_num']}",
        font=font_regular,
        fill="black",
        anchor="ms",
    )
    y_pos += LINE_HEIGHT

    draw.text(
        (IMG_WIDTH / 2, y_pos),
        COMPANY_INFO["address"],
        font=font_regular,
        fill="black",
        anchor="ms",
    )
    y_pos += LINE_HEIGHT

    draw.text(
        (IMG_WIDTH / 2, y_pos),
        f"Phone: {COMPANY_INFO['phone']}",
        font=font_regular,
        fill="black",
        anchor="ms",
    )
    y_pos += LINE_HEIGHT * 1.5

    draw.line(
        [(LEFT_MARGIN, y_pos), (IMG_WIDTH - LEFT_MARGIN, y_pos)],
        fill="black",
        width=1,
    )
    y_pos += 5

    sale_id = sale_data.get("_id", "N/A")
    sale_date_obj = datetime.datetime.fromisoformat(sale_data.get("sale_date"))

    draw.text(
        (LEFT_MARGIN, y_pos),
        f"Receipt #: {sale_id[:8]}... DATE: {sale_date_obj.strftime('%d/%m/%Y')}",
        font=font_regular,
        fill="black",
    )
    y_pos += LINE_HEIGHT

    draw.text(
        (LEFT_MARGIN, y_pos),
        f"Cashier: {sale_data.get('user_id', 'N/A')} TIME: {sale_date_obj.strftime('%H:%M:%S')}",
        font=font_regular,
        fill="black",
    )
    y_pos += LINE_HEIGHT

    draw.line(
        [(LEFT_MARGIN, y_pos), (IMG_WIDTH - LEFT_MARGIN, y_pos)],
        fill="black",
        width=1,
    )
    y_pos += 10

    # Table column header
    header = f"{'Description'.ljust(20)} {'Price'.rjust(7)} {'Qty'.rjust(5)} {'Total'.rjust(8)}"
    draw.text(
        (LEFT_MARGIN, y_pos), header, font=font_regular, fill="black"
    )
    y_pos += LINE_HEIGHT

    # Purchased items loop
    for item in sale_data.get("items", []):
        name = (
            (item["name"][:18] + "..")
            if len(item["name"]) > 20
            else item["name"]
        )

        unit_price_str = f"{item['unit_price']:.2f}".rjust(7)
        quantity_str = str(item["quantity"]).rjust(5)
        subtotal_str = f"{item['unit_price'] * item['quantity']:.2f}".rjust(8)
        line = f"{name.ljust(20)} {unit_price_str} {quantity_str} {subtotal_str}"

        draw.text(
            (LEFT_MARGIN, y_pos), line, font=font_regular, fill="black"
        )
        y_pos += LINE_HEIGHT

    y_pos += 5
    draw.line(
        [(LEFT_MARGIN, y_pos), (IMG_WIDTH - LEFT_MARGIN, y_pos)],
        fill="black",
        width=1,
    )
    y_pos += 10

    # Payment details
    total = sale_data.get("total_amount", 0)
    payment_method = sale_data.get("payment_method", "N/A")
    amount_received = sale_data.get("amount_received", 0.0)

    if payment_method in ["Dinheiro", "Cash"]:
        change = amount_received - total
        draw.text(
            (IMG_WIDTH - LEFT_MARGIN, y_pos),
            f"Total: $ {total:.2f}",
            font=font_regular,
            fill="black",
            anchor="rs",
        )
        y_pos += LINE_HEIGHT

        draw.text(
            (IMG_WIDTH - LEFT_MARGIN, y_pos),
            f"Paid (Cash): $ {amount_received:.2f}",
            font=font_regular,
            fill="black",
            anchor="rs",
        )
        y_pos += LINE_HEIGHT

        draw.text(
            (IMG_WIDTH - LEFT_MARGIN, y_pos),
            f"Change: $ {max(0, change):.2f}",
            font=font_bold,
            fill="black",
            anchor="rs",
        )
        y_pos += LINE_HEIGHT * 2
    else:  # PIX/Card or digital payments
        draw.text(
            (IMG_WIDTH - LEFT_MARGIN, y_pos),
            f"Total Paid ({payment_method}): $ {total:.2f}",
            font=font_bold,
            fill="black",
            anchor="rs",
        )
        y_pos += LINE_HEIGHT * 2

    # Footer notice
    draw.text(
        (IMG_WIDTH / 2, y_pos),
        "*** NOT A TAX RECEIPT ***",
        font=font_bold,
        fill="black",
        anchor="ms",
    )
    y_pos += LINE_HEIGHT

    draw.text(
        (IMG_WIDTH / 2, y_pos),
        "Customer Signature",
        font=font_regular,
        fill="black",
        anchor="ms",
    )
    y_pos += LINE_HEIGHT

    draw.line(
        [(IMG_WIDTH * 0.2, y_pos), (IMG_WIDTH * 0.8, y_pos)],
        fill="black",
        width=1,
    )

    file_path = f"sale_receipt_{sale_id}.png"
    image.save(file_path)
    return file_path