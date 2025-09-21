# receipt_generator.py
import datetime
import os
import sys
from PIL import Image, ImageDraw, ImageFont

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

FONT_PATH = resource_path("DejaVuSansMono.ttf")
IMG_WIDTH = 400
LEFT_MARGIN = 10
LINE_HEIGHT = 15

COMPANY_INFO = {
    "name": "FARMACIA 01", "cnpj": "00.291.485/0001-10", "im": "1312431",
    "address": "RUA PARANA, 5446, CENTRO, CASCAVEL, PR", "phone": "(45) 3226-1243"
}

def create_receipt_image(sale_data: dict) -> str:
    try:
        font_regular = ImageFont.truetype(FONT_PATH, 10)
        font_bold = ImageFont.truetype(FONT_PATH, 11)
    except IOError:
        print(f"Erro: Fonte '{FONT_PATH}' não encontrada."); return ""

    num_items = len(sale_data.get("items", []))
    img_height = 280 + (num_items * LINE_HEIGHT)
    
    image = Image.new('RGB', (IMG_WIDTH, img_height), color='white')
    draw = ImageDraw.Draw(image)
    y_pos = 10

    # Cabeçalho
    draw.text((IMG_WIDTH/2, y_pos), COMPANY_INFO["name"], font=font_bold, fill='black', anchor='ms'); y_pos += LINE_HEIGHT
    draw.text((IMG_WIDTH/2, y_pos), f"CNPJ: {COMPANY_INFO['cnpj']} IM: {COMPANY_INFO['im']}", font=font_regular, fill='black', anchor='ms'); y_pos += LINE_HEIGHT
    draw.text((IMG_WIDTH/2, y_pos), COMPANY_INFO["address"], font=font_regular, fill='black', anchor='ms'); y_pos += LINE_HEIGHT
    draw.text((IMG_WIDTH/2, y_pos), f"Fone: {COMPANY_INFO['phone']}", font=font_regular, fill='black', anchor='ms'); y_pos += LINE_HEIGHT * 1.5
    draw.line([(LEFT_MARGIN, y_pos), (IMG_WIDTH - LEFT_MARGIN, y_pos)], fill='black', width=1); y_pos += 5
    sale_id = sale_data.get('_id', 'N/A')
    sale_date_obj = datetime.datetime.fromisoformat(sale_data.get('sale_date'))
    draw.text((LEFT_MARGIN, y_pos), f"Num Nota: {sale_id[:8]}... EMISSAO: {sale_date_obj.strftime('%d/%m/%Y')}", font=font_regular, fill='black'); y_pos += LINE_HEIGHT
    draw.text((LEFT_MARGIN, y_pos), f"Vendedor: {sale_data.get('user_id', 'N/A')} HORA: {sale_date_obj.strftime('%H:%M:%S')}", font=font_regular, fill='black'); y_pos += LINE_HEIGHT
    draw.line([(LEFT_MARGIN, y_pos), (IMG_WIDTH - LEFT_MARGIN, y_pos)], fill='black', width=1); y_pos += 10
    
    # Cabeçalho dos Itens
    header = f"{'Descricao'.ljust(20)} {'V.Unit'.rjust(7)} {'Qtd'.rjust(5)} {'V.Total'.rjust(8)}"
    draw.text((LEFT_MARGIN, y_pos), header, font=font_regular, fill='black'); y_pos += LINE_HEIGHT

    # Lista de Itens
    for item in sale_data.get("items", []):
        name = (item['name'][:18] + '..') if len(item['name']) > 20 else item['name']
        
        # --- LINHA CORRIGIDA ---
        # A formatação agora é feita de forma mais limpa, sem aninhar f-strings.
        unit_price_str = f"{item['unit_price']:.2f}".rjust(7)
        quantity_str = str(item['quantity']).rjust(5)
        subtotal_str = f"{item['unit_price'] * item['quantity']:.2f}".rjust(8)
        line = f"{name.ljust(20)} {unit_price_str} {quantity_str} {subtotal_str}"
        
        draw.text((LEFT_MARGIN, y_pos), line, font=font_regular, fill='black'); y_pos += LINE_HEIGHT
    
    y_pos += 5
    draw.line([(LEFT_MARGIN, y_pos), (IMG_WIDTH - LEFT_MARGIN, y_pos)], fill='black', width=1); y_pos += 10

    # Seção de Pagamento
    total = sale_data.get('total_amount', 0)
    payment_method = sale_data.get('payment_method', 'N/A')
    amount_received = sale_data.get('amount_received', 0.0)

    if payment_method == 'Dinheiro':
        change = amount_received - total
        draw.text((IMG_WIDTH - LEFT_MARGIN, y_pos), f"Total: R$ {total:.2f}", font=font_regular, fill='black', anchor='rs'); y_pos += LINE_HEIGHT
        draw.text((IMG_WIDTH - LEFT_MARGIN, y_pos), f"Pago (Dinheiro): R$ {amount_received:.2f}", font=font_regular, fill='black', anchor='rs'); y_pos += LINE_HEIGHT
        draw.text((IMG_WIDTH - LEFT_MARGIN, y_pos), f"Troco: R$ {max(0, change):.2f}", font=font_bold, fill='black', anchor='rs'); y_pos += LINE_HEIGHT * 2
    else: # PIX/Cartão
        draw.text((IMG_WIDTH - LEFT_MARGIN, y_pos), f"Total Pago ({payment_method}): R$ {total:.2f}", font=font_bold, fill='black', anchor='rs'); y_pos += LINE_HEIGHT * 2

    # Rodapé
    draw.text((IMG_WIDTH/2, y_pos), "*** NAO E DOCUMENTO FISCAL ***", font=font_bold, fill='black', anchor='ms'); y_pos += LINE_HEIGHT
    draw.text((IMG_WIDTH/2, y_pos), "Assinatura", font=font_regular, fill='black', anchor='ms'); y_pos += LINE_HEIGHT
    draw.line([(IMG_WIDTH*0.2, y_pos), (IMG_WIDTH*0.8, y_pos)], fill='black', width=1)

    file_path = f"recibo_venda_{sale_id}.png"
    image.save(file_path)
    return file_path