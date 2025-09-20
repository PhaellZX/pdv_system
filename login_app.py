import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import requests
from main_view import MainApplication

BACKEND_URL = "http://127.0.0.1:8000"

class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Login - Sistema PDV")
        self.root.geometry("400x300")
        self.root.resizable(True, True)

        try:
            img = tk.PhotoImage(file='icon.png')
            self.root.iconphoto(False, img)
        except tk.TclError:
            print("Ícone 'icon.png' não encontrado ou inválido.")

        self.root.eval('tk::PlaceWindow . center')
        
        # O frame principal agora é um atributo da classe para que possamos destruí-lo
        self.main_frame = ttk.Frame(self.root, padding=(20, 20))
        self.main_frame.pack(expand=True, fill=tk.BOTH)
        
        self.create_widgets()

    def create_widgets(self):
        title_label = ttk.Label(
            self.main_frame, text="Acesso ao Sistema", 
            font=("Segoe UI", 18, "bold"), bootstyle="primary"
        )
        title_label.pack(pady=(10, 20))

        form_frame = ttk.Frame(self.main_frame)
        form_frame.pack(pady=10, fill=tk.X)

        username_label = ttk.Label(form_frame, text="Usuário:", font=("Segoe UI", 10))
        username_label.pack(fill=tk.X)
        self.username_entry = ttk.Entry(form_frame, font=("Segoe UI", 10))
        self.username_entry.pack(fill=tk.X, pady=(0, 10))
        self.username_entry.focus_set()

        password_label = ttk.Label(form_frame, text="Senha:", font=("Segoe UI", 10))
        password_label.pack(fill=tk.X)
        self.password_entry = ttk.Entry(form_frame, show="*", font=("Segoe UI", 10))
        self.password_entry.pack(fill=tk.X)
        
        login_button = ttk.Button(
            self.main_frame, 
            text="➤ Entrar",
            command=self.attempt_login,
            bootstyle="primary"
        )
        login_button.pack(pady=(20, 10), ipady=5, ipadx=20)
        
        self.root.bind('<Return>', lambda event=None: login_button.invoke())

    def attempt_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Erro de Login", "Usuário e senha são obrigatórios.")
            return

        try:
            response = requests.post(
                f"{BACKEND_URL}/token",
                data={"username": username, "password": password}
            )

            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                
                # --- LÓGICA DE TRANSIÇÃO CORRIGIDA ---
                # 1. Apaga o conteúdo da tela de login (o frame)
                self.main_frame.destroy()

                # 2. Carrega a aplicação principal na MESMA janela 'root'
                MainApplication(self.root, token=access_token).pack(expand=True, fill=tk.BOTH)
                
            elif response.status_code == 401:
                messagebox.showerror("Erro de Login", "Nome de usuário ou senha incorretos.")
            else:
                messagebox.showerror("Erro", f"Ocorreu um erro inesperado: {response.text}")

        except requests.exceptions.ConnectionError:
            messagebox.showerror("Erro de Conexão", "Não foi possível conectar ao servidor.")

if __name__ == "__main__":
    root = ttk.Window(themename="litera")
    app = LoginApp(root)
    root.mainloop()