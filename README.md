# cyberpy
belajar cyber, belajar python, belajar github

# 🚀 FastAPI Setup Guide (From Zero to Running)

Panduan lengkap setup **FastAPI** dari nol sampai aplikasi berjalan di browser.
Cocok untuk pemula, project backend, microservices, dan production preparation.

---

## 📦 Prerequisites

Pastikan sudah terinstall:

* Python 3.9+
* pip
* Git

Cek versi:

```bash
python --version
pip --version
git --version
```

---

## 🏗️ 1. Buat Folder Project

```bash
mkdir cyberpy
cd cyberpy
```

---

## 🧪 2. Buat Virtual Environment

```bash
python -m venv venv
```

### Aktivasi venv

**Windows:**

```bash
venv\Scripts\activate
```

**Linux/Mac:**

```bash
source venv/Scripts/activate
```

---

## 📥 3. Install Requirements.txt

```bash
pip install -r requirements.txt
```

Simpan dependency:

```bash
pip freeze > requirements.txt
```

---

## 📁 4. Struktur Project

```
fastapi-project/
│
├── app/
│   ├── main.py
│   └── __init__.py
│
├── venv/
├── requirements.txt
└── .gitignore
```

---

## 🧠 5. Buat File Aplikasi

### app/main.py

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "FastAPI running 🚀"}
```

---

## ▶️ 6. Jalankan Server

```bash
uvicorn app.main:app --reload
```

---

## 🌍 7. Akses Aplikasi

Buka browser:

```
http://127.0.0.1:8000
```

Output:

```json
{
  "message": "FastAPI running 🚀"
}
```

---

## 📚 8. API Documentation (Otomatis)

FastAPI menyediakan dokumentasi otomatis:

### Swagger UI

```
http://127.0.0.1:8000/docs
```

### ReDoc

```
http://127.0.0.1:8000/redoc
```

---

## 🧹 9. .gitignore

Buat file `.gitignore`

```
venv/
__pycache__/
*.pyc
.env
.idea/
.vscode/
```

---

## 🧬 10. Init Git Repository

```bash
git init
git add .
git commit -m "Initial FastAPI setup"
```

---

## 🌍 11. Push ke GitHub

### Buat repo di GitHub

* Login GitHub
* New Repository
* Repo name: `cyberpy`
* Jangan centang README

### Connect ke repo

```bash
git remote add origin https://github.com/df1g45/cyberpy.git
git branch -M main
git push -u origin main
```

---

## ✅ Status Akhir

* FastAPI terinstall ✅
* Server running ✅
* Docs aktif ✅
* Virtual env aktif ✅
* Git repo siap ✅
* GitHub repo online ✅

---

## 🔥 Next Level (Opsional)

Upgrade ke:

* JWT Auth
* PostgreSQL
* SQLAlchemy
* Alembic
* Docker
* CI/CD
* Cloud deploy
* Microservices
* API Gateway

---

## 🎯 Target Learning Path

Beginner → Intermediate → Advanced → Production → Enterprise

---

## 👨‍💻 Author

Muhammad Daffa Al Farizi
Backend Developer | Fullstack Engineer

---

> "Start simple. Build clean. Scale smart." 🚀
