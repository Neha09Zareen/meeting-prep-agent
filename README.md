# Meeting Prep AI Agent

A hackathon MVP based on the supplied 24-hour workflow.

Core flow:
1. Log a meeting.
2. Store the relationship memory in Hindsight.
3. Recall relevant memories.
4. Reflect over them to create a "Before You Walk In" brief.
5. Show the raw recall results as a Memory Trace.

## Stack
- Hindsight for persistent relationship memory
- Groq for LLM extraction / Hindsight LLM provider
- FastAPI + SQLite backend
- React + Vite frontend

## Backend setup (Windows PowerShell)

```powershell
cd backend
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Put your Groq API key in `.env`.

Start Hindsight separately using Docker (see the workflow PDF).

Then:

```powershell
uvicorn main:app --reload
```

Backend: http://localhost:8000

## Frontend

Open another PowerShell:

```powershell
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

## Seed demo data

After the backend is running:

```powershell
cd backend
python seed.py
```

The seed creates Sarah, Rahul and Ananya demo histories designed to show memory, commitments and changing priorities.

## Important demo moment

Log a NEW meeting for Sarah, then click Prepare again. The brief should incorporate the new memory. This is the key "agent learns from the relationship" moment.
