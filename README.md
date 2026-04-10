<div align="center">
  <h1>🍳 Nutri-Chef-AI</h1>
  <p><strong>Transform any ingredients into gourmet recipes with the power of Generative AI.</strong></p>
  
  [![Live Demo](https://img.shields.io/badge/Live%20Demo-Visit%20Website-success?style=for-the-badge)](https://nutri-chef-ai-omega.vercel.app/)
</div>

---

## 🌟 Overview

**Nutri-Chef-AI** is an advanced Generative AI application that bridges the gap between machine learning and culinary arts. Utilizing state-of-the-art Large Language Models (LLMs) and Vision AI, the platform empowers users to craft personalized, highly structured recipes based on available ingredients. 

The application goes beyond simple generation: it automatically estimates nutritional information, discovers cover images, and curates a rich experience allowing users to manage a personal cookbook and share creations with the community. It showcases a full ML pipeline—from fine-tuned generation to a production-ready API and front-end interface.

## ✨ Key Features

- **🪄 AI Recipe Generator**: Simply enter the ingredients you have on hand, and let the AI craft a tailored recipe complete with step-by-step instructions and a full nutritional breakdown.
- **📸 Fridge Mode (Vision AI)**: Upload a photo of your fridge or pantry. The integrated Vision AI pipeline detects available ingredients automatically and generates personalized recipes in seconds.
- **📝 Write Your Own Recipe**: Input hand-crafted recipes, and the system will automatically fetch nutritional data and an appealing cover image for you.
- **🌍 Community Recipes**: Discover, save, and interact with what food enthusiasts around the globe are cooking.
- **📖 Personalized Cookbook**: All your generated and saved recipes are securely stored in one beautifully formatted, searchable personal collection.

## 🛠️ Technology Stack

**Backend**
*   **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.x)
*   **AI/ML**: [LangChain](https://python.langchain.com/), [Groq API](https://groq.com/) for lightning-fast inference, Computer Vision.
*   **Database**: PostgreSQL via [SQLAlchemy](https://www.sqlalchemy.org/) & `asyncpg`
*   **Authentication**: bcrypt, custom auth mechanisms.

**Frontend**
*   Vanilla HTML/CSS/JavaScript

**Deployment & CI/CD**
*   **Containerization**: Docker
*   **CI/CD**: GitHub Actions
*   **Hosting**: Railway (Backend), Vercel (Front-end Demo)

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL Server
- Tesseract OCR / compatible Vision Dependencies (If running Fridge Mode locally)
- API Keys: Groq API Key

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/Nutri-Chef-AI.git
   cd Nutri-Chef-AI
   ```

2. **Set up a virtual environment and install dependencies:**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: .\env\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the root directory based on the configuration needed.
   ```env
   # Example .env configuration
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/nutrichefdb
   GROQ_API_KEY=your_groq_api_key
   ```

4. **Run the Backend Server:**
   ```bash
   python main.py
   ```
   The backend will start at `http://localhost:8000`. You can test the API by accessing the Swagger UI at `http://localhost:8000/docs`.

5. **Run the Frontend (Optional for standalone testing):**
   Simply open the `frontend/index.html` file in your preferred web browser, or serve it using tools like Live Server.

## 📁 Project Structure

```
Nutri-Chef-AI/
├── database/         # Database connection and schema definitions (SQLAlchemy)
├── frontend/         # Contains the User Interface (HTML/CSS/JS)
├── routes/           # FastAPI application routes (Auth, Generator, Community)
├── services/         # Core business logic and AI orchestration
├── utils/            # Helper functions and loggers
├── config/           # Application configuration
├── main.py           # FastAPI entry point
├── Dockerfile        # Containerization configurations
└── requirements.txt  # Python dependency list
```

## 📄 License

This project is open-source and available under the terms of the project's [LICENSE](LICENSE).
