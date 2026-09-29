# RecallOps — AI Incident Response Agent
> **Turn past production outages into faster decisions with Hindsight persistent memory.**

---

## 📌 Executive Summary

**RecallOps** is an autonomous AI incident-response agent designed for Site Reliability Engineers (SREs) and DevOps teams. Unlike conventional stateless AI chatbots that diagnose every outage from scratch, RecallOps leverages **Hindsight persistent memory** to remember an organization's historical incidents, recall relevant precedents when new alerts fire, provide context-aware root cause analysis, and continuously learn verified human resolutions for future outages.

The core differentiator is simple yet transformative: **The agent gets smarter and faster with every incident it resolves.**

---

## 🚨 The Problem

* **Recurring Outages:** Production incidents frequently repeat across deployment cycles (e.g., database connection pool exhaustion, Redis cache stampedes, or misconfigured TLS handshakes).
* **Tribal Knowledge Loss:** Solutions remain scattered across Slack threads, Jira tickets, and buried Google Docs. When on-call at 3:00 AM, engineers waste hours rediscovering solutions that someone already solved last month.
* **The "Day-One" Flaw of Stateless LLMs:** Standard AI coding assistants and chatbots have zero memory of your production architecture or past post-mortems. They offer generic advice rather than institutional operational memory.

---

## 💡 The Solution: Hindsight-Powered Operational Memory

RecallOps bridges the gap between active incident telemetry and persistent organizational knowledge. By embedding the **Hindsight memory engine**, RecallOps implements a continuous operational feedback loop:

$$\text{RETAIN} \longrightarrow \text{RECALL} \longrightarrow \text{REASON} \longrightarrow \text{LEARN}$$

1. **RETAIN (Institutional Memory):** Historical post-mortems, architecture quirks, and verified resolutions are indexed into persistent Hindsight banks (`recallops-demo`).
2. **RECALL (Semantic Precedents):** When an alert triggers, RecallOps queries Hindsight for semantically matching symptoms, connection patterns, and previous fixes—even when current logs are worded completely differently.
3. **REASON (Context-Aware Diagnosis):** The LLM synthesizes live error logs alongside retrieved historical precedents to output a structured 5-part triage report:
   * **LIKELY CAUSE:** Concrete technical hypothesis backed by past evidence.
   * **CONFIDENCE:** Calibrated certainty score with explanation (no blind hallucinations).
   * **SIMILAR INCIDENTS:** Direct citations of matching historical records.
   * **RECOMMENDED ACTIONS:** Step-by-step mitigation and rollback checklist.
   * **WHY MEMORY HELPED:** Explicit explanation of what institutional memory uncovered that a stateless LLM would have missed.
4. **LEARN (Closing the Loop):** Once the on-call engineer confirms the actual fix, clicking **"Save Resolution to Memory"** commits the verified post-mortem back into Hindsight. Subsequent incidents immediately benefit from this learned resolution.

---

## 🌟 The "Wow" Moment: Proven Learning Loop

* **Incident 1:** Payment API fails with `503 errors and DB connection timeouts after deployment v2.4.0`. The agent recalls past pool saturation issues. The engineer confirms the fix: *"Increased PostgreSQL pool size to 80 and rolled back deployment."* This resolution is retained into Hindsight.
* **Incident 2 (Weeks later, different wording):** *"Customers are experiencing intermittent payment failures. API returns 503 and logs show database timeouts after release 2.4.1."*
* **The Magic:** RecallOps immediately surfaces the **verified resolution** from Incident 1 at the top of the recalled memories and instructs the engineer to apply the exact verified configuration fix in minutes.

---

## 🛠️ Technology Stack

* **Persistent Memory Engine:** [Hindsight](https://hindsight.vectorize.io) (`hindsight-client` Python SDK)
* **Backend:** Python 3.13, Flask REST API
* **Reasoning AI:** Groq Cloud (`qwen/qwen3.8-27b` / Llama-3.3) & OpenAI compatibility
* **Frontend:** Dark-themed responsive developer console (Vanilla HTML5, CSS3, JavaScript)
* **Audit Storage:** Local JSON audit trail (`incidents.json`)
