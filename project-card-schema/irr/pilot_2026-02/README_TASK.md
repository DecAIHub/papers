# Task: independent coding of 50 project cards

*English rendering of the protocol handed to the coder in February 2026 (the coder worked from the Russian original).*

## Context

You are an **independent coder** in a pilot inter-rater reliability (IRR) study. Your task is to **code 50 cards** of AI-crypto projects **on your own**, following the protocol below. Your results will be compared with those of the principal coder in order to assess how objective the protocol is.

**Important:** you work **fully independently**. Do not look at anyone else's coding and do not discuss borderline cases with the principal coder before you have finished.

---

## What you receive

1. **This document** — instructions and the coding protocol
2. **The folder `cards/`** — 50 files with the raw project data (descriptions, links)
3. **The file `coding_sheet.csv`** — an empty table to fill in

---

## What you return

The completed `coding_sheet.csv` (or .xlsx, whichever is more convenient).

---

## Coding protocol

### Part 1. Classifying artifacts by tier (Tier-1 / Tier-2 / Tier-3)

Every card lists links (artifacts). For **each artifact** determine its tier:

| Tier | Name | Definition | Examples |
|---|---|---|---|
| **Tier-1** | Evidence | Official documentation, source code/releases, on-chain facts (addresses, transactions), public audits, post-mortems, bug bounties | Project whitepaper, GitHub repository, contract page on Etherscan/Solscan, audit report, official documentation (docs), roadmap on the official site |
| **Tier-2** | Context | Aggregator data (CoinMarketCap, CoinGecko), catalogues, interviews/AMAs, analytics dashboards | Project page on CoinGecko, founder interview, DeFi Llama dashboard |
| **Tier-3** | Noise | Influencer content, promotional reviews, reposts without primary sources | X/Twitter threads, YouTube reviews, paid content |

**Rule:** if the link leads to the **project's own site/documentation, its GitHub, a blockchain explorer, or an independent audit** — Tier-1. If to an **aggregator** (CoinGecko, CMC, DeFi Llama) — Tier-2. If to **social media, influencers, advertising** — Tier-3.

#### Determining the tier from the URL

| URL pattern | Tier | Note |
|---|---|---|
| `docs.*`, `*.gitbook.io`, project documentation | Tier-1 | Official documentation |
| `github.com/...` | Tier-1 | Source code |
| `etherscan.io`, `solscan.io`, `basescan.org`, any blockchain explorer | Tier-1 | On-chain fact |
| Whitepaper (PDF or page) | Tier-1 | Technical specification |
| `*.medium.com` (project blog) | Tier-1 | Official blog = documentation |
| Audit report (Certik, Trail of Bits, etc.) | Tier-1 | Independent audit |
| Roadmap on the official site | Tier-1 | Official plan |
| Main project site (landing) | Tier-1 | Primary source |
| App / Demo | Tier-1 | Working product |
| `coingecko.com/...` | Tier-2 | Aggregator |
| `coinmarketcap.com/...` | Tier-2 | Aggregator |
| `defillama.com/...` | Tier-2 | Analytics dashboard |
| `x.com`, `twitter.com` | Tier-1 if the **project's official account**, otherwise Tier-3 |
| `discord.gg`, `t.me` | Tier-1 (official channel) |
| YouTube reviews / influencers | Tier-3 | Secondary content |

**If unsure:** use your best judgement and record the doubt in the `notes` column.

---

### Part 2. Coding the CCI flags (Claim Intensity Index)

For each project, determine the value of 13 binary flags (0 or 1). The flags form three blocks.

#### Block AI (d_AI): how real the AI is

**Main rule: a flag = 1 ONLY if it is confirmed by a Tier-1 or Tier-2 source. When in doubt, put 0.**

**Critically important (the most frequent systematic error):**

- **AI_0 ≠ "the word AI appears in the name/marketing".**
  **AI_0 = 1** only if AI intentions/plans are **explicitly recorded** in a **Tier-1/2** artifact (docs/whitepaper/roadmap/official repository/official blog).
  If AI is mentioned only in a meme context/ticker/name — **AI_0 = 0**.
- **AI_4 = 1** only if there are **technical details** about the model/architecture/versions/datasets/pipeline.
  An "architecture/technology" section about the product **without a description of the AI model** does not make AI_4 = 1.

| Flag | Question you answer | 1 = yes, if... | 0 = no, if... |
|---|---|---|---|
| **AI_0** | Does the project declare AI intentions? | Documentation/roadmap/whitepaper explicitly mentions AI, ML, neural networks, agents, etc. as part of plans or current work | No AI mentions in official sources |
| **AI_1** | Is it described what the AI concretely does? | A specific function is described: "our AI analyses X", "the model does Y", "the agent performs Z" — detailed enough to see that it is not mere marketing | Only generic phrases such as "AI-powered platform", "leveraging AI", without specifics |
| **AI_2** | Is there a working demo / live product with AI? | The result of the AI can be seen: demo, app, API, dashboard, screenshots with results | Only promises, roadmap, "coming soon" |
| **AI_3** | Are there quantitative AI metrics/benchmarks? | Numbers are given: accuracy, latency, throughput, comparison with a baseline, test results | No figures, only qualitative descriptions |
| **AI_4** | Is the model architecture / versioning described? | A technical description exists: which model (GPT, BERT...), architecture, versions, datasets, pipeline | No technical details about the AI "internals" |

#### Block OC (d_OC): how real the on-chain part is

| Flag | Question | 1 = yes | 0 = no |
|---|---|---|---|
| **OC_1** | Are there verifiable smart contracts/addresses? | The contract can be found on a blockchain explorer; the address is given in the documentation | No addresses, no contracts, or the links do not work |
| **OC_2** | Is there on-chain logic beyond token transfers? | The smart contract performs useful functions: access, accounting, DAO voting, staking logic, escrow, etc. | Only ordinary ERC-20/SPL token transfers |
| **OC_3** | Is the blockchain critical for the product? | Without the blockchain the product breaks / loses a key property. "Replacement test": if the blockchain were replaced by an ordinary database, would something essential disappear? | The blockchain was added "for the token"; the product would work without it |

#### Block TK (d_TK): the role of the token

| Flag | Question | 1 = yes | 0 = no |
|---|---|---|---|
| **TK_0** | Is there NO token? | The project has no token at all | The project has a token (then TK_0 = 0) |
| **TK_1** | Is the token used to pay for the service? | The token pays for API calls, compute, access, gas | The token is not used as a means of payment |
| **TK_2** | Is the token used for incentives? | Staking, rewards, penalties, mining through the token | No incentive mechanisms |
| **TK_3** | Is the token used for governance? | Voting, governance proposals through the token | No governance through the token |
| **TK_4** | Is the token replaceable? | The project would work the same if the token were replaced by USDC or a subscription. The token carries no unique function | The token is critical to the mechanics (gas of its own network, validator staking, etc.) |

---

### Part 3. Coding procedure (for each card)

1. **Open the card file** from the `cards/` folder
2. **Read the project description** — understand what the project does
3. **Go through the links** — open each link and determine its tier:
   - Record the tier of each artifact in `coding_sheet.csv`
4. **Code the 13 flags**:
   - For each flag ask yourself the question from the table above
   - Answer 0 or 1
   - **If 1** — record in the `evidence_for_flags` column the URL of the source on which you based the 1
   - **If in doubt** — put 0 (conservative rule)
5. **Write notes** — if something was ambiguous, describe it in the `notes` column

**Expected time:** ~5–10 minutes per card. Total: 4–8 hours.

---

### Part 4. Format of `coding_sheet.csv`

Columns:

```
project_id, project_name,
artifact_1_url, artifact_1_tier,
artifact_2_url, artifact_2_tier,
artifact_3_url, artifact_3_tier,
artifact_4_url, artifact_4_tier,
artifact_5_url, artifact_5_tier,
artifact_6_url, artifact_6_tier,
artifact_7_url, artifact_7_tier,
artifact_8_url, artifact_8_tier,
AI_0, AI_1, AI_2, AI_3, AI_4,
OC_1, OC_2, OC_3,
TK_0, TK_1, TK_2, TK_3, TK_4,
evidence_for_flags, notes
```

- `artifact_N_tier` — value `1`, `2` or `3` (tier number)
- all flags — value `0` or `1`
- `evidence_for_flags` — list, separated by `;`, the URLs that justified your `= 1` decisions
- `notes` — free text, if there were doubts

---

### Part 5. Example

Suppose the project "ExampleAI":
- Links: docs.example.ai (Tier-1), github.com/example (Tier-1), coingecko.com/example (Tier-2)
- The documentation says: "our platform uses AI to analyse DeFi protocols" (AI_0 = 1, AI_1 = 1)
- There is a working dashboard (AI_2 = 1) but no metrics (AI_3 = 0) and no technical description of the model (AI_4 = 0)
- Contract on Etherscan (OC_1 = 1), token transfers only (OC_2 = 0), blockchain not critical (OC_3 = 0)
- There is a token (TK_0 = 0), it pays for the API (TK_1 = 1), staking (TK_2 = 1), no governance (TK_3 = 0), the token is replaceable by USDC (TK_4 = 1)

```csv
example_ai, ExampleAI,
https://docs.example.ai, 1,
https://github.com/example, 1,
https://coingecko.com/example, 2,
,,,,,,,,,,
1, 1, 1, 0, 0,
1, 0, 0,
0, 1, 1, 0, 1,
"docs.example.ai; github.com/example; etherscan.io/...",
"AI_1 — the description is generic but specific enough for 1"
```

---

## FAQ

**Q: A link does not open / the site is unavailable.**
A: Write `dead_link` as the tier of that artifact and mention it in `notes`.

**Q: The project is described in a foreign language I do not know.**
A: Use Google Translate. If the translation is unclear, mention it in `notes`.

**Q: I cannot decide whether AI_1 = 0 or 1 — the description is borderline.**
A: Put 0 by default. In `notes` write "AI_1 borderline: [reason]".

**Q: The project has more than 8 artifacts.**
A: Code the first 8. If the remaining ones are critically important, add rows or describe them in `notes`.

**Q: The project has fewer than 8 artifacts.**
A: Leave the extra cells empty.

---

## Contact

For technical questions (not about coding!) — [contact]. Questions such as "is this project Tier-1 or Tier-2?" **may not** be asked before the work is finished — that is the point of the study.
