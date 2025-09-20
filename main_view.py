import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
import requests
from product_view import ProductView
from pos_view import POSView
from reports_view import ReportsView
from forecast_view import ForecastView

class MainApplication(tk.Frame):
    def __init__(self, parent, token):
        super().__init__(parent)
        self.parent = parent
        self.token = token
        self.api_headers = {"Authorization": f"Bearer {self.token}"}
        self.current_view = None
        self.user_data = None

        self.parent.title("Sistema PDV - Painel Principal")
        self.parent.geometry("1100x700") # Aumentado para melhor visualização

        # Tenta carregar o ícone da janela
        try:
            img = tk.PhotoImage(file='icon.png')
            self.parent.iconphoto(False, img)
        except tk.TclError:
            print("Ícone 'icon.png' não encontrado ou inválido.")

        self.parent.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.create_widgets()
        self.load_user_info()

    def create_widgets(self):
        self.create_menu()
        
        # --- Barra de Status Estilizada ---
        self.status_bar = ttk.Label(self.parent, text="Pronto", padding=5, bootstyle="primary-inverse")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # --- Frame de Informações do Usuário Estilizado ---
        user_info_frame = ttk.LabelFrame(self.parent, text="Usuário Logado", padding=10, bootstyle="secondary")
        user_info_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 0))
        
        self.user_info_label = ttk.Label(user_info_frame, text="Carregando...", font=("Segoe UI", 10))
        self.user_info_label.pack()

        # --- Área de Conteúdo Principal ---
        self.main_content_frame = ttk.Frame(self.parent)
        self.main_content_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        self.welcome_label = ttk.Label(self.main_content_frame, text="Selecione um módulo no menu para começar.", font=("Segoe UI", 16), bootstyle="secondary")
        self.welcome_label.pack(pady=50)

    def create_menu(self):
        menubar = ttk.Menu(self.parent)
        self.parent.config(menu=menubar)
        pos_menu = ttk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Caixa", menu=pos_menu)
        pos_menu.add_command(label="Abrir PDV", command=self.show_pos_view)
        management_menu = ttk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Gerenciamento", menu=management_menu)
        management_menu.add_command(label="Produtos", command=self.show_product_view)
        management_menu.add_command(label="Relatórios", command=self.show_reports_view)
        management_menu.add_command(label="Previsão de Vendas", command=self.show_forecast_view)
        management_menu.add_separator()
        management_menu.add_command(label="Sair", command=self.on_closing)

    def show_view(self, view_class, **kwargs):
        if self.welcome_label:
            self.welcome_label.pack_forget()
            self.welcome_label = None

        if self.current_view: self.current_view.destroy()
        self.current_view = view_class(self.main_content_frame, self.token, **kwargs)
        self.current_view.pack(fill=tk.BOTH, expand=True)
    
    # ... (O resto das funções show_*, load_user_info e on_closing permanecem as mesmas)
    def show_pos_view(self):
        if self.user_data: self.show_view(POSView, user_info=self.user_data)
        else: messagebox.showwarning("Atenção", "Aguarde o carregamento das informações do usuário.")
    def show_product_view(self): self.show_view(ProductView)
    def show_reports_view(self): self.show_view(ReportsView)
    def show_forecast_view(self): self.show_view(ForecastView)
    def load_user_info(self):
        try:
            self.status_bar.config(text="Carregando informações do usuário...")
            response = requests.get("http://127.0.0.1:8000/users/me", headers=self.api_headers)
            if response.status_code == 200:
                self.user_data = response.json()
                welcome_message = f"Bem-vindo(a), {self.user_data['username']}! | Perfil: {self.user_data['role'].capitalize()}"
                self.user_info_label.config(text=welcome_message); self.status_bar.config(text="Pronto")
            else:
                messagebox.showerror("Erro de Autenticação", f"Sessão expirada.\n\nDetalhe: {response.text}"); self.parent.destroy()
        except requests.exceptions.ConnectionError: messagebox.showerror("Erro de Conexão", "Não foi possível conectar ao servidor."); self.parent.destroy()
    def on_closing(self):
        if messagebox.askokcancel("Sair", "Deseja sair do sistema?"): self.parent.destroy()