# POS System with Sales Forecasting (Desktop)

## 🎯 Overview

This repository features a Point of Sale (POS) and inventory management desktop solution. Built with Python, it integrates an intuitive Graphical User Interface (GUI) with a FastAPI backend and Machine Learning algorithms to predict product demand. The compiled application is distributed as two independent executables: one for the backend server and another for the client GUI interface.

## 🛠️ Tech Stack

* **Programming Language:** Python 3.10+
* **Graphical User Interface (GUI):** Tkinter enhanced with `ttkbootstrap` modern themes.
* **Backend API:** Local REST API built with FastAPI and hosted via Uvicorn.
* **Database Engine:** MongoDB.
* **Machine Learning Engine:** Facebook's `Prophet` for time series sales forecasting.
* **Executable Packaging:** `PyInstaller` for standalone binary creation.
* **Data Manipulation:** `Pandas` for dataset processing.
* **Document Generation:** `Pillow` (PIL) for image receipt rendering.
* **Data Visualization:** `Matplotlib` for dashboard analytics charts.

## ✨ Features

* **Role-Based Authentication:** Secure user access control system.
* **Inventory Management:** Full CRUD operations, real-time stock tracking, and complete JSON database backup/restore functionality.
* **Point of Sale (POS):** Fast-checkout cashier terminal with automatic change calculation.
* **Receipt Generation:** Automatic visual image receipt (.png) rendering upon transaction completion.
* **Analytics Dashboard:** Executive KPI monitoring (Total Revenue, Sales Volume, Average Ticket Size) and graphical sales insights.
* **Sales Forecasting (AI):** Machine Learning pipeline predicting future product demand based on historical transaction logs.
* **User Provisioning:** Administrative endpoint management for creating new user credentials.

## 📁 Repository Structure

```text
├── assets/
│   ├── fonts/
│   │   └── DejaVuSansMono.ttf
│   ├── icons/
│   │   ├── icon.ico
│   │   └── icon.png
│   └── images/
│       └── Screenshot_1.png
├── build_scripts/
│   ├── app.spec
│   └── server.spec
├── config/
├── src/
│   ├── core/
│   ├── forecasting/
│   ├── utils/
│   │   ├── receipt_generator.py
│   │   └── setup_db.py
│   └── views/
│       ├── forecast_view.py
│       ├── login_view.py
│       ├── main_view.py
│       ├── pos_view.py
│       ├── product_view.py
│       └── reports_view.py
├── tests/
├── .gitignore
├── main.py
├── README.md
├── requirements.txt
├── run.py
└── run_server.py
```

##  🚀 Installation & Setup

Follow these steps to set up your local development environment.

**1. Prerequisites:**
* **Python 3.10+** Download and install from [python.org](https://www.python.org/downloads/)
* **MongoDB Community Server:** Ensure MongoDB is installed and running locally on standard port 27017. Download from [MongoDB Community](https://www.mongodb.com/try/download/community).

**2. Environment Setup:**
* Clone this repository and navigate to the project directory:

```bash
git clone [https://github.com/PhaellZX/pdv_system.git](https://github.com/PhaellZX/pdv_system.git)
cd pdv_system
```

Create and activate a Python virtual environment:

```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**3. Install Dependencies:**
```bash
pip install -r requirements.txt
```

**4. Database Initialization:**

Run the setup script to seed the database with default administrator credentials (admin / admin123):

```bash
python -m src.utils.setup_db
```

## ⚡ Running the Application

### Development Mode

Requires two separate terminal sessions:

1. Terminal 1 - Backend Server:

```bash
uvicorn main:app --reload
```

2. Terminal 2 - Client Desktop Interface:

```bash
python run.py
```

### Standalone Server Mode

If running the dedicated server host script directly:

```bash
python run_server.py
```

## 📦 Building Executable Binaries (PyInstaller)

To compile the application into standalone executables:

1. Ensure PyInstaller is installed:

```bash
pip install pyinstaller
```

2. Build Server Executable:

```bash
pyinstaller build_scripts/server.spec
```

3. Build GUI Client Executable:

```bash
pyinstaller build_scripts/app.spec
```

Upon completion, compiled binaries will be output into the dist/ directory.

---