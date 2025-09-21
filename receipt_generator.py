# receipt_generator.py
from PIL import Image, ImageDraw, ImageFont
import datetime
import sys
import os

def resource_path(relative_path):
    """ 
    Obtém o caminho absoluto para o recurso, funciona para desenvolvimento
    e para o executável criado com PyInstaller.
    """
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Constantes de Configuração ---
FONT_PATH = resource_path("DejaVuSansMono.ttf") # Usa a função para encontrar a fonte
IMG_WIDTH = 400
LEFT_MARGIN = 10
LINE_HEIGHT = 15

# --- Informações da Empresa (Personalize como quiser) ---
COMPANY_INFO = {
    "name": "FARMACIA 01",
    "cnpj": "00.291.485/0001-10",
    "im": "1312431",
    "address": "RUA PARANA, 5446, CENTRO, CASCAVEL, PR",
    "phone": "(45) 3226-1243"
}

def create_receipt_image(sale_data: dict) -> str:
    """
    Gera uma imagem de recibo a partir dos dados da venda.
    Retorna o caminho do arquivo da imagem salva.
    """
    try:
        font_regular = ImageFont.truetype(FONT_PATH, 10)
        font_bold = ImageFont.truetype(FONT_PATH, 11)
    except IOError:
        print(f"Erro: Arquivo de fonte '{FONT_PATH}' não encontrado.")
        return ""

    num_items = len(sale_data.get("items", []))
    img_height = 250 + (num_items * LINE_HEIGHT)
    
    image = Image.new('RGB', (IMG_WIDTH, img_height), color='white')
    draw = ImageDraw.Draw(image)
    y_pos = 10

    draw.text((IMG_WIDTH/2, y_pos), COMPANY_INFO["name"], font=font_bold, fill='black', anchor='ms'); y_pos += LINE_HEIGHT
    draw.text((IMG_WIDTH/2, y_pos), f"CNPJ: {COMPANY_INFO['cnpj']} IM: {COMPANY_INFO['im']}", font=font_regular, fill='black', anchor='ms'); y_pos += LINE_HEIGHT
    draw.text((IMG_WIDTH/2, y_pos), COMPANY_INFO["address"], font=font_regular, fill='black', anchor='ms'); y_pos += LINE_HEIGHT
    draw.text((IMG_WIDTH/2, y_pos), f"Fone: {COMPANY_INFO['phone']}", font=font_regular, fill='black', anchor='ms'); y_pos += LINE_HEIGHT * 1.5
    draw.line([(LEFT_MARGIN, y_pos), (IMG_WIDTH - LEFT_MARGIN, y_pos)], fill='black', width=1); y_pos += 5

    sale_id = sale_data.get('_id', 'N/A')
    # Converte a string de data ISO de volta para um objeto datetime
    sale_date_obj = datetime.fromisoformat(sale_data.get('sale_date'))
    draw.text((LEFT_MARGIN, y_pos), f"Num Nota: {sale_id[:8]}... EMISSAO: {sale_date_obj.strftime('%d/%m/%Y')}", font=font_regular, fill='black'); y_pos += LINE_HEIGHT
    draw.text((LEFT_MARGIN, y_pos), f"Vendedor: {sale_data.get('user_id', 'N/A')} HORA: {sale_date_obj.strftime('%H:%M:%S')}", font=font_regular, fill='black'); y_pos += LINE_HEIGHT
    draw.line([(LEFT_MARGIN, y_pos), (IMG_WIDTH - LEFT_MARGIN, y_pos)], fill='black', width=1); y_pos += 10
    
    header = f"{'Descricao'.ljust(20)} {'V.Unit'.rjust(7)} {'Qtd'.rjust(5)} {'V.Total'.rjust(8)}"
    draw.text((LEFT_MARGIN, y_pos), header, font=font_regular, fill='black'); y_pos += LINE_HEIGHT

    for item in sale_data.get("items", []):
        name = (item['name'][:18] + '..') if len(item['name']) > 20 else item['name']
        unit_price = f"{item['unit_price']:.2f}"
        qty = str(item['quantity'])
        subtotal = f"{item['unit_price'] * item['quantity']:.2f}"
        line = f"{name.ljust(20)} {unit_price.rjust(7)} {qty.rjust(5)} {subtotal.rjust(8)}"
        draw.text((LEFT_MARGIN, y_pos), line, font=font_regular, fill='black'); y_pos += LINE_HEIGHT
    
    y_pos += 10
    total = sale_data.get('total_amount', 0)
    draw.text((IMG_WIDTH - LEFT_MARGIN, y_pos), f"A Pagar $: {total:.2f}", font=font_bold, fill='black', anchor='rs'); y_pos += LINE_HEIGHT * 2

    draw.text((IMG_WIDTH/2, y_pos), "*** NAO E DOCUMENTO FISCAL ***", font=font_bold, fill='black', anchor='ms'); y_pos += LINE_HEIGHT
    draw.text((IMG_WIDTH/2, y_pos), "Assinatura", font=font_regular, fill='black', anchor='ms'); y_pos += LINE_HEIGHT
    draw.line([(IMG_WIDTH*0.2, y_pos), (IMG_WIDTH*0.8, y_pos)], fill='black', width=1)

    # Salva o recibo na pasta de onde o .exe está sendo executado
    file_path = f"recibo_venda_{sale_id}.png"
    image.save(file_path)
    return file_path