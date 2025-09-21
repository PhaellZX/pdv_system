import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
import requests
from main_view import MainApplication
import sys
import os

# Função para encontrar recursos no ambiente do .exe
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class LoginApp:
    # O __init__ agora é mais simples
    def __init__(self, root):
        self.root = root
        self.root.title("Login - Sistema PDV")
        self.root.geometry("400x300")
        self.root.resizable(True, True)

        try:
            # Usa a função 'resource_path' definida neste arquivo
            icon_path = resource_path('icon.png')
            img = tk.PhotoImage(file=icon_path)
            self.root.iconphoto(False, img)
        except tk.TclError:
            print("Ícone 'icon.png' não encontrado ou inválido.")

        self.root.eval('tk::PlaceWindow . center')
        
        self.main_frame = ttk.Frame(self.root, padding=(20, 20))
        self.main_frame.pack(expand=True, fill=tk.BOTH)
        
        self.create_widgets()
    
    # ... (o resto da classe LoginApp continua exatamente igual) ...
    def create_widgets(self):
        title_label = ttk.Label(self.main_frame, text="Acesso ao Sistema", font=("Segoe UI", 18, "bold"), bootstyle="primary"); title_label.pack(pady=(10, 20))
        form_frame = ttk.Frame(self.main_frame); form_frame.pack(pady=10, fill=tk.X)
        username_label = ttk.Label(form_frame, text="Usuário:", font=("Segoe UI", 10)); username_label.pack(fill=tk.X)
        self.username_entry = ttk.Entry(form_frame, font=("Segoe UI", 10)); self.username_entry.pack(fill=tk.X, pady=(0, 10)); self.username_entry.focus_set()
        password_label = ttk.Label(form_frame, text="Senha:", font=("Segoe UI", 10)); password_label.pack(fill=tk.X)
        self.password_entry = ttk.Entry(form_frame, show="*", font=("Segoe UI", 10)); self.password_entry.pack(fill=tk.X)
        login_button = ttk.Button(self.main_frame, text="➤ Entrar", command=self.attempt_login, bootstyle="primary"); login_button.pack(pady=(20, 10), ipady=5, ipadx=20)
        self.root.bind('<Return>', lambda event=None: login_button.invoke())
    def attempt_login(self):
        username = self.username_entry.get(); password = self.password_entry.get()
        if not username or not password: messagebox.showerror("Erro de Login", "Usuário e senha são obrigatórios."); return
        try:
            response = requests.post(f"http://127.0.0.1:8000/token", data={"username": username, "password": password})
            if response.status_code == 200:
                access_token = response.json().get("access_token")
                self.main_frame.destroy()
                MainApplication(self.root, token=access_token).pack(expand=True, fill=tk.BOTH)
            elif response.status_code == 401: messagebox.showerror("Erro de Login", "Nome de usuário ou senha incorretos.")
            else: messagebox.showerror("Erro", f"Ocorreu um erro inesperado: {response.text}")
        except requests.exceptions.ConnectionError: messagebox.showerror("Erro de Conexão", "Não foi possível conectar ao servidor.")

# Bloco para tornar este arquivo o ponto de entrada
if __name__ == "__main__":
    root = ttk.Window(themename="litera")
    app = LoginApp(root)
    root.mainloop()