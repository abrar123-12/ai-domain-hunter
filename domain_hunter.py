import json
import re


# Load our domain rules
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


def clean_name(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def score_domain(domain):
    name = domain.split(".")[0].lower()
    score = 0

    # Brandability
    if 5 <= len(name) <= 10:
        score += 25
    elif len(name) <= 15:
        score += 18
    elif len(name) <= 20:
        score += 10

    # Market relevance
    relevance = sum(1 for word in AI_WORDS if word in name)

    if relevance >= 2:
        score += 25
    elif relevance == 1:
        score += 18
    else:
        score += 5

    # Memorability
    if len(name) <= 10:
        score += 15
    elif len(name) <= 15:
        score += 10
    else:
        score += 5

    # Commercial potential
    commercial_words = [
        "ai", "agent", "automation",
        "flow", "cloud", "labs",
        "logic", "stack", "forge"
    ]

    if any(word in name for word in commercial_words):
        score += 20
    else:
        score += 8

    # TLD quality
    tld = "." + domain.split(".")[-1]

    score += {
        ".com": 10,
        ".ai": 9,
        ".io": 8,
        ".dev": 7
    }.get(tld, 0)

    # Shortness
    if len(name) <= 8:
        score += 5
    elif len(name) <= 12:
        score += 3

    # Penalties
    if "-" in domain:
        score -= 15

    if any(char.isdigit() for char in name):
        score -= 15

    return max(0, min(score, 100))


def generate_candidates():

    candidates = set()

    # AI word combinations
    for word in AI_WORDS:
        for suffix in SUFFIXES:
            candidates.add(clean_name(word + suffix))

    # Prefix + AI word
    for prefix in PREFIXES:
        for word in AI_WORDS:
            candidates.add(clean_name(prefix + word))

    # Prefix + suffix
    for prefix in PREFIXES:
        for suffix in SUFFIXES:
            candidates.add(clean_name(prefix + suffix))

    return candidates


def main():

    candidates = generate_candidates()

    results = []

    for name in candidates:

        for tld in [".com", ".ai", ".io", ".dev"]:

            domain = name + tld
            score = score_domain(domain)

            results.append({
                "domain": domain,
                "score": score
            })

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    print("\n🔥 TOP DOMAIN CANDIDATES\n")

    for item in results[:30]:
        print(
            f"{item['domain']:30} "
            f"Score: {item['score']}/100"
        )


if __name__ == "__main__":
    main()
