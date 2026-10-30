# 📚 StudyVault — Your Digital Learning Library

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:141E30,50:243B55,100:00C9FF&height=220&section=header&text=StudyVault&fontSize=60&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=Your%20Knowledge.%20Your%20Library.%20Your%20Future.&descAlignY=60&descSize=17" width="100%" />
</p>

<p align="center">
  <strong>A modern digital library built to make learning, discovering, and managing educational resources easier.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Project-StudyVault-00C9FF?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Frontend-React-61DAFB?style=for-the-badge&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/Backend-Flask-000000?style=for-the-badge&logo=flask" />
  <img src="https://img.shields.io/badge/Database-SQLite-003B57?style=for-the-badge&logo=sqlite" />
</p>

<p align="center">
  <a href="#-overview">Overview</a> •
  <a href="#-features">Features</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-project-structure">Structure</a> •
  <a href="#-contributing">Contributing</a>
</p>

---

## 🌟 Overview

**StudyVault** is a student-focused Digital Library Platform designed to provide a centralized space for storing, discovering, accessing, and managing educational resources.

Instead of searching through multiple platforms and scattered files, students can use StudyVault to organize their learning materials in one place.

The platform combines a modern React interface with a Flask-powered backend and SQLite database to deliver a simple and convenient digital learning experience.

### 🎯 Our Mission

> Making educational resources more accessible, organized, and convenient for every learner.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 User Authentication | Secure registration and login workflows |
| 📤 Resource Upload | Upload and manage educational PDF resources |
| 🔍 Smart Search | Search for available learning materials |
| 📖 PDF Preview | Preview supported PDF documents |
| 📥 File Download | Access and download available resources |
| 🛡️ Duplicate Detection | Prevent duplicate document uploads |
| 📊 Preview Tracking | Track document preview activity |
| 🌗 Theme Support | Light and dark mode interface |
| 📱 Responsive UI | Designed for different screen sizes |

---

## 🖥️ Tech Stack

<p align="center">
  <img src="https://skillicons.dev/icons?i=react,vite,js,python,flask,sqlite,html,css,git,github,vscode" />
</p>

### Frontend
- React.js
- Vite
- JavaScript
- HTML5
- CSS3

### Backend
- Python
- Flask
- REST API

### Database
- SQLite

### Development Tools
- Visual Studio Code
- Git & GitHub
- Ngrok (for development tunneling)

---

## 📸 Application Preview

<p align="center">
  <strong>Explore the StudyVault interface</strong>
</p>

> Add your actual application screenshots below.

| Home Page | Digital Library |
|---|---|
| Add homepage screenshot | Add library screenshot |
| PDF Preview | User Dashboard |
| Add preview screenshot | Add dashboard screenshot |

---

## ⚙️ Installation & Setup

Follow these steps to run StudyVault locally.

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
```

```bash
cd StudyVault
```

### 2. Backend Setup

Open a terminal:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it:

**Windows**
```bash
venv\Scripts\activate
```

**macOS / Linux**
```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the Flask backend:

```bash
python run.py
```

### 3. Frontend Setup

Open another terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

### 4. Open the Application

Visit the local frontend URL displayed in your terminal, usually:

```text
http://localhost:5173
```

> **Note:** Start the backend and frontend in separate terminals. Make sure the backend configuration and API URL match your local environment.

---

## 📁 Project Structure

```text
StudyVault/
│
├── backend/
│   ├── routes/
│   ├── services/
│   ├── database.db
│   ├── run.py
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── assets/
│   │   └── ...
│   ├── package.json
│   └── vite.config.js
│
├── README.md
└── .gitignore
```

*Folder structure may vary depending on the current project implementation.*

---

## 🔒 Security & Best Practices

- Keep API keys and credentials in environment variables.
- Never commit `.env` files or sensitive credentials.
- Validate uploaded files on the backend.
- Restrict access to protected resources.
- Avoid exposing internal server paths to users.
- Keep dependencies updated.

---

## 🛣️ Future Enhancements

The following ideas can be explored in future versions:

- [ ] AI-powered PDF Smart Summarization
- [ ] Personalized learning recommendations
- [ ] Advanced document categorization
- [ ] Learning progress dashboard
- [ ] More document formats
- [ ] Improved resource discovery

---

## 🤝 Contributing

Contributions are welcome!

1. Fork this repository.
2. Create a new branch.

```bash
git checkout -b feature/your-feature-name
```

3. Make your changes.
4. Commit your changes.

```bash
git commit -m "Add: your feature description"
```

5. Push your branch.

```bash
git push origin feature/your-feature-name
```

6. Open a Pull Request.

---

## 👨‍💻 Developer

<p align="center">
  <strong>Developed with ❤️ by Rohith</strong>
  <br/>
  <a href="https://github.com/rohith-1806">GitHub</a> •
  <a href="https://rohith06-portfolio.netlify.app/">Portfolio</a>
</p>

<p align="center">
  If you find StudyVault useful, consider giving this repository a ⭐
</p>

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:00C9FF,50:243B55,100:141E30&height=120&section=footer" width="100%" />
</p>

<p align="center">
  <sub>StudyVault — Empowering students through accessible digital learning.</sub>
</p>
