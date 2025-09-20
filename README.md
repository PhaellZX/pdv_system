#  Sistema de PDV com Previsão de Vendas (Desktop)

![Screenshot da Tela de PDV](imgs/Screenshot_1.png)

## 🎯 Objetivo

Este projeto é um sistema completo de Ponto de Venda (PDV) e gestão de estoque para desktop. Desenvolvido em Python, ele combina uma interface gráfica intuitiva com um backend robusto e funcionalidades de Inteligência Artificial para prever a demanda de produtos.

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.10+
* **Interface Gráfica (Frontend):** Tkinter, com temas profissionais da `ttkbootstrap`.
* **Backend:** API local com FastAPI, rodando com Uvicorn.
* **Banco de Dados:** MongoDB.
* **Inteligência Artificial:** `Prophet` (do Facebook) para previsão de séries temporais.
* **Análise de Dados:** `Pandas` para manipulação de dados.
* **Geração de Imagens:** `Pillow` para a criação de recibos.
* **Gráficos:** `Matplotlib` para a visualização de dados nos relatórios.

## ✨ Funcionalidades

O sistema é dividido nos seguintes módulos:

* **Autenticação por Perfil:** Sistema de login seguro com diferentes níveis de acesso (admin, gerente, caixa).
* **Gestão de Produtos:**
    * CRUD completo (Criar, Ler, Atualizar, Inativar) para produtos.
    * Suporte a código de barras.
    * Controle de estoque.
* **Ponto de Venda (PDV):**
    * Interface ágil para registro de vendas.
    * Busca de produtos por nome ou código de barras.
    * Cálculo de troco para pagamentos em dinheiro.
* **Geração de Recibos:** Criação automática de um comprovante visual (imagem .png) após cada venda.
* **Dashboard de Relatórios:**
    * Visualização de KPIs (Faturamento, N° de Vendas, Ticket Médio).
    * Gráfico com os produtos mais vendidos.
* **Previsão de Vendas (IA):**
    * Utiliza o histórico de vendas para prever a demanda futura de cada produto.
    * Exibe um gráfico com a previsão para os próximos dias.
* **Backup e Restauração:** Funcionalidade para exportar e importar o cadastro de produtos em formato JSON.

## 🚀 Como Instalar e Configurar

Siga os passos abaixo para configurar o ambiente e executar o projeto.

**1. Pré-requisitos:**
* **Python 3.10 ou superior:** [python.org](https://www.python.org/downloads/)
* **MongoDB Community Server:** É necessário ter o MongoDB instalado e rodando na sua máquina. [Faça o download aqui](https://www.mongodb.com/try/download/community).

**2. Setup do Projeto:**
* Clone este repositório ou baixe os arquivos para uma pasta no seu computador.
* Abra o terminal e navegue até a pasta do projeto.

**3. Crie um Ambiente Virtual:**
É uma boa prática isolar as dependências do projeto.
```bash
# Cria o ambiente virtual
python -m venv venv

# Ativa o ambiente (Windows)
.\venv\Scripts\activate

# Ativa o ambiente (Linux/Mac)
source venv/bin/activate
```

**4. Instale as Dependências:**
Todas as bibliotecas necessárias estão listadas no arquivo `requirements.txt`.
```bash
pip install -r requirements.txt
```

**5. Configure a Fonte e o Ícone:**
* Para a geração de recibos, baixe a fonte **DejaVu Sans Mono** e coloque o arquivo `DejaVuSansMono.ttf` na pasta do projeto.
* (Opcional) Para o ícone da janela, adicione uma imagem `icon.png` na pasta do projeto.

**6. Crie o Primeiro Usuário no Banco:**
Execute o script `create_first_user.py` para criar um usuário `admin` com a senha `admin123`.
```bash
python create_first_user.py
```

## ⚡ Como Executar

Com o ambiente configurado, siga estes 3 passos em terminais separados:

**1. Inicie o Banco de Dados:**
* Certifique-se de que o serviço do MongoDB está em execução.

**2. Inicie o Servidor Backend:**
* No terminal, com o ambiente virtual ativado, execute:
    ```bash
    uvicorn main:app --reload
    ```

**3. Inicie a Aplicação Desktop (Frontend):**
* Em **outro** terminal, também com o ambiente virtual ativado, execute:
    ```bash
    python login_app.py
    ```
* A tela de login aparecerá. Use as credenciais `admin` / `admin123`.

---