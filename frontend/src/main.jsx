import React, { useEffect, useState } from "react"
import { createRoot } from "react-dom/client"
import "./styles.css"

const API = "http://localhost:8000"

function findCommitments(meetings) {
  const text = meetings.map(m => m.raw_notes).join(" ")
  const commitments = []

  if (/roadmap/i.test(text)) {
    commitments.push({
      title: "Send the implementation roadmap",
      status: /still waiting|still not sent|overdue/i.test(text)
        ? "Still pending"
        : "Mentioned in meetings",
      detail: "Sarah is waiting for the roadmap.",
    })
  }

  if (/follow up with finance|budget approval/i.test(text)) {
    const approved = /finance approved|budget approved|approved the budget/i.test(text)

    commitments.push({
      title: approved
        ? "Budget approval"
        : "Follow up with Finance",
      status: approved
        ? "Completed"
        : "Still pending",
      detail: approved
        ? "Finance approved the budget. Next: finalize the implementation schedule."
        : "Budget approval needs a concrete status update.",
    })
  }

  return commitments
}

function App() {
  const [contacts, setContacts] = useState([])
  const [selected, setSelected] = useState(null)
  const [brief, setBrief] = useState(null)
  const [meetings, setMeetings] = useState([])
  const [loading, setLoading] = useState(false)
  const [showMeetingForm, setShowMeetingForm] = useState(false)
const [newNotes, setNewNotes] = useState("")

  async function loadContacts() {
    const r = await fetch(`${API}/contacts`)
    setContacts(await r.json())
  }

  async function openContact(c) {
    setSelected(c)
    setBrief(null)

    const r = await fetch(`${API}/contacts/${c.id}/meetings`)
    setMeetings(await r.json())
  }

  async function prepare() {
    if (!selected) return

    setLoading(true)

    try {
      const r = await fetch(`${API}/brief/${selected.id}`)
      const data = await r.json()

      if (!r.ok) {
        throw new Error(data.detail || "Could not prepare brief")
      }

      setBrief(data)
    } catch (e) {
      alert(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function addMeeting() {
  if (!selected || !newNotes.trim()) return

  try {
    const r = await fetch(`${API}/meetings`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        contact_id: selected.id,
        date: new Date().toISOString().slice(0, 10),
        notes: newNotes,
      }),
    })

    if (!r.ok) {
      const data = await r.json()
      throw new Error(data.detail || "Could not save meeting")
    }

    setNewNotes("")
    setShowMeetingForm(false)

    await openContact(selected)
    setBrief(null)
  } catch (e) {
    alert(e.message)
  }
}

  useEffect(() => {
    loadContacts()
  }, [])

  const commitments = findCommitments(meetings)

  return (
    <div className="app">
      <header>
        <div>
          <div className="eyebrow">MEETING PREP AI</div>
          <h1>Walk in prepared.</h1>
          <p>Your relationship memory, not just your last meeting.</p>
        </div>
      </header>

      <main>

        {/* PEOPLE */}
        <section className="panel">
          <h2>People</h2>

          <div className="contacts">
            {contacts.map(c => (
              <button
                key={c.id}
                className={`contact ${
                  selected?.id === c.id ? "active" : ""
                }`}
                onClick={() => openContact(c)}
              >
                <strong>{c.name}</strong>
                <span>{c.company}</span>
              </button>
            ))}
          </div>
        </section>

        {/* CONTACT PROFILE */}
        {selected && (
          <section className="panel">

            <div className="profileHead">
              <div>
                <h2>{selected.name}</h2>
                <p>{selected.company}</p>
              </div>

              <button
                className="primary"
                onClick={prepare}
                disabled={loading}
              >
                {loading ? "Preparing..." : "Prepare me"}
              </button>
            </div>
<div style={{ marginBottom: "16px" }}>
  <button
    className="primary"
    onClick={() => setShowMeetingForm(!showMeetingForm)}
  >
    {showMeetingForm ? "Cancel" : "+ Log New Meeting"}
  </button>

  {showMeetingForm && (
    <div style={{ marginTop: "12px" }}>
      <textarea
        value={newNotes}
        onChange={(e) => setNewNotes(e.target.value)}
        placeholder="What happened in the meeting?"
        rows="4"
        style={{ width: "100%", marginBottom: "8px" }}
      />

      <button className="primary" onClick={addMeeting}>
        Save Meeting
      </button>
    </div>
  )}
</div>

            <h3>Meeting history</h3>

            <div className="meetings">
              {meetings.map(m => (
                <article key={m.id}>
                  <time>{m.date}</time>
                  <p>{m.raw_notes}</p>
                </article>
              ))}
            </div>

          </section>
        )}

        {/* MEETING BRIEF */}
        {brief && (
          <section className="panel">

            <div className="briefTitle">
              <div>
                <div className="eyebrow">BEFORE YOU WALK IN</div>
                <h2>Meeting Brief</h2>
              </div>

              <span className="memoryBadge">
                Memory-powered
              </span>
            </div>

            <div className="briefText">
              {brief.brief}
            </div>

            {/* COMMITMENT TRACKER */}
            {commitments.length > 0 && (
              <div className="commitmentBox">

                <div className="commitmentHeader">
                  <div>
                    <div className="eyebrow">
                      FOLLOW-UPS
                    </div>
                    <h3>Commitment Tracker</h3>
                  </div>
                </div>

                {commitments.map((item, index) => (
                  <div
                    className="commitment"
                    key={index}
                  >
                    <div className="commitmentStatus">
                      {item.status}
                    </div>

                    <strong>
                      {item.title}
                    </strong>

                    <p>
                      {item.detail}
                    </p>
                  </div>
                ))}

              </div>
            )}

            {/* MEMORY TRACE */}
            <details className="trace">
              <summary>
                Why do I know this? — Memory Trace
              </summary>

              <div className="traceList">
                {brief.memory_trace?.map((item, index) => (
                  <div className="traceItem" key={index}>
                    <strong>{item.date}</strong>
                    <p>{item.notes}</p>
                  </div>
                ))}
              </div>
            </details>

          </section>
        )}

      </main>
    </div>
  )
}

createRoot(
  document.getElementById("root")
).render(<App />)