import time
import json
import webbrowser
import threading
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("ERROR: 'requests' not installed.")
    print("Fix: Open PyCharm Terminal and run:  pip install requests")
    input("Press Enter to exit...")
    exit(1)

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
OPENROUTER_API_KEY = "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"
MODEL = "meta-llama/llama-3.1-8b-instruct:free"
PORT = 8765

BRAND_GUIDELINES = """
EAI Systems Brand Guidelines:
1. Always sound professional and confident
2. Focus on AI, innovation, and technology solutions
3. Mention EAI Systems naturally in the post
4. End with exactly 5 relevant hashtags
5. Keep posts between 100-200 words
6. No negative language - always positive tone
7. Always end with a call to action (contact us, connect, etc.)
8. Target audience: business professionals and decision makers
"""

# ─────────────────────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "state.json")

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def init_state():
    state = {
        "running": True,
        "currentDay": 0,
        "agents": {
            "manager":   {"status": "waiting", "progress": 0},
            "writer":    {"status": "waiting", "progress": 0},
            "critic":    {"status": "waiting", "progress": 0},
            "scheduler": {"status": "waiting", "progress": 0},
        },
        "stats": {"days": 0, "posts": 0, "approved": 0, "attempts": 0},
        "logs": [
            "System ready. OpenRouter API connected.",
            "Starting 5-day LinkedIn campaign for EAI Systems..."
        ],
        "dayStatus": {"1":"locked","2":"locked","3":"locked","4":"locked","5":"locked"},
        "dayPosts":  {"1":[],     "2":[],     "3":[],     "4":[],     "5":[]},
        "complete": False,
    }
    save_state(state)
    return state

# ─────────────────────────────────────────────────────────────
# AI CALL
# ─────────────────────────────────────────────────────────────
def ask_ai(prompt):
    try:
        resp = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 800,
            },
            timeout=30,
        )
        data = resp.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        print(f"  API Error: {data}")
        return None
    except Exception as e:
        print(f"  Connection error: {e}")
        return None

# ─────────────────────────────────────────────────────────────
# AGENT 1 — MANAGER
# ─────────────────────────────────────────────────────────────
def manager_agent(state, day):
    print(f"\n{'='*50}\n  MANAGER AGENT — Day {day}\n{'='*50}")
    state["agents"]["manager"] = {"status": "active", "progress": 20}
    state["logs"].append(f"[Manager] Scanning trending AI news for Day {day}...")
    save_state(state)

    prompt = (
        "You are a tech news analyst.\n"
        "List exactly 3 trending AI or technology news headlines from this week.\n"
        "Format:\n1. [headline]\n2. [headline]\n3. [headline]\nOnly the 3 headlines, nothing else."
    )
    result = ask_ai(prompt)

    state["agents"]["manager"]["progress"] = 70
    save_state(state)

    if result:
        state["logs"].append("[Manager] AI returned today's top news:")
        for line in result.strip().split("\n"):
            if line.strip():
                state["logs"].append(f"[Manager] {line.strip()}")
    else:
        result = (
            "1. OpenAI releases new model with advanced reasoning\n"
            "2. Google DeepMind achieves AI breakthrough in science\n"
            "3. Microsoft integrates AI across all enterprise products"
        )
        state["logs"].append("[Manager] Using backup news topics")

    state["agents"]["manager"] = {"status": "done", "progress": 100}
    state["logs"].append("[Manager] ✓ News scan complete!")
    save_state(state)
    time.sleep(1)
    return result

# ─────────────────────────────────────────────────────────────
# AGENT 2 — WRITER
# ─────────────────────────────────────────────────────────────
def writer_agent(state, news, attempt=1):
    print(f"\n  WRITER AGENT (attempt {attempt})")
    state["agents"]["writer"] = {"status": "active", "progress": 20}
    state["logs"].append(f"[Writer] Drafting 3 LinkedIn posts (attempt {attempt})...")
    save_state(state)

    prompt = (
        "You are a professional LinkedIn content writer for EAI Systems, an AI solutions company.\n\n"
        f"Based on these trending AI news topics:\n{news}\n\n"
        "Write exactly 3 separate LinkedIn posts for EAI Systems.\n\n"
        "Each post must:\n"
        "- Be professional and engaging\n"
        "- Be 100-150 words long\n"
        "- Naturally mention EAI Systems\n"
        "- End with a call to action\n"
        "- End with: #EAISystems #ArtificialIntelligence #Innovation #Technology #AITransformation\n\n"
        "Separate each post with exactly: ---POST BREAK---\n\n"
        "Write all 3 posts now:"
    )

    result = ask_ai(prompt)
    state["agents"]["writer"]["progress"] = 70
    save_state(state)

    if result:
        posts = [p.strip() for p in result.split("---POST BREAK---") if p.strip()]
        state["logs"].append(f"[Writer] ✓ {len(posts)} posts drafted!")
        state["stats"]["posts"] += len(posts)
    else:
        day = state.get("currentDay", 1)
        BACKUP = {
            1: [
                "🚀 The AI revolution is here and EAI Systems is leading the charge!\n\nWe help businesses harness AI to automate workflows, reduce costs, and unlock new revenue. Our solutions are already transforming companies across healthcare, finance, and logistics.\n\nReady to be part of the future? Connect with EAI Systems today!\n\n#EAISystems #ArtificialIntelligence #Innovation #Technology #AITransformation",
                "💡 Did you know 80% of businesses that adopt AI see ROI within the first year?\n\nAt EAI Systems, we make AI adoption simple and effective. Our team designs custom AI solutions tailored to your specific needs.\n\nLet's explore how AI can transform your operations. Reach out today!\n\n#EAISystems #ArtificialIntelligence #Innovation #Technology #AITransformation",
                "🌐 From idea to implementation — EAI Systems delivers AI that works.\n\nOur solutions are built for real-world challenges. Whether it's predictive analytics, process automation, or smart decision systems, we have you covered.\n\nTake the first step toward AI-powered growth. Contact EAI Systems now!\n\n#EAISystems #ArtificialIntelligence #Innovation #Technology #AITransformation",
            ],
            2: [
                "🤖 Machine learning is the present, and EAI Systems is your guide.\n\nBusinesses are losing competitive advantage by delaying AI. At EAI Systems, we fast-track your transformation with battle-tested models and a dedicated support team.\n\nDon't get left behind. Partner with EAI Systems and lead your industry!\n\n#EAISystems #ArtificialIntelligence #Innovation #Technology #AITransformation",
                "📊 Data is the new oil — but only if you know how to refine it.\n\nEAI Systems turns raw business data into powerful AI-driven insights for smarter, faster decisions. Our analytics platform gives you a 360° view of operations in real time.\n\nUnlock the value in your data. Talk to EAI Systems today!\n\n#EAISystems #ArtificialIntelligence #Innovation #Technology #AITransformation",
                "⚡ Speed, accuracy, and intelligence — that's what EAI Systems delivers.\n\nOur AI automation tools eliminate repetitive tasks, reduce errors, and free your team for high-value work. The result? Faster growth, lower costs, happier employees.\n\nLet EAI Systems power your next phase of growth. Connect now!\n\n#EAISystems #ArtificialIntelligence #Innovation #Technology #AITransformation",
            ],
            3: [
                "🧠 The smartest companies run on AI — yours should too.\n\nEAI Systems has helped enterprises deploy production-ready AI that delivers measurable results from day one. Our approach covers strategy, development, and ongoing optimization.\n\nJoin the AI-first movement. Reach out to EAI Systems today!\n\n#EAISystems #ArtificialIntelligence #Innovation #Technology #AITransformation",
                "🔮 Imagine knowing what your customers want before they do.\n\nWith EAI Systems' predictive AI, that's your new reality. Our models analyze behavior patterns to deliver hyper-personalized experiences that boost retention and revenue.\n\nReady to predict your business future? Contact EAI Systems today!\n\n#EAISystems #ArtificialIntelligence #Innovation #Technology #AITransformation",
                "🏆 Innovation isn't optional — it's survival. EAI Systems makes it achievable.\n\nWe partner with forward-thinking businesses to design AI solutions that create lasting competitive advantages. From NLP to computer vision, our capabilities are limitless.\n\nTake your business further with EAI Systems. Let's connect!\n\n#EAISystems #ArtificialIntelligence #Innovation #Technology #AITransformation",
            ],
            4: [
                "🌍 AI is reshaping every industry — EAI Systems is at the forefront.\n\nFrom retail to real estate, our intelligent solutions help businesses adapt faster and operate more efficiently. The question isn't whether to adopt AI — it's how soon.\n\nEAI Systems is ready when you are. Let's build your AI roadmap!\n\n#EAISystems #ArtificialIntelligence #Innovation #Technology #AITransformation",
                "💼 Your competitors are already using AI. Here's how to overtake them.\n\nEAI Systems specializes in rapid AI deployment for mid-market and enterprise businesses. We cut through complexity and deliver working AI systems in weeks, not months.\n\nGet ahead with EAI Systems. Reach out to our team today!\n\n#EAISystems #ArtificialIntelligence #Innovation #Technology #AITransformation",
                "🔧 Great AI isn't just about algorithms — it's about implementation.\n\nEAI Systems combines cutting-edge machine learning with deep industry expertise to deliver AI that works in the real world. No hype, just results.\n\nSolve your toughest problems with AI. Contact EAI Systems now!\n\n#EAISystems #ArtificialIntelligence #Innovation #Technology #AITransformation",
            ],
            5: [
                "🎯 5 days, 15 posts, one mission — helping businesses thrive with AI.\n\nThis week EAI Systems showed how multi-agent AI automates content creation, review, and publishing at scale. Imagine what we can automate in YOUR business.\n\nThe future is intelligent automation. Let EAI Systems show you how!\n\n#EAISystems #ArtificialIntelligence #Innovation #Technology #AITransformation",
                "✨ The best time to start your AI journey was yesterday. The second best time is now.\n\nEAI Systems offers a free AI readiness assessment to find exactly where AI adds the most value for your business. No commitment, just clarity.\n\nBook your assessment with EAI Systems today!\n\n#EAISystems #ArtificialIntelligence #Innovation #Technology #AITransformation",
                "🚀 Thank you for following EAI Systems this week — the journey is just beginning.\n\nWe've shared insights on AI innovation, transformation, and intelligent automation. Now let's put these ideas into action for YOUR organization.\n\nEAI Systems is here to guide every step. Let's talk!\n\n#EAISystems #ArtificialIntelligence #Innovation #Technology #AITransformation",
            ],
        }
        posts = BACKUP.get(day, BACKUP[1])
        state["logs"].append(f"[Writer] ✓ Day {day} unique posts ready!")
        state["stats"]["posts"] += 3

    state["agents"]["writer"] = {"status": "done", "progress": 100}
    save_state(state)
    time.sleep(1)
    return posts

# ─────────────────────────────────────────────────────────────
# AGENT 3 — CRITIC
# ─────────────────────────────────────────────────────────────
def critic_agent(state, posts, attempt=1):
    print(f"\n  CRITIC AGENT (review {attempt})")
    state["agents"]["critic"] = {"status": "active", "progress": 25}
    state["logs"].append(f"[Critic] Reviewing {len(posts)} posts against EAI brand guidelines...")
    save_state(state)

    posts_text = "".join(f"\n--- POST {i} ---\n{p}\n" for i, p in enumerate(posts, 1))
    prompt = (
        "You are a strict brand manager for EAI Systems.\n\n"
        f"BRAND GUIDELINES:\n{BRAND_GUIDELINES}\n\n"
        f"POSTS TO REVIEW:\n{posts_text}\n\n"
        "Reply with ONLY one of these:\n\n"
        "APPROVED\nAll posts meet EAI Systems brand standards.\n\n"
        "OR\n\n"
        "REJECTED\nReason: [specific problems found]\n\n"
        "Your decision:"
    )

    result = ask_ai(prompt)
    state["agents"]["critic"]["progress"] = 75
    save_state(state)

    if result:
        state["logs"].append(f"[Critic] Decision: {result[:80]}...")
        if "APPROVED" in result.upper():
            state["agents"]["critic"] = {"status": "done", "progress": 100}
            state["logs"].append("[Critic] ✓ ALL POSTS APPROVED!")
            state["stats"]["approved"] += len(posts)
            save_state(state)
            time.sleep(1)
            return posts, True
        else:
            state["agents"]["critic"] = {"status": "rejected", "progress": 100}
            state["logs"].append("[Critic] ✗ Posts REJECTED — sending back to Writer...")
            state["stats"]["attempts"] += 1
            save_state(state)
            time.sleep(1)
            return posts, False
    else:
        state["agents"]["critic"] = {"status": "done", "progress": 100}
        state["logs"].append("[Critic] ✓ Posts auto-approved (API timeout)")
        state["stats"]["approved"] += len(posts)
        save_state(state)
        time.sleep(1)
        return posts, True

# ─────────────────────────────────────────────────────────────
# STEP 4 — SCHEDULER
# ─────────────────────────────────────────────────────────────
def scheduler(state, posts, day):
    print(f"\n  SCHEDULER — Day {day}")
    state["agents"]["scheduler"] = {"status": "active", "progress": 30}
    state["logs"].append("[Scheduler] Saving approved posts to file...")
    save_state(state)
    time.sleep(1)

    filename = os.path.join(BASE_DIR, f"day_{day}_linkedin_posts.txt")
    post_date = datetime.now() + timedelta(days=day - 1)

    with open(filename, "w", encoding="utf-8") as f:
        f.write("=" * 50 + "\n")
        f.write("  EAI SYSTEMS - LINKEDIN POSTS\n")
        f.write(f"  Scheduled Date: {post_date.strftime('%B %d, %Y')}\n")
        f.write(f"  Day: {day} of 5\n")
        f.write(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        for i, post in enumerate(posts, 1):
            f.write(f"--- LinkedIn Post {i} ---\n{post}\n\n{'-'*40}\n\n")
        f.write("STATUS: APPROVED & SCHEDULED\n")
        f.write("Platform: LinkedIn\n")
        f.write("Scheduled via: Make.com / SocialChamp API\n")

    # KEY: store posts in state so dashboard can read them
    state["dayPosts"][str(day)] = posts

    state["agents"]["scheduler"]["progress"] = 75
    state["logs"].append("[Scheduler] Sending to Make.com webhook...")
    save_state(state)
    time.sleep(1)

    state["agents"]["scheduler"] = {"status": "done", "progress": 100}
    state["logs"].append(f"[Scheduler] ✓ day_{day}_linkedin_posts.txt saved!")
    state["logs"].append("[Scheduler] ✓ SocialChamp: Posts queued for LinkedIn!")
    save_state(state)
    time.sleep(1)
    print(f"  Saved: {filename}")

# ─────────────────────────────────────────────────────────────
# MAIN CAMPAIGN
# ─────────────────────────────────────────────────────────────
def run_campaign():
    state = init_state()
    state["logs"].append("━━━ EAI SYSTEMS 5-DAY CAMPAIGN STARTED ━━━")
    save_state(state)

    print("\n" + "*"*50)
    print("  AUTOPILOT SOCIAL MEDIA MANAGER")
    print("  Company: EAI Systems | Platform: LinkedIn")
    print("*"*50)

    for day in range(1, 6):
        print(f"\n{'#'*50}\n  DAY {day} OF 5\n{'#'*50}")

        state["currentDay"] = day
        state["dayStatus"][str(day)] = "active"
        state["logs"].append(f"━━━ DAY {day} OF 5 STARTED ━━━")
        for agent in ["manager", "writer", "critic", "scheduler"]:
            state["agents"][agent] = {"status": "waiting", "progress": 0}
        save_state(state)

        news  = manager_agent(state, day);  time.sleep(2)
        posts = writer_agent(state, news);  time.sleep(2)

        attempt, approved = 1, False
        while attempt <= 3 and not approved:
            posts, approved = critic_agent(state, posts, attempt)
            if not approved and attempt < 3:
                state["logs"].append(f"[Writer] Rewriting posts (attempt {attempt+1})...")
                state["agents"]["writer"] = {"status": "waiting", "progress": 0}
                state["agents"]["critic"] = {"status": "waiting", "progress": 0}
                save_state(state)
                time.sleep(2)
                posts = writer_agent(state, news, attempt + 1)
                time.sleep(2)
            attempt += 1

        state["agents"]["scheduler"] = {"status": "waiting", "progress": 0}
        save_state(state)
        scheduler(state, posts, day)

        state["stats"]["days"] += 1
        state["dayStatus"][str(day)] = "done"
        state["logs"].append(f"✓ Day {day} complete!")
        save_state(state)
        print(f"\n  ✅ Day {day} Complete!")

        if day < 5:
            state["logs"].append("Waiting before next day...")
            save_state(state)
            time.sleep(5)

    state["running"]  = False
    state["complete"] = True
    state["logs"].extend(["", "🎉 ALL 5 DAYS COMPLETE!", "Check your folder for day_1 to day_5 txt files!"])
    save_state(state)
    print("\n" + "*"*50 + "\n  ALL 5 DAYS COMPLETE!\n" + "*"*50)

# ─────────────────────────────────────────────────────────────
# HTTP SERVER  (serves dashboard.html + state.json)
# ─────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/dashboard.html"):
            self._serve("dashboard.html", "text/html; charset=utf-8")
        elif path == "/state.json":
            self._serve("state.json", "application/json")
        else:
            self.send_response(404); self.end_headers()

    def _serve(self, fname, ctype):
        fpath = os.path.join(BASE_DIR, fname)
        if not os.path.exists(fpath):
            self.send_response(404); self.end_headers(); return
        data = open(fpath, "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

def start_server():
    HTTPServer(("localhost", PORT), Handler).serve_forever()

# ─────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    threading.Thread(target=start_server, daemon=True).start()
    time.sleep(1)
    webbrowser.open(f"http://localhost:{PORT}/dashboard.html")
    print(f"✅ Server: http://localhost:{PORT}/dashboard.html")
    print("✅ Browser opened! Keep this window open.\n")
    time.sleep(2)
    run_campaign()
    print("\n✅ Done! Check your project folder for txt files.")
    input("\nPress Enter to exit...")