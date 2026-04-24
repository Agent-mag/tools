import json
import os
import sys
import urllib.request
import urllib.error

endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
api_key = os.environ.get("AZURE_OPENAI_API_KEY", "")
deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "")
version_context = os.environ.get("VERSION_CONTEXT", "")

with open("/tmp/raw-changelog.md") as f:
    raw = f.read()

if not endpoint or not api_key or not deployment:
    print("Azure OpenAI not configured, using raw changelog", file=sys.stderr)
    with open("/tmp/polished-changelog.md", "w") as f:
        f.write(raw)
    sys.exit(0)

system_prompt = (
    "You are a release notes writer for Agent Mag (theagentmag.com), "
    "the publication and tooling ecosystem for AI agent builders. Rewrite the grouped commit "
    "messages below into professional, polished release notes.\n\n"
    "Rules:\n"
    "- Keep the markdown section headers (### New Features, ### Bug Fixes, etc.)\n"
    "- Rewrite each bullet into a clean, professional one-liner that describes what changed and why it matters\n"
    "- Remove any commit hashes or technical jargon that end users would not care about\n"
    "- Merge duplicate or closely related items into a single bullet\n"
    "- Keep the stats line at the bottom (commits + contributors)\n"
    "- Be concise but professional — this is for a public GitHub releases page\n"
    "- Do not add sections that have no items\n"
    "- Do not add any preamble or closing remarks — just the changelog content\n"
    "- Output valid markdown only"
)

user_msg = version_context + "\n\nHere are the raw grouped commits:\n\n" + raw

body = json.dumps({
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ],
    "max_tokens": 4000,
    "temperature": 0.3,
}).encode("utf-8")

url = (
    f"{endpoint}/openai/deployments/{deployment}"
    "/chat/completions?api-version=2024-12-01-preview"
)
req = urllib.request.Request(url, data=body, method="POST")
req.add_header("Content-Type", "application/json")
req.add_header("api-key", api_key)

try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
        content = data["choices"][0]["message"]["content"]
        if content.strip():
            with open("/tmp/polished-changelog.md", "w") as f:
                f.write(content)
            print("GPT-4o polishing succeeded")
        else:
            raise ValueError("Empty response")
except Exception as e:
    print(f"GPT-4o failed ({e}), falling back to raw changelog", file=sys.stderr)
    with open("/tmp/polished-changelog.md", "w") as f:
        f.write(raw)
