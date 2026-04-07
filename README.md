# 🌐 OpenEnv Browser-Based Inference Prototype

A production-ready, browser-based LLM inference prototype designed to pass automated submission benchmarks (e.g., OpenEnv) with 100% compliance.

## ✨ Features
- **Headless Browser Navigation**: Uses **Playwright (Chromium)** to perform real-world web actions (`GOTO`, `CLICK`, `FINAL`).
- **Standardized Architecture**: Follows the official OpenEnv file hierarchy (`envs/` structure).
- **Strict STDOUT Compliance**: Emits only the mandatory `[START]`, `[STEP]`, and `[END]` log blocks for evaluation.
- **Multi-Provider Fallback**: Automatically switches between **Groq**, **OpenAI**, and **Hugging Face** based on your API keys.
- **Submission Gatekeeper**: Includes both PowerShell and Bash scripts for local 3/3 validation.

---

## 📂 Project Structure
```text
├── envs/prototype_env/      # Standardized environment package
│   ├── models.py            # Pydantic models for Action/Observation
│   ├── client.py            # Async HTTP client logic
│   └── server/              # FastAPI backend
│       ├── app.py           # API Entry point (Port 7860)
│       ├── my_environment.py # Browser interaction logic
│       └── Dockerfile       # Subdirectory container config
├── inference.py             # THE AGENT (Main inference loop)
├── Dockerfile               # Root-level Production Dockerfile
├── validate-submission.ps1  # Windows Validation Script
├── validate-submission.sh   # Linux/WSL Validation Script
└── .env.template            # Clean configuration template
```

---

## 🚀 Getting Started

### 1. Setup Environment
Copy the template and add your API keys:
```bash
cp .env.template .env
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt  # (Or manually install: fastapi uvicorn playwright openai httpx)
playwright install chromium
```

### 3. Run Locally (Testing the Agent)
```bash
python inference.py
```

---

## 🛡️ Submission Gatekeeper
Before you submit, ensure you pass the 3-step automatic validation:

**On Windows:**
```powershell
.\validate-submission.ps1 -SpaceUrl http://localhost:7860 -MockBuild
```

**On Linux:**
```bash
./validate-submission.sh http://localhost:7860
```

---

## ☁️ Deployment (Hugging Face Spaces)
1. Create a new **Docker Space** on Hugging Face.
2. Upload the `envs/` folder, `Dockerfile`, and `inference.py`.
3. Add your `API_KEY` and `MODEL_NAME` to the Space **Secrets**.
4. Once running, verify your public URL with the gatekeeper.

---

## ⚖️ License
MIT License. Created for the OpenEnv Hackathon.
