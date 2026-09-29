from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from hindsight_client import Hindsight
from groq import Groq
from dotenv import load_dotenv

import os
import sqlite3
import json
import uuid


load_dotenv()


app = FastAPI(title="Meeting Prep Agent")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

HINDSIGHT_URL = os.getenv(
    "HINDSIGHT_URL",
    "http://localhost:8888"
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

hs = Hindsight(base_url=HINDSIGHT_URL)

groq = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

DB = "meetings.db"


# ---------------------------------------------------------
# Database
# ---------------------------------------------------------

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = db()

    con.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            company TEXT
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id TEXT PRIMARY KEY,
            contact_id TEXT NOT NULL,
            date TEXT NOT NULL,
            raw_notes TEXT NOT NULL
        )
    """)

    con.commit()
    con.close()


init_db()


# ---------------------------------------------------------
# Models
# ---------------------------------------------------------

class MeetingIn(BaseModel):
    contact_id: str
    date: str
    notes: str


class ContactIn(BaseModel):
    id: str
    name: str
    company: str = ""


# ---------------------------------------------------------
# Health
# ---------------------------------------------------------

@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "meeting-prep-agent"
    }


# ---------------------------------------------------------
# Contacts
# ---------------------------------------------------------

@app.get("/contacts")
def contacts():
    con = db()

    rows = con.execute(
        "SELECT id, name, company FROM contacts ORDER BY name"
    ).fetchall()

    con.close()

    return [dict(r) for r in rows]


@app.post("/contacts")
def create_contact(c: ContactIn):
    con = db()

    con.execute(
        """
        INSERT OR REPLACE INTO contacts(id, name, company)
        VALUES (?, ?, ?)
        """,
        (c.id, c.name, c.company),
    )

    con.commit()
    con.close()

    return {
        "status": "created",
        "contact": c.model_dump()
    }


# ---------------------------------------------------------
# Meeting history
# ---------------------------------------------------------

@app.get("/contacts/{contact_id}/meetings")
def contact_meetings(contact_id: str):
    con = db()

    rows = con.execute(
        """
        SELECT id, contact_id, date, raw_notes
        FROM meetings
        WHERE contact_id=?
        ORDER BY date DESC
        """,
        (contact_id,),
    ).fetchall()

    con.close()

    return [dict(r) for r in rows]


# ---------------------------------------------------------
# Groq memory extraction
# ---------------------------------------------------------

def extract_memory(notes: str):

    # If Groq is unavailable, still keep the raw meeting.
    if not groq:
        return {
            "summary": notes,
            "priorities": [],
            "concerns": [],
            "commitments": [],
        }

    prompt = f"""
Extract structured meeting memory from these notes.

Return ONLY valid JSON with:

summary: string
priorities: array of strings
concerns: array of strings
commitments: array of strings

A commitment can be something either person promised to do,
especially with a deadline.

NOTES:
{notes}
"""

    try:

        result = groq.chat.completions.create(
            model="openai/gpt-oss-120b",
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract concise structured meeting facts."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        return json.loads(
            result.choices[0].message.content
        )

    except Exception:

        return {
            "summary": notes,
            "priorities": [],
            "concerns": [],
            "commitments": [],
        }


# ---------------------------------------------------------
# Meeting logging
# ---------------------------------------------------------

@app.post("/meetings")
def log_meeting(m: MeetingIn):

    # Make sure contact exists.
    con = db()

    exists = con.execute(
        "SELECT 1 FROM contacts WHERE id=?",
        (m.contact_id,),
    ).fetchone()

    if not exists:
        con.close()

        raise HTTPException(
            status_code=404,
            detail="Contact not found"
        )

    meeting_id = (
        f"{m.contact_id}-{m.date}-"
        f"{uuid.uuid4().hex[:6]}"
    )

    # Always save the meeting locally first.
    con.execute(
        "INSERT INTO meetings VALUES (?,?,?,?)",
        (
            meeting_id,
            m.contact_id,
            m.date,
            m.notes,
        ),
    )

    con.commit()
    con.close()

    # Extract structured information.
    extracted = extract_memory(m.notes)

    memory_content = json.dumps(
        {
            "meeting_date": m.date,
            "raw_notes": m.notes,
            "extracted": extracted,
        },
        ensure_ascii=False,
    )

    # -----------------------------------------------------
    # Try Hindsight.
    # If unavailable, local SQLite memory remains usable.
    # -----------------------------------------------------

    try:

        hs.retain(
            bank_id=m.contact_id,
            content=memory_content,
            context=f"Meeting on {m.date}",
            timestamp=f"{m.date}T10:00:00Z",
        )

        memory_source = "hindsight"

    except Exception:

        memory_source = "local"


    return {
        "status": "retained",
        "memory_source": memory_source,
        "meeting_id": meeting_id,
        "extracted": extracted,
    }


# ---------------------------------------------------------
# Meeting Brief
# ---------------------------------------------------------

@app.get("/brief/{contact_id}")
def get_brief(contact_id: str):

    # =====================================================
    # PRIMARY PATH: HINDSIGHT
    # =====================================================

    try:

        recalled = hs.recall(
            bank_id=contact_id,
            query=(
                "upcoming meeting preparation: priorities, "
                "concerns, commitments, decisions, "
                "unresolved issues, recent changes"
            ),
        )

        reflection = hs.reflect(
            bank_id=contact_id,
            query=(
                "Prepare a concise meeting brief with: "
                "current priority, biggest concern, "
                "my open commitments, their open commitments, "
                "what changed recently, suggested talking "
                "points and questions. "
                "If facts conflict, trust the most recent one."
            ),
        )

        return {
            "memory_trace": recalled,
            "brief": getattr(
                reflection,
                "text",
                str(reflection)
            ),
            "memory_source": "hindsight",
        }


    # =====================================================
    # FALLBACK PATH: LOCAL SQLITE MEMORY
    # =====================================================

    except Exception:

        con = db()

        rows = con.execute(
            """
            SELECT date, raw_notes
            FROM meetings
            WHERE contact_id=?
            ORDER BY date ASC
            """,
            (contact_id,),
        ).fetchall()

        con.close()


        if not rows:

            raise HTTPException(
                status_code=404,
                detail="No meeting history found"
            )


        # -------------------------------------------------
        # Memory Trace
        # -------------------------------------------------

        memory_trace = [
            {
                "date": row["date"],
                "notes": row["raw_notes"],
            }
            for row in rows
        ]


        # -------------------------------------------------
        # Generate brief using Groq
        # -------------------------------------------------

        if groq:

            history = "\n\n".join(
                (
                    f"Meeting on {row['date']}:\n"
                    f"{row['raw_notes']}"
                )
                for row in rows
            )

            prompt = f"""
You are a meeting preparation assistant.

Use the remembered meeting history below to prepare
a concise, useful meeting brief.

Focus on:

1. Current priority
2. Biggest concern
3. Open commitments
4. Recent changes
5. Suggested talking points
6. Questions to ask

IMPORTANT:
If information changed over time, prefer the most
recent information.

MEETING HISTORY:

{history}
"""

            try:

                result = groq.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    temperature=0,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You prepare concise meeting briefs "
                                "using remembered relationship history."
                            ),
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                )

                brief = result.choices[0].message.content

            except Exception:

                brief = rows[-1]["raw_notes"]

        else:

            brief = rows[-1]["raw_notes"]


        return {
            "memory_trace": memory_trace,
            "brief": brief,
            "memory_source": "local",
        }