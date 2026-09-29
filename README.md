# RecallOps — AI Incident Response Agent

> **Turn past incidents into faster decisions with Hindsight persistent memory.**

---

## Problem

Production incidents frequently repeat across services and deployment cycles, but on-call engineers waste precious minutes or hours rediscovering diagnoses, re-debugging connection pools, or hunting for old Slack threads and post-mortems. Stateless LLMs treat every incident like day one—they lack organizational context, cannot recall what fixed an outage last week, and cannot improve from operational experience.

## Solution

**RecallOps** is an AI incident-response agent powered by **Hindsight persistent memory**. It remembers an organization's historical production outages, recalls relevant precedents when a new incident occurs, provides context-aware root cause analysis with recommended actions, and retains human-verified fixes into persistent memory so the next outage is resolved even faster.

## Key Innovation

**The agent continuously improves through accumulated operational experience.** Rather than relying on generic prompt engineering or ephemeral chat history, RecallOps grounds every troubleshooting recommendation in verified institutional knowledge.

---

## Hindsight Usage

The application demonstrates the four pillars of Hindsight memory:

* **RETAIN**: Historical incident post-mortems and newly verified incident resolutions are committed to Hindsight persistent memory (`bank_id: recallops-demo`).
* **RECALL**: When a new incident is submitted, RecallOps queries Hindsight memory for semantically matching symptoms, connection patterns, and previous fixes.
* **REASON**: The LLM synthesizes live error logs with the recalled historical memories to produce a structured, high-confidence diagnosis without hallucination.
* **LEARN**: Once the on-call engineer verifies the fix, clicking **"Save Resolution to Memory"** retains the solution back into Hindsight, closing the learning loop.

---

## Architecture

```
                          ┌───────────────────────────┐
                          │   Active Incident Report  │
                          │   (Service, Logs, Env)    │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │   Flask Backend API       │
                          └──────┬─────────────▲──────┘
                                 │             │
                    1. Semantic  │             │ 4. Retain Verified Fix
                    Recall Query │             │    (Close Learning Loop)
                                 ▼             │
    ┌──────────────────────────────────────────┴────────────────────────┐
    │                 HINDSIGHT PERSISTENT MEMORY                       │
    │  • Bank: recallops-demo                                           │
    │  • Historical Post-Mortems (Payment, Redis, DB Pool, Auth 502)     │
    │  • Newly Retained Verified Resolutions                            │
    └────────────────────────────┬──────────────────────────────────────┘
                                 │
                     2. Relevant │ Historical
                        Memories │
                                 ▼
                          ┌─────────────┐
                          │     LLM     │ (Groq llama-3.3-70b-versatile
                          │  Reasoning  │  or OpenAI gpt-4o-mini)
                          └──────┬──────┘
                                 │
                     3. Structured Diagnosis
                        & Mitigations
                                 ▼
                     ┌───────────────────────┐
                     │   RecallOps UI        │
                     │  • LIKELY CAUSE       │
                     │  • CONFIDENCE         │
                     │  • SIMILAR INCIDENTS  │
                     │  • RECOMMENDED ACTIONS│
                     │  • WHY MEMORY HELPED  │
                     └───────────────────────┘
```

---

## Setup & Running

### 1. Clone & Enter Directory
```powershell
cd RecallOps_Hackathon_Prototype
```

### 2. Create and Activate Virtual Environment
```powershell
# Create venv (if not already created)
python -m venv .venv

# Windows activation:
.\.venv\Scripts\activate

# macOS / Linux activation:
source .venv/bin/activate
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```powershell
# Copy template
copy .env.example .env
```

Edit `.env` and fill in your API credentials:
```ini
HINDSIGHT_API_KEY=your_hindsight_api_key_here
HINDSIGHT_URL=https://api.hindsight.vectorize.io
HINDSIGHT_BANK_ID=recallops-demo

GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

*(Note: If you prefer OpenAI, you can set `OPENAI_API_KEY=your_key` instead of `GROQ_API_KEY`.)*

### 5. Start the Application
```powershell
python app.py
```

Open your browser to: **`http://127.0.0.1:5000`**

---

## 60-Second Demo Sequence

1. **Verify Status**: Confirm the top pills display `HINDSIGHT MEMORY ENABLED` and your LLM model.
2. **Seed Organizational Memory**: Click **"Load Demo Memory"**. Hindsight retains 8 realistic incident post-mortems covering Payment API, Redis saturation, database pool exhaustion, and deployment errors.
3. **Analyze Initial Incident**: Click **Preset 1 ("1. Payment 503 Outage")**, then click **"Analyze with Memory →"**.
   * Notice the right panel displays **"MEMORIES RECALLED"** from Hindsight.
   * Review the diagnosis: `LIKELY CAUSE: Database connection pool exhaustion`, `CONFIDENCE: High`, `RECOMMENDED ACTIONS`, and `WHY MEMORY HELPED`.
4. **Close the Learning Loop**: In the **"Close the Learning Loop"** panel, click **"⚡ Pre-fill Verified Fix for Demo"**, then click **"Save Resolution to Memory"**.
   * Hindsight retains the verified fix (`"Resolution learned by Hindsight."`).
5. **Demonstrate Experience & Recall**: Click **Preset 2 ("2. Reworded Payment (Test Learning Loop)")**:
   * Error text: *"Customers are experiencing intermittent payment failures. The API is returning 503 responses and logs show database connection timeouts after release 2.4.1."*
   * Click **"Analyze with Memory →"**.
   * **The Wow Moment**: RecallOps retrieves the newly retained verified resolution from Step 4! The AI diagnosis cites the newly learned fix as the primary recommended action.

---

## Environment Variables Reference

| Variable | Description | Default |
| :--- | :--- | :--- |
| `HINDSIGHT_API_KEY` | Your Hindsight Cloud API key | Required |
| `HINDSIGHT_URL` | Hindsight API base URL | `https://api.hindsight.vectorize.io` |
| `HINDSIGHT_BANK_ID` | Persistent bank identifier | `recallops-demo` |
| `GROQ_API_KEY` | Groq Cloud API key (recommended) | Optional (or OpenAI) |
| `GROQ_MODEL` | Groq model identifier | `llama-3.3-70b-versatile` |
| `OPENAI_API_KEY` | OpenAI API key (fallback if Groq unset) | Optional |
| `PORT` | Local web server port | `5000` |

---

## Future Improvements

* Automated Slack/PagerDuty webhook ingestion for real-time incident triage.
* Multi-modal log parsing (supporting Prometheus time-series and Kubernetes events).
* Bi-directional sync with Jira / Confluence incident post-mortem repositories.
