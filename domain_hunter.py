import json
import os
import re
import urllib.request

with open("domain_rules.json", "r") as f:
    rules = json.load(f)

AI_WORDS = [
    "ai", "agent", "agents", "auto", "automate",
    "automation", "flow", "workflow", "llm",
    "model", "neural", "cortex", "prompt",
    "bot", "bots", "machine", "learn",
    "data", "cloud", "api", "saas",
    "stack", "logic", "forge", "labs",
    "mind", "brain", "tech"
]

PREFIXES = [
    "neo", "smart", "auto", "meta", "nova",
    "next", "hyper", "quant", "deep",
    "syn", "cloud", "agent"
]

SUFFIXES = [
    "ai", "labs", "flow", "forge",
    "logic", "mind", "stack", "works",
    "hub", "core", "base"
]

TLDS = [".com", ".ai", ".io", ".dev"]


def clean_name(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def score_domain(domain):
    name = domain.split(".")[0].lower()
    score = 0

    if 5 <= len(name) <= 10:
        score += 25
    elif len(name) <= 15:
        score += 18
    elif len(name) <= 20:
        score += 10

    relevance = sum(1 for word in AI_WORDS if word in name)

    if relevance >= 2:
        score += 25
    elif relevance == 1:
        score += 18
    else:
        score += 5

    if len(name) <= 10:
        score += 15
    elif len(name) <= 15:
        score += 10
    else:
        score += 5

    commercial_words = [
        "ai", "agent", "automation",
        "flow", "cloud", "labs",
        "logic", "stack", "forge"
    ]

    if any(word in name for word in commercial_words):
        score += 20
    else:
        score += 8

    tld = "." + domain.split(".")[-1]

    score += {
        ".com": 10,
        ".ai": 9,
        ".io": 8,
        ".dev": 7
    }.get(tld, 0)

    if len(name) <= 8:
        score += 5
    elif len(name) <= 12:
        score += 3

    return max(0, min(score, 100))


def generate_candidates():
    candidates = set()

    for word in AI_WORDS:
        for suffix in SUFFIXES:
            candidates.add(clean_name(word + suffix))

    for prefix in PREFIXES:
        for word in AI_WORDS:
            candidates.add(clean_name(prefix + word))

    for prefix in PREFIXES:
        for suffix in SUFFIXES:
            candidates.add(clean_name(prefix + suffix))

    return candidates


def cloudflare_check(domains):
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")

    if not token or not account_id:
        raise RuntimeError("Cloudflare secrets are missing.")

    url = (
        f"https://api.cloudflare.com/client/v4/"
        f"accounts/{account_id}/registrar/domain-check"
    )

    payload = json.dumps({
        "domains": domains
    }).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    candidates = generate_candidates()

    # First score candidates
    scored = []

    for name in candidates:
        for tld in TLDS:
            domain = name + tld
            score = score_domain(domain)

            scored.append({
                "domain": domain,
                "score": score
            })

    # Only check the best candidates with Cloudflare
    scored.sort(key=lambda x: x["score"], reverse=True)
    shortlist = scored[:60]

    domains = [item["domain"] for item in shortlist]

    print("\n🔎 Checking top domains with Cloudflare...\n")

    available = []

    # Cloudflare allows maximum 20 domains per request
    for i in range(0, len(domains), 20):
        batch = domains[i:i + 20]

        response = cloudflare_check(batch)

        if not response.get("success"):
            print("❌ Cloudflare API error")
            print(response)
            continue

        for result in response["result"]["domains"]:

            if result.get("registrable") is True:
                domain = result["name"]
                score = next(
                    item["score"]
                    for item in shortlist
                    if item["domain"] == domain
                )

                pricing = result.get("pricing", {})

                registration_cost = pricing.get(
                    "registration_cost", "N/A"
                )

                tier = result.get("tier", "unknown")

                if tier == "standard":
                    available.append({
                        "domain": domain,
                        "score": score,
                        "price": registration_cost
                    })

    available.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    print("\n🔥 AVAILABLE DOMAIN CANDIDATES\n")

    if not available:
        print("No available domains found.")
        return

    for item in available:
        print(
            f"{item['domain']:30} "
            f"Score: {item['score']}/100  "
            f"Price: ${item['price']}"
        )


if __name__ == "__main__":
    main()
