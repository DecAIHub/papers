"""
Controlled vocabularies of ABPC v1.1.0 and the documented rules that map the
curator's free-text (raw) passport values onto them.

Controlled fields: Category, chain, type, token_type (+ token_mechanisms). Raw values are always retained
(`*_raw` fields); the canonical value is an additional layer produced by the tables below and written out per
value by build_mapping_tables.py. ai_component and use_case are released as free text.
"""
import re

# --------------------------------------------------------------------------- chain
CHAIN_CANON = [
    "Ethereum", "Solana", "Base", "BNB Chain", "Arbitrum", "Polygon", "Avalanche",
    "Sui", "Aptos", "Near", "Cosmos", "TON", "Fantom", "Optimism", "zkSync",
    "Bittensor", "other",
]
CHAIN_SYNONYMS = {
    "BNB Smart Chain": "BNB Chain",
    "BNB Beacon Chain": "BNB Chain",
    "Arbitrum One": "Arbitrum",
    "zkSync Era": "zkSync",
    "NEAR": "Near",
}


def map_chain(raw):
    if raw is None:
        return None
    v = raw.strip()
    v = CHAIN_SYNONYMS.get(v, v)
    return v if v in CHAIN_CANON else "other"


# --------------------------------------------------------------------------- type
TYPE_CANON = ["EVM", "non-EVM", "Appchain", "L1", "L2", "Rollup", "Sidechain"]


def map_type(raw):
    if raw is None:
        return None
    v = raw.replace("\u2011", "-").replace("\u2010", "-").strip()
    return v if v in TYPE_CANON else None


# --------------------------------------------------------------------------- token_type
TOKEN_TYPE_CANON = ["utility", "meme", "community", "none", "unknown"]

# mechanism vocabulary (the parenthesised part of "utility (...)" values)
TOKEN_MECHANISMS = [
    "payments", "fees", "gas", "staking", "governance", "rewards", "incentives",
    "access", "discounts", "burn", "buyback", "slashing", "security", "other",
]
_MECH_RULES = [
    ("governance", r"governance|voting|vote|dao"),
    ("staking", r"stak|locks|bonding|node deposit|deposit|collateral"),
    ("payments", r"payment|currency|transactions|purchases|purchase|pay\b|service|compute fees|in-game|marketplace|queries|work|publishing|ads|endorsements|campaigns|dataset"),
    ("fees", r"\bfee|fees|tax"),
    ("gas", r"\bgas\b|energy for smart contracts|cycles"),
    ("rewards", r"reward|revenue|revshare|profit|yield|emissions|mining|boost"),
    ("incentives", r"incentiv|alignment|programs"),
    ("access", r"access|gating|gated|premium|subscription|tier|membership|api limits|upgrades|customization|benefits"),
    ("discounts", r"discount"),
    ("burn", r"burn"),
    ("buyback", r"buyback|buy-and-burn"),
    ("slashing", r"slash"),
    ("security", r"security|insurance"),
]


def map_token_type(raw):
    """Return (canonical class, mechanisms list or None)."""
    if raw is None:
        return None, None
    v = raw.strip()
    low = v.lower()
    if low == "unknown":
        return "unknown", None
    if low.startswith("none"):
        return "none", None
    if re.match(r"^(meme|community)", low):
        return ("meme" if "meme" in low else "community"), None
    if low.startswith("utility"):
        inner = " ".join(re.findall(r"\((.*?)\)", v)) or v[len("utility"):]
        inner_low = inner.lower()
        mechs = []
        for name, rx in _MECH_RULES:
            if re.search(rx, inner_low) and name not in mechs:
                mechs.append(name)
        if not mechs:
            mechs = ["other"]
        if "meme" in low:
            return "meme", mechs
        return "utility", mechs
    return "utility", ["other"]


# --------------------------------------------------------------------------- English rendering of residual Russian text
# The curator's cards are written in Russian; the exported free-text values are English except for these annotations,
# which are rendered in English at export (representation only; the wording of the cards is unchanged).
ENGLISH_RENDERINGS = {
    # launch_date_raw
    "2021 (верификация контракта на Etherscan: 2021-02-01)": "2021 (contract verified on Etherscan: 2021-02-01)",
    "2025 (документы/roadmap Q3 2025)": "2025 (documents/roadmap Q3 2025)",
    "2024 (точная дата Tier-1 не найдена)": "2024 (exact date not found in Tier-1 sources)",
    "2024-12 (mainnet launch заявлен)": "2024-12 (mainnet launch claimed)",
    "— (не найдено в извлечённых Tier-1)": "— (not found in the extracted Tier-1 sources)",
    "— (не подтверждено Tier-1)": "— (not confirmed by Tier-1 sources)",
    "2025 (контракт токена опубликован в обозревателе)": "2025 (token contract published in the explorer)",
    "2017 (ICO по данным Etherscan)": "2017 (ICO according to Etherscan)",
    "May 20, 13:39 UTC (genesis event; год не указан в источнике)": "May 20, 13:39 UTC (genesis event; year not given in the source)",
    "2021 (запуск протокола/контрактов; по litepaper “launched in 2021”)": "2021 (protocol/contract launch; litepaper: “launched in 2021”)",
    "2021 (основание; по докам)": "2021 (founded; per docs)",
    "2023-11-27 (mainnet launch по roadmap)": "2023-11-27 (mainnet launch per roadmap)",
    "2023-05-29 (mainnet launch по Humans Blockchain странице)": "2023-05-29 (mainnet launch per the Humans Blockchain page)",
    "2024-03-21 (token launch по сайту проекта)": "2024-03-21 (token launch per the project website)",
    "2022-12 (TGE/первые релизы HOOK по расписанию эмиссии)": "2022-12 (TGE/first HOOK releases per the emission schedule)",
    "2024-04-25 (анонс запуска токена на Solana; сам токен уже существует onchain)":
        "2024-04-25 (announcement of the token launch on Solana; the token already exists on-chain)",
    "2025 (roadmap: beta/public версии по кварталам 2025)": "2025 (roadmap: beta/public versions by quarter in 2025)",
    "2022-02-12 (genesis токена по tokenomics)": "2022-02-12 (token genesis per tokenomics)",
    "2022-03-10 (TGE по tokenomics)": "2022-03-10 (TGE per tokenomics)",
    "2025-08-08 (дата “submitted for verification” контракта токена)": "2025-08-08 (date the token contract was “submitted for verification”)",
    "2017-10-02 (регистрация Measurable Foundation в whitepaper)": "2017-10-02 (registration of the Measurable Foundation per whitepaper)",
    "2024 (whitepaper датирован 2024-03-20)": "2024 (whitepaper dated 2024-03-20)",
    "2022-12 (по сайту, “Date of birth”)": "2022-12 (per website, “Date of birth”)",
    "2022-06-19 (старт эпохи Octa — по whitepaper timeline)": "2022-06-19 (start of the Octa epoch per the whitepaper timeline)",
    "2024 (в доках: “Since launching in early 2024…”)": "2024 (docs: “Since launching in early 2024…”)",
    "2022 (в доках: “launched in late 2022”)": "2022 (docs: “launched in late 2022”)",
    "2024-06 (TGE: June 2024 — по whitepaper NRN Agents)": "2024-06 (TGE: June 2024, per the NRN Agents whitepaper)",
    "2025-10-20 (деплой токена 42 на BSC)": "2025-10-20 (deployment of the 42 token on BSC)",
    "2025-10 (публичный запуск токена VULT описан в документации)": "2025-10 (public launch of the VULT token described in the documentation)",
    "2021-06-10 (запуск LIME ERC-20; по docs)": "2021-06-10 (LIME ERC-20 launch; per docs)",
    "2025-12-18 (TGE date, по whitepaper)": "2025-12-18 (TGE date, per whitepaper)",
    "2021-10-22 (первый mint на SuperRare; по docs)": "2021-10-22 (first mint on SuperRare; per docs)",
    "2024-08-13 (fair launch; по tokenomics)": "2024-08-13 (fair launch; per tokenomics)",
    "2018 (компания, по whitepaper); 2020–2021 (IVFAO/продажи в whitepaper/на сайте)":
        "2018 (company, per whitepaper); 2020–2021 (IVFAO/sales per whitepaper/website)",
    "2022-12 (маркетплейс “publicly opened”, по roadmap на сайте)": "2022-12 (marketplace “publicly opened”, per the roadmap on the website)",
    "2019-11 (public launch; по token economics post)": "2019-11 (public launch; per the token economics post)",
    "2024 (по публичным агрегаторам; Tier-1 подтверждения даты не найдено)": "2024 (per public aggregators; no Tier-1 confirmation of the date found)",
    "2019 (по docs); TGE — Q1 2024 (по roadmap)": "2019 (per docs); TGE — Q1 2024 (per roadmap)",
    "2024-10-16 (заявлено как launch via pump.fun в Medium статье)": "2024-10-16 (claimed as launch via pump.fun in a Medium article)",
    "unknown (приложение доступно в App Store/Google Play; docs описывают public beta)":
        "unknown (app available on App Store/Google Play; docs describe a public beta)",
    "unknown (в извлечённых Tier-1 страницах нет даты genesis/mainnet; docs обновлялись в 2024–2026)":
        "unknown (no genesis/mainnet date in the extracted Tier-1 pages; docs updated 2024–2026)",
    "unknown (в извлечённых Tier-1 источниках нет точной даты запуска mainnet)":
        "unknown (no exact mainnet launch date in the extracted Tier-1 sources)",
    "2024-05-01 (Git tag `v0.1.0-alpha` в changelog; на roadmap-странице встречается 2025 — конфликт)":
        "2024-05-01 (Git tag `v0.1.0-alpha` in the changelog; the roadmap page mentions 2025 — conflict)",
    "2022 (whitepaper; план релизов 2022–2023)": "2022 (whitepaper; release plan 2022–2023)",
    "2018 (верификация контракта на Etherscan: 2018-03-23)": "2018 (contract verified on Etherscan: 2018-03-23)",
    "2022 (MVP stage); в whitepaper: launch on peaq 2024-09-12 (миграция активности onchain)":
        "2022 (MVP stage); whitepaper: launch on peaq 2024-09-12 (migration of activity on-chain)",
    "2025 (в docs примерные “epochs” Q3 2025; точная дата запуска протокола не подтверждена)":
        "2025 (docs give approximate “epochs” for Q3 2025; exact protocol launch date not confirmed)",
    "2024 (launch Q1 2024 в litepaper)": "2024 (launch Q1 2024 per litepaper)",
    "2025-06-06 (TGE в Investor Docs)": "2025-06-06 (TGE per Investor Docs)",
    "2024 (копирайт на сайте)": "2024 (copyright notice on the website)",
    "2017 (по сайту “Since 2017…”)": "2017 (website: “Since 2017…”)",
    "2024–2025 (roadmap описывает этапы 2023–2025)": "2024–2025 (roadmap describes stages 2023–2025)",
    "2021 (node mainnet, по сайту)": "2021 (node mainnet, per website)",
    "2024–2025 (точная дата не подтверждена Tier-1)": "2024–2025 (exact date not confirmed by Tier-1 sources)",
    "2025-08-18 (TGE по докам)": "2025-08-18 (TGE per docs)",
    "— (не найдено для KEY/SFI в извлечённых Tier-1)": "— (not found for KEY/SFI in the extracted Tier-1 sources)",
    "— (не установлено по Tier-1)": "— (not established from Tier-1 sources)",
    "2023-12-10 (дата whitepaper)": "2023-12-10 (whitepaper date)",
    "2024 (roadmap: запуск в Q1 2024)": "2024 (roadmap: launch in Q1 2024)",
    "2025-03-05 (mainnet; заявлено)": "2025-03-05 (mainnet; claimed)",
    "2024-10-31 (fair launch, по docs)": "2024-10-31 (fair launch, per docs)",
    "2024-09-18 (заявлено)": "2024-09-18 (claimed)",
    "2024 (по CMC: ATH Dec 2024)": "2024 (per CMC: ATH Dec 2024)",
    "2025-03-07 (дата litepaper; запуск токена — не установлен)": "2025-03-07 (litepaper date; token launch not established)",
    "2025-01-15 (listing, по docs)": "2025-01-15 (listing, per docs)",
    "2018-08-30 (деплой ERC-20 контракта HAVY; по Etherscan tx создания)": "2018-08-30 (deployment of the HAVY ERC-20 contract; per the Etherscan creation tx)",
    "2018-07-28 (деплой ERC-20 контракта FOAM в Ethereum; по Etherscan tx создания)":
        "2018-07-28 (deployment of the FOAM ERC-20 contract on Ethereum; per the Etherscan creation tx)",
    # ai_component / use_case / token_type_raw
    "AI-сервис (заявлено)": "AI service (claimed)",
    "discovery агентов и комьюнити вокруг токена": "agent discovery and community around the token",
    "каталог и создание “AI agents”": "catalogue and creation of “AI agents”",
    "utility (не подтверждено) / meme": "utility (not confirmed) / meme",
    # ticker / token_contract
    "PUBLIC (docs) / TSR (whitepaper; конфликт)": "PUBLIC (docs) / TSR (whitepaper; conflict)",
    "AIBGPT (по CoinMarketCap; Tier-2)": "AIBGPT (per CoinMarketCap; Tier-2)",
    "VOLS (также заявлен VOLSAI)": "VOLS (VOLSAI also claimed)",
    "KEY → SFI (миграция)": "KEY → SFI (migration)",
    "— (не найдено в доступных Tier-1)": "— (not found in the available Tier-1 sources)",
    "— (ERC-20 представление см. в links_*/Evidence)": "— (see links_*/Evidence for the ERC-20 representation)",
    "0x814e0908b12a99fecf5bc101bb5d0b8b5cdf7d26 (Ethereum; “Main Chain” на token page)":
        "0x814e0908b12a99fecf5bc101bb5d0b8b5cdf7d26 (Ethereum; “Main Chain” on the token page)",
    "native: —; ERC-20 (обёртка/представление): 0x75858677e27C930FB622759FeafFeE2b754Af07F (Etherscan)":
        "native: —; ERC-20 (wrapper/representation): 0x75858677e27C930FB622759FeafFeE2b754Af07F (Etherscan)",
    "— (нативная монета сети Cortex)": "— (native coin of the Cortex network)",
    "0xa61a3b3a130a9c20768eebf97e21515a6046a1fa (ERC-20, по GitHub); tWKHzXd5PRmxTF5cMfJkm2Ua3TcjwNNoSRUqx6Apump (SPL, по links_*)":
        "0xa61a3b3a130a9c20768eebf97e21515a6046a1fa (ERC-20, per GitHub); tWKHzXd5PRmxTF5cMfJkm2Ua3TcjwNNoSRUqx6Apump (SPL, per links_*)",
    "0x1F735f84b07cc20E9aC471C291a87b5A2428d518 (по сайту как ERC20/BEP20)": "0x1F735f84b07cc20E9aC471C291a87b5A2428d518 (per website, as ERC20/BEP20)",
    # link types
    "DEX Screener (пул, справочно)": "DEX Screener (pool, reference)",
    "YouTube (demo, заявлено в коде контракта)": "YouTube (demo, claimed in the contract code)",
}
_CYRILLIC = re.compile("[\u0400-\u04FF]")


def render_english(value, strip_backticks=False):
    """Normalise the template's typographic hyphens (U+2011, U+2010) and render residual Russian annotations in English.
    Fails on an unlisted Russian value so that no untranslated text reaches the deposit."""
    if not isinstance(value, str):
        return value
    s = value.replace("\u2011", "-").replace("\u2010", "-")
    if strip_backticks:
        s = s.replace("`", "")
    if _CYRILLIC.search(s):
        if s not in ENGLISH_RENDERINGS:
            raise ValueError(f"no English rendering for exported value: {s!r}")
        s = ENGLISH_RENDERINGS[s]
    return s


# --------------------------------------------------------------------------- ai_component / use_case
# Released as the curator's free-text descriptors. Only a verification status is derived for ai_component,
# from explicit markers in the descriptor.
AI_COMPONENT_STATUS = ["identified", "positioning_only", "none", "unknown"]


def ai_component_status(raw):
    if raw is None:
        return None
    low = raw.lower()
    if re.search(r"^none\b|not an ai model|not ai models|ai component not detected|^not applicable", low):
        return "none"
    if re.search(r"positioning only|\(positioning\)", low):
        return "positioning_only"
    if re.search(r"^unknown\b|details unknown", low):
        return "unknown"
    return "identified"


def use_case_is_unknown(raw):
    """Descriptor states that no use case was established (used in the missingness table only)."""
    if raw is None:
        return False
    return bool(re.search(r"^unknown\b|not established|^ai service \(claimed\)|positioning only|details unknown", raw.lower()))


# --------------------------------------------------------------------------- Category
CATEGORY_CANON = [
    "Infra", "AI/Other", "AI/Agents", "DeFi", "Meme", "AI/Compute", "Consumer",
    "AI/Data", "Gaming", "AI/Inference", "AI/Analytics", "AI/Training", "DePIN",
    "Metaverse", "Social", "NFT", "DAO", "Privacy", "Stablecoin", "Bridge", "Oracle",
    "Other",
]
# explicit mapping of every observed non-canonical label (multi-target allowed)
CATEGORY_MAP = {
    "AI/Assistants": ["AI/Agents"],
    "SocialFi": ["Social"],
    "AdTech": ["Other"],
    "AI/Tools": ["AI/Other"],
    "Data": ["AI/Data"],
    "Security": ["Infra"],
    "L1": ["Infra"],
    "AI": ["AI/Other"],
    "Marketplace": ["Other"],
    "GameFi": ["Gaming"],
    "DePIN/Compute": ["DePIN", "AI/Compute"],
    "Analytics": ["AI/Analytics"],
    "RWA": ["DeFi"],
    "AI/Robotics": ["AI/Other"],
    "Trading": ["DeFi"],
    "PayFi": ["DeFi"],
    "AI/Knowledge": ["AI/Other"],
    "Identity": ["Infra"],
    "InfoFi": ["Social"],
    "Payments": ["DeFi"],
    "Launchpad": ["DeFi"],
    "AI/Security": ["AI/Other"],
    "AI/Privacy": ["Privacy"],
    "AI/Infra": ["Infra"],
    "Web3": ["Other"],
    "Derivatives": ["DeFi"],
    "AI/NFT": ["NFT"],
    "Education": ["Consumer"],
    "Onboarding": ["Consumer"],
    "AI/Anti-Fraud": ["AI/Other"],
    "Media": ["Consumer"],
    "Apps": ["Consumer"],
    "AI/RL": ["AI/Training"],
    "MEV": ["Infra"],
    "Sequencing": ["Infra"],
    "Wallet": ["Infra"],
    "MPC/TSS": ["Infra"],
    "AI/Research": ["AI/Other"],
    "Provenance": ["Infra"],
    "AI/SaaS": ["AI/Other"],
    "AgriTech": ["Other"],
    "Cryptography": ["Privacy"],
    "Oracles": ["Oracle"],
    "LegalTech": ["Other"],
    "AI/Culture": ["AI/Other"],
    "AI/ComputerVision": ["AI/Other"],
    "Consumer app": ["Consumer"],
    "Automation": ["Infra"],
    "AI/Content": ["AI/Other"],
    "AI/Identity": ["AI/Other"],
    "Data Union": ["AI/Data"],
    "DeFi/Trading": ["DeFi"],
    "DeSci": ["Other"],
    "IoT/Robotics": ["DePIN"],
    "AI (product feature)": ["AI/Other"],
    "Consumer apps": ["Consumer"],
    "AI/HR": ["AI/Other"],
    "Web3 jobs": ["Other"],
    "AI/DeFi": ["AI/Other", "DeFi"],
    "ZK": ["Privacy"],
    "L2": ["Infra"],
    "AI/Media": ["AI/Other"],
    "Music": ["Consumer"],
    "AI/Gaming": ["Gaming"],
    "DePIN/Infra": ["DePIN"],
    "Networking": ["Infra"],
    "Creator economy": ["Social"],
    "DeFAI": ["AI/Other", "DeFi"],
    "AI/Community": ["Social"],
    "Community": ["Social"],
    "AI/Models": ["AI/Inference"],
    "AI/API": ["AI/Inference"],
    "AI/Discovery": ["AI/Other"],
    "Interop": ["Bridge"],
    "AI/Edge": ["AI/Compute"],
    "Real estate": ["Other"],
    "AI/GenAI": ["AI/Other"],
    "App": ["Consumer"],
    "Travel": ["Consumer"],
    "Bonds": ["DeFi"],
    "AI/Meta": ["AI/Other"],
    "Interop/Bridge": ["Bridge"],
    "AI/Oracle": ["Oracle"],
    "Compute": ["AI/Compute"],
    "DAO tooling": ["DAO"],
    "Tooling": ["Infra"],
    "Dev/Marketplace": ["Infra"],
    "Productivity": ["Consumer"],
    "Insurance": ["DeFi"],
    "Research": ["Other"],
    "L1/L2": ["Infra"],
    "Trading tools": ["DeFi"],
}


def map_category(raw):
    """Return (canonical label list, list of raw labels)."""
    if raw is None:
        return None, None
    labels = [x.strip() for x in raw.split("|") if x.strip()]
    out = []
    for lab in labels:
        targets = [lab] if lab in CATEGORY_CANON else CATEGORY_MAP.get(lab, ["Other"])
        for t in targets:
            if t not in out:
                out.append(t)
    return out, labels
