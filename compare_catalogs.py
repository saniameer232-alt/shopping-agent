import json

rules = {p["id"]: p for p in json.load(open("data/catalog_rules.json", encoding="utf-8"))}
llm = {p["id"]: p for p in json.load(open("data/catalog.json", encoding="utf-8"))}

keys = ["water", "lightweight", "review_waterproof_contradiction", "review_durability_issue"]
diffs = 0
for i, r in rules.items():
    for k in keys:
        if r[k] != llm[i][k]:
            diffs += 1
            print(f"{r['title']}: {k}: rules={r[k]} | llm={llm[i][k]}")
print("total differences:", diffs)