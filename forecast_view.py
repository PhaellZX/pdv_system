import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
import requests
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import matplotlib.pyplot as plt

BACKEND_URL = "http://127.0.0.1:8000"

class ForecastView(ttk.Frame):
    def __init__(self, parent, token, **kwargs):
        super().__init__(parent)
        self.token = token
        self.api_headers = {"Authorization": f"Bearer {self.token}"}
        
        self.products = []
        self.create_widgets()
        self.load_product_list()

    def create_widgets(self):
        selection_frame = ttk.Frame(self, padding=10)
        selection_frame.pack(fill=tk.X)

        ttk.Label(selection_frame, text="Selecione o Produto:").pack(side=tk.LEFT, padx=(0, 10))
        self.product_combobox = ttk.Combobox(selection_frame, state="readonly", width=40, bootstyle="primary")
        self.product_combobox.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        ttk.Button(selection_frame, text="Gerar Previsão", command=self.generate_forecast, bootstyle="primary").pack(side=tk.LEFT, padx=10)

        self.chart_frame = ttk.LabelFrame(self, text="Previsão de Vendas", padding=10, bootstyle="secondary")
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def load_product_list(self):
        try:
            response = requests.get(f"{BACKEND_URL}/produtos", headers=self.api_headers)
            if response.status_code == 200:
                self.products = response.json()
                product_names = [p['name'] for p in self.products]
                self.product_combobox['values'] = product_names
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro de Conexão", str(e))

    def generate_forecast(self):
        selected_name = self.product_combobox.get()
        if not selected_name:
            return messagebox.showwarning("Atenção", "Por favor, selecione um produto.")

        product_id = next((p['_id'] for p in self.products if p['name'] == selected_name), None)
        if not product_id:
            return messagebox.showerror("Erro", "ID do produto não encontrado.")

        try:
            response = requests.get(f"{BACKEND_URL}/previsao/produto/{product_id}", headers=self.api_headers)
            if response.status_code == 200:
                self.plot_forecast(response.json(), selected_name)
            else:
                error = response.json().get("detail", "Erro desconhecido")
                messagebox.showerror("Erro na Previsão", f"Não foi possível gerar a previsão.\n\nDetalhe: {error}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro de Conexão", str(e))
            
    def plot_forecast(self, data, product_name):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        if not data:
            ttk.Label(self.chart_frame, text="Nenhuma previsão foi retornada.").pack()
            return

        plt.style.use('default')
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])

        fig = Figure(figsize=(8, 5), dpi=100)
        fig.patch.set_facecolor('#f8f9fa')

        ax = fig.add_subplot(111)
        ax.set_facecolor('#ffffff')
        
        ax.plot(df['date'], df['predicted_sales'], marker='o', linestyle='-', color='#0d6efd', label='Vendas Previstas')
        ax.set_title(f'Previsão de Vendas para "{product_name}"', color='gray')
        ax.set_xlabel('Data', color='gray'); ax.set_ylabel('Qtd. de Vendas Prevista', color='gray')
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend()
        ax.tick_params(axis='x', colors='gray'); ax.tick_params(axis='y', colors='gray')
        fig.autofmt_xdate()
        
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)