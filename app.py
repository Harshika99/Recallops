import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from hindsight_client import Hindsight
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
DATA_FILE = "incidents.json"

def get_hindsight_config():
    """Retrieve Hindsight configuration from environment."""
    return {
        "api_key": os.getenv("HINDSIGHT_API_KEY", "").strip(),
        "url": os.getenv("HINDSIGHT_URL", "https://api.hindsight.vectorize.io").strip(),
        "bank_id": os.getenv("HINDSIGHT_BANK_ID", "recallops-demo").strip()
    }

def get_hindsight_client():
    """Instantiate official Hindsight client if API key is configured."""
    cfg = get_hindsight_config()
    if not cfg["api_key"]:
        return None
    return Hindsight(base_url=cfg["url"], api_key=cfg["api_key"])

def get_llm_client():
    """Instantiate OpenAI-compatible LLM client (preferring Groq)."""
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    if groq_key:
        model = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b").strip()
        client = OpenAI(
            api_key=groq_key,
            base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip()
        )
        return client, "Groq", model

    if openai_key:
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        base_url = os.getenv("OPENAI_BASE_URL")
        client = OpenAI(api_key=openai_key, base_url=base_url) if base_url else OpenAI(api_key=openai_key)
        return client, "OpenAI", model

    return None, None, None

def load_incidents():
    """Load local incident records for display and audit log."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_incident(item):
    """Save an incident record locally."""
    items = load_incidents()
    items.insert(0, item)
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(items[:100], f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save incident locally: {e}")

# =========================================================================
# 1. RETAIN — Seed Organizational Incident Memory
# =========================================================================
def seed_memories():
    """
    Seed realistic historical production incidents into Hindsight persistent memory.
    Covers Payment API, Database pool exhaustion, Redis saturation, Auth 502,
    API Gateway timeouts, and configuration rollouts.
    """
    hs = get_hindsight_client()
    cfg = get_hindsight_config()
    if not hs:
        return False, "Hindsight connection failed: Missing HINDSIGHT_API_KEY in .env. Please configure your API key to seed memory."

    bank_id = cfg["bank_id"]
    try:
        # Ensure organizational bank exists
        try:
            hs.create_bank(
                bank_id=bank_id,
                name="RecallOps Incident Memory",
                mission="Persistent operational incident memory for production diagnostics, triage, and verified resolutions."
            )
        except Exception:
            # Bank already exists or managed by Hindsight Cloud
            pass

        historical_incidents = [
            {
                "id": "INC-001",
                "service": "Payment API",
                "content": """Incident INC-001: Payment API returned HTTP 503 errors and database timeout messages after deployment v2.4.0.
Symptom: High error rate on /v1/charges, database connection timeout errors in application worker logs.
Root cause: Database connection pool exhaustion caused by default pool_size=10 in the updated configuration file.
Resolution: Increased PostgreSQL connection pool size to 80 and rolled back deployment v2.4.0 to v2.3.9.
Operational Lesson: For payment 503 errors after deployment, check DB connection pool metrics, pool saturation, and recent config diffs before checking downstream payment gateways.""",
                "tags": ["payment-api", "database", "connection-pool", "deployment", "503-error"]
            },
            {
                "id": "INC-002",
                "service": "Payment API",
                "content": """Incident INC-002: Intermittent payment transaction dropouts and HTTP 500/503 responses under peak load.
Symptom: API logs showed 'pool-exhausted: unable to acquire connection within 30000ms' during traffic surge.
Root cause: Unbounded transaction holds in checkout payment flow coupled with undersized HikariCP database pool (size=20).
Resolution: Increased DB connection pool max_connections to 100, tuned acquire timeout to 3000ms, and restarted payment workers.
Operational Lesson: Similar payment 503 and database timeout patterns consistently indicate connection pool saturation and require pool capacity expansion.""",
                "tags": ["payment-api", "database", "hikari-pool", "timeout", "503-error"]
            },
            {
                "id": "INC-003",
                "service": "Checkout Service",
                "content": """Incident INC-003: Checkout requests timed out intermittently with HTTP 504 Gateway Timeout during flash sale traffic spike.
Symptom: Queue latency increased to 4500ms; Redis cluster CPU pegged at 98%; connection pool maxed out at 500 connections.
Root cause: Redis connection pool saturation and cache key hotspot on session validation during flash sale.
Resolution: Increased Redis connection limits, scaled Redis read replicas, and restarted affected checkout worker pods.
Operational Lesson: Checkout timeout incidents during traffic spikes should immediately verify Redis connection usage, cluster CPU, and worker saturation.""",
                "tags": ["checkout", "redis", "connection-pool", "timeout", "flash-sale"]
            },
            {
                "id": "INC-004",
                "service": "Auth Service",
                "content": """Incident INC-004: Authentication service failed with repeated HTTP 502 Bad Gateway errors immediately following release v3.1.2.
Symptom: Ingress proxy failed health checks to auth upstream; container pods crashing in CrashLoopBackOff.
Root cause: Missing JWT_SIGNING_KEY secret in deployment manifest causing worker process crashes upon boot.
Resolution: Injected missing environment secret in deployment YAML and executed a rolling pod restart.
Operational Lesson: 502 errors immediately following deployment indicate container startup crashes or missing environment configuration.""",
                "tags": ["auth-service", "deployment", "502-error", "secrets", "crashloop"]
            },
            {
                "id": "INC-005",
                "service": "Order Service",
                "content": """Incident INC-005: Order creation endpoint /orders/create degraded to 12s p99 latency with database CPU locked at 100%.
Symptom: Severe Postgres lock contention and sequential table scans on the orders table.
Root cause: Missing composite index on (customer_id, created_at) introduced in recent release.
Resolution: Created composite index CONCURRENTLY on orders table and deployed optimized query plan.
Operational Lesson: Slow order creation accompanied by 100% DB CPU is almost always an unindexed query or missing migration index.""",
                "tags": ["order-service", "database", "cpu-spike", "indexing", "slow-query"]
            },
            {
                "id": "INC-006",
                "service": "API Gateway",
                "content": """Incident INC-006: External clients experienced cascading 504 Gateway Timeout errors across all microservices.
Symptom: Envoy proxy thread pool starvation; open connections exceeded 10,000.
Root cause: Misconfigured downstream timeout (60s instead of 5s) on a third-party fraud verification webhook allowed hung connections to starve the gateway pool.
Resolution: Adjusted circuit breaker threshold to 5000ms timeout and enabled fail-open fallback for fraud checks.
Operational Lesson: Gateway 504 cascades indicate downstream webhook starvation; ensure circuit breakers and strict timeouts are active.""",
                "tags": ["api-gateway", "timeout", "504-error", "circuit-breaker", "webhooks"]
            },
            {
                "id": "INC-007",
                "service": "Product Catalog",
                "content": """Incident INC-007: Product catalog latency skyrocketed to 8000ms after Redis cluster eviction warnings.
Symptom: Redis memory reached maxmemory limit; keys evicted aggressively under volatile-lru policy.
Root cause: Cache stampede on product taxonomy cache expiration without jitter or mutex locking.
Resolution: Added randomized TTL jitter (+/- 15%) and implemented single-flight locking for catalog cache rebuilds.
Operational Lesson: Catalog latency spikes with high cache miss rates require TTL jitter and single-flight cache repopulation.""",
                "tags": ["product-catalog", "redis", "cache-stampede", "latency", "eviction"]
            },
            {
                "id": "INC-008",
                "service": "Notification Service",
                "content": """Incident INC-008: Email and SMS dispatch queue backed up with 45,000 unprocessed messages after scheduled maintenance.
Symptom: Celery background workers failing with RabbitMQ AMQPConnectionWorkflowError.
Root cause: TLS cipher suite mismatch between updated worker image and RabbitMQ cluster broker.
Resolution: Updated TLS cipher configuration in worker deployment and rolled back worker base image.
Operational Lesson: Post-maintenance queue backlogs should inspect message broker TLS handshake logs and worker connection configuration.""",
                "tags": ["notification-service", "deployment", "rabbitmq", "tls", "queue-backlog"]
            }
        ]

        # Retain each incident into Hindsight persistent memory
        for inc in historical_incidents:
            hs.retain(
                bank_id=bank_id,
                content=inc["content"],
                context=f"Historical post-mortem for {inc['service']}",
                tags=inc["tags"],
                metadata={
                    "incident_id": inc["id"],
                    "service": inc["service"],
                    "category": "production_postmortem"
                }
            )

        return True, f"Successfully seeded {len(historical_incidents)} historical incidents into Hindsight persistent memory (Bank: {bank_id})."
    except Exception as e:
        return False, f"Hindsight connection failed: {str(e)}"
    finally:
        try:
            hs.close()
        except Exception:
            pass

# =========================================================================
# 2. RECALL — Query Hindsight for Relevant Historical Incidents
# =========================================================================
def recall_memories(service, error):
    """
    Query Hindsight persistent memory to find historical incidents and verified resolutions
    matching the current incident symptoms.
    """
    hs = get_hindsight_client()
    cfg = get_hindsight_config()
    if not hs:
        raise ValueError("Missing HINDSIGHT_API_KEY in .env. Real Hindsight memory recall requires a configured API key.")

    bank_id = cfg["bank_id"]
    query = f"Production incident in {service}. Observed symptoms and logs: {error}. Find past root causes and verified resolutions."

    try:
        # Execute genuine Hindsight recall
        result = hs.recall(
            bank_id=bank_id,
            query=query,
            budget="mid",
            max_tokens=3500
        )

        memories = []
        if hasattr(result, "results") and result.results:
            for idx, r in enumerate(result.results[:5]):
                raw_scores = getattr(r, "scores", None)
                scores_dict = None
                if raw_scores is not None:
                    if hasattr(raw_scores, "model_dump"):
                        scores_dict = raw_scores.model_dump()
                    elif hasattr(raw_scores, "dict"):
                        scores_dict = raw_scores.dict()
                    elif isinstance(raw_scores, dict):
                        scores_dict = raw_scores

                memories.append({
                    "index": idx + 1,
                    "id": getattr(r, "id", None) or f"MEM-{idx+1}",
                    "text": getattr(r, "text", str(r)),
                    "type": getattr(r, "type", "historical_incident"),
                    "context": getattr(r, "context", None),
                    "tags": list(getattr(r, "tags", []) or []),
                    "scores": scores_dict
                })

        return memories
    finally:
        try:
            hs.close()
        except Exception:
            pass

# =========================================================================
# 3. REASON — Synthesize Current Incident with Recalled Memory via LLM
# =========================================================================
def analyze_with_llm(incident, memories):
    """
    Send the current incident alongside genuine recalled Hindsight memories to the LLM.
    Strictly enforce the required 5-part diagnostic response format.
    """
    client, provider, model = get_llm_client()
    if not client:
        raise ValueError("Missing GROQ_API_KEY (or OPENAI_API_KEY) in .env. Configure an API key for AI reasoning.")

    # Format recalled memories into prompt
    if memories:
        memory_blocks = []
        for m in memories:
            tags_str = f" [Tags: {', '.join(m['tags'])}]" if m.get("tags") else ""
            memory_blocks.append(f"• Historical Incident Record #{m['index']}{tags_str}:\n{m['text']}")
        memory_text = "\n\n".join(memory_blocks)
    else:
        memory_text = "No prior incidents found in Hindsight persistent memory for these specific symptoms."

    system_prompt = (
        "You are RecallOps, an elite principal SRE and AI incident-response agent. "
        "You diagnose active production outages by cross-referencing live incident logs with "
        "the organization's Hindsight persistent memory of past incidents and verified resolutions. "
        "Be rigorous, precise, and operationally realistic. Never invent fake incident IDs or claim "
        "100% certainty if evidence is ambiguous."
    )

    user_prompt = f"""Analyze the active production incident using historical precedents retrieved from Hindsight persistent memory.

CURRENT PRODUCTION INCIDENT:
- Service: {incident['service']}
- Environment: {incident['environment']}
- Observed Error / Logs:
{incident['error']}

RELEVANT HISTORICAL MEMORY (Retrieved via Hindsight Persistent Memory):
{memory_text}

OUTPUT INSTRUCTIONS:
You MUST provide your response with EXACTLY the following 5 uppercase section headers:

LIKELY CAUSE:
[State the most probable technical root cause based on current symptoms and historical precedents.]

CONFIDENCE:
[High, Medium, or Low — followed by a concise 1-sentence explanation.]

SIMILAR INCIDENTS:
[Summarize relevant historical incidents recalled from Hindsight and how their symptoms match the current incident.]

RECOMMENDED ACTIONS:
1. [First immediate diagnostic or containment action]
2. [Second verification or remediation action]
3. [Third step, referencing historical resolution if applicable]
4. [Verification step to ensure resolution]

WHY MEMORY HELPED:
[Explicitly explain how Hindsight persistent memory accelerated this diagnosis compared to a stateless LLM, highlighting specific historical patterns or verified resolutions.]"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        max_tokens=850
    )
    return response.choices[0].message.content

# =========================================================================
# 4. LEARN — Retain Verified Resolution into Hindsight Persistent Memory
# =========================================================================
def retain_resolution(incident_id, service, environment, error, root_cause, resolution):
    """
    Save the human-verified incident resolution into Hindsight persistent memory.
    This closes the learning loop so future similar incidents immediately recall this fix.
    """
    hs = get_hindsight_client()
    cfg = get_hindsight_config()
    if not hs:
        return False, "Hindsight connection failed: Missing HINDSIGHT_API_KEY in .env. Please configure your key to save resolutions."

    bank_id = cfg["bank_id"]
    content = f"""Verified Incident Post-Mortem & Resolution ({incident_id}):
Service: {service}
Environment: {environment}
Initial Symptoms / Logs: {error}
Verified Root Cause: {root_cause}
Successful Resolution: {resolution}
Operational Directive: When {service} exhibits {error}, apply this verified resolution: {resolution}."""

    try:
        hs.retain(
            bank_id=bank_id,
            content=content,
            context=f"Verified incident post-mortem resolution for {service}",
            tags=[service.lower().replace(" ", "-"), "verified-resolution", "learned-fix", "incident-resolution"],
            metadata={
                "incident_id": str(incident_id),
                "service": str(service),
                "type": "verified_resolution",
                "learned_at": datetime.now().isoformat()
            }
        )
        return True, "Resolution learned by Hindsight."
    except Exception as e:
        return False, f"Hindsight retain failed: {str(e)}"
    finally:
        try:
            hs.close()
        except Exception:
            pass

# =========================================================================
# Flask Routes
# =========================================================================
@app.route("/")
def index():
    cfg = get_hindsight_config()
    _, provider, model = get_llm_client()
    return render_template(
        "index.html",
        incidents=load_incidents(),
        hindsight_configured=bool(cfg["api_key"]),
        bank_id=cfg["bank_id"],
        hindsight_url=cfg["url"],
        llm_configured=bool(provider),
        llm_provider=provider or "Unconfigured",
        llm_model=model or "None"
    )

@app.route("/api/status", methods=["GET"])
def api_status():
    """Return live system configuration status."""
    cfg = get_hindsight_config()
    _, provider, model = get_llm_client()
    return jsonify({
        "ok": True,
        "hindsight": {
            "configured": bool(cfg["api_key"]),
            "bank_id": cfg["bank_id"],
            "url": cfg["url"]
        },
        "llm": {
            "configured": bool(provider),
            "provider": provider or "None",
            "model": model or "None"
        }
    })

@app.route("/seed", methods=["POST"])
def seed():
    """Seed demo organizational memory into Hindsight."""
    ok, message = seed_memories()
    if not ok:
        return jsonify({"ok": False, "error": message}), 400
    return jsonify({"ok": True, "message": message})

@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Triage incident:
    1. Validate inputs
    2. Genuinely recall relevant memories from Hindsight
    3. Run LLM reasoning
    4. Save incident audit record
    """
    data = request.get_json() or {}
    service = data.get("service", "").strip()
    environment = data.get("environment", "Production").strip()
    error = data.get("error", "").strip()

    if not service or not error:
        return jsonify({"ok": False, "error": "Service name and Error/Logs are required fields."}), 400

    incident = {
        "id": f"INC-{datetime.now().strftime('%m%d%H%M%S')}",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "service": service,
        "environment": environment,
        "error": error
    }

    # Step 1: Hindsight Recall
    try:
        memories = recall_memories(service, error)
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": f"Hindsight connection failed: {str(e)}"
        }), 502

    # Step 2: LLM Reasoning
    try:
        analysis = analyze_with_llm(incident, memories)
    except Exception as e:
        return jsonify({
            "ok": False,
            "memories": memories,
            "error": f"LLM reasoning failed: {str(e)}"
        }), 502

    # Step 3: Record local audit trail
    save_incident({
        **incident,
        "memory_count": len(memories),
        "analysis": analysis
    })

    return jsonify({
        "ok": True,
        "incident": incident,
        "memories": memories,
        "analysis": analysis
    })

@app.route("/resolve", methods=["POST"])
def resolve():
    """Close the learning loop by saving verified root cause and fix to Hindsight."""
    data = request.get_json() or {}
    incident_id = data.get("incident_id", "INC-CURRENT").strip()
    service = data.get("service", "Payment API").strip()
    environment = data.get("environment", "Production").strip()
    error = data.get("error", "").strip()
    root_cause = data.get("root_cause", "").strip()
    resolution = data.get("resolution", "").strip()

    if not root_cause or not resolution:
        return jsonify({"ok": False, "error": "Both Actual Root Cause and Successful Resolution are required."}), 400

    ok, message = retain_resolution(incident_id, service, environment, error, root_cause, resolution)
    if not ok:
        return jsonify({"ok": False, "error": message}), 500

    return jsonify({
        "ok": True,
        "message": message,
        "details": {
            "incident_id": incident_id,
            "root_cause": root_cause,
            "resolution": resolution
        }
    })

@app.route("/api/incidents", methods=["GET"])
def get_incidents():
    return jsonify({"ok": True, "incidents": load_incidents()})

@app.route("/api/incidents/clear", methods=["POST"])
def clear_incidents():
    if os.path.exists(DATA_FILE):
        try:
            os.remove(DATA_FILE)
        except Exception:
            pass
    return jsonify({"ok": True, "message": "Incident history cleared."})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
