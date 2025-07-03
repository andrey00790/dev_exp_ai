#!/usr/bin/env python
"""
Проверяет доступ к: Jira, Confluence, GitLab-серверам.
Читает переменные из .env.local (используйте python-dotenv или export).
"""

import os, sys, json, base64, httpx

def ok(msg): print(f"✅ {msg}")
def fail(msg): print(f"❌ {msg}")

# ---------- Jira ----------
def test_jira():
    url = os.getenv("JIRA_URL")
    user = os.getenv("JIRA_USERNAME")
    pwd  = os.getenv("JIRA_PASSWORD")
    if not (url and user and pwd):
        fail("Jira creds пусты"); return
    auth = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    r = httpx.get(f"{url}/rest/api/2/project", headers={"Authorization": f"Basic {auth}"}, timeout=10)
    ok("Jira OK") if r.status_code == 200 else fail(f"Jira {r.status_code}")

# ---------- Confluence ----------
def test_conf():
    url = os.getenv("CONFLUENCE_URL")
    user = os.getenv("CONFLUENCE_USERNAME")
    tok  = os.getenv("CONFLUENCE_API_TOKEN") or os.getenv("CONFLUENCE_PASSWORD")
    if not (url and user and tok):
        fail("Confluence creds пусты"); return
    auth = base64.b64encode(f"{user}:{tok}".encode()).decode()
    r = httpx.get(f"{url}/rest/api/content?limit=1", headers={"Authorization": f"Basic {auth}"}, timeout=10)
    ok("Confluence OK") if r.status_code == 200 else fail(f"Confluence {r.status_code}")

# ---------- GitLab (динамический список) ----------
def test_gitlabs():
    # ищем переменные GITLAB_N_ALIAS / URL / TOKEN
    for k,v in os.environ.items():
        if k.startswith("GITLAB_") and k.endswith("_ALIAS"):
            suf   = k.split("_")[1]
            alias = v
            url   = os.getenv(f"GITLAB_{suf}_URL")
            tok   = os.getenv(f"GITLAB_{suf}_TOKEN")
            if not (url and tok):
                fail(f"GitLab {alias}: creds не заданы"); continue
            r = httpx.get(f"{url}/api/v4/projects?per_page=1",
                          headers={"PRIVATE-TOKEN": tok}, timeout=10)
            ok(f"GitLab {alias} OK") if r.status_code == 200 else fail(f"GitLab {alias} {r.status_code}")

if __name__ == "__main__":
    test_jira()
    test_conf()
    test_gitlabs()