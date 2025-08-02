

# 📦 Personal Economy Agent

## 🚀 What is it?

The **Personal Economy Agent** is your AI-powered assistant that helps you unlock hidden value from your gadgets. Most of us buy electronics like phones, headphones, webcams, or laptops — but after a while, they sit unused in drawers, even though they still have resale value.

This project automatically tracks your electronic purchases, checks whether they’re still being used, and estimates their **realistic resale value** today. All data is kept private and encrypted in your **Hushh Vault**, with full user consent managed through the **Hushh MCP protocol**.

---

## 💡 Why is it useful?

* People forget about the **resale value of their old gadgets**.
* Traditional expense trackers only tell you what you spent — not what you can still earn back.
* With this system, your electronics become a **“hidden wallet”** — money you can recover anytime.
* Runs with **data security at the core** thanks to Hushh MCP.

---

## ✨ Key Features

* **Email Receipt Extraction** → Reads purchase invoices from Gmail/Outlook (Amazon, Flipkart, Croma, etc.) to identify item, price, purchase date, and platform.
* **Usage Detection (multi-signal)** →

  * **Calendar mentions** (e.g., meetings with "Zoom webcam" hint).
  * **Browser history** (e.g., searches like *“how to fix headphones not charging”* or *“buy new mouse”*).
  * **Email mentions** (e.g., warranty or repair emails).
  * **Driver/Device metadata** (e.g., was this webcam connected to the system recently? Battery check for headphones?).
* **Valuation Agent** → Estimates realistic resale prices based on category, age, and market trends in India.
* **Resale Deals Dashboard** → A simple dashboard that shows all your gadgets with their current resale values.
* **Privacy by Design** → All personal data is stored encrypted in the **Hushh Vault** with full user consent managed by the MCP protocol.

---

## ⚙️ How it Works (Step by Step)

1. **Receipt Agent** scans your emails daily → extracts product name, purchase date, price, and platform.
2. Data is stored in the **Hushh Vault** securely with user consent.
3. **Usage Agent** combines multiple signals:

   * Looks for related searches in **browser history**.
   * Checks **OS driver/device metadata** to see if the product was connected recently.
   * Scans **calendar events** for mentions of that device.
   * Reads **emails** for repair/warranty/service activity.
     Together, these signals form a picture of whether the product is *active, inactive, or uncertain*.
4. **Valuation Agent** calculates the resale value using depreciation logic + GPT reasoning.
5. **Resale Deals Agent** compiles all active items with their updated resale values and shows them in the dashboard.

---

## 🔐 Trust & Privacy

This project integrates the **Hushh MCP Protocol** for:

* **Consent Management** → User decides what data can be read.
* **Trust Links** → Verified, auditable connections between agents.
* **Vault Encryption** → All personal data stays private and encrypted.

---

## 🖥️ Example Use Case

* You bought a Logitech webcam in 2023.
* The system sees **no recent Zoom calendar meetings**, **no browser searches about webcam use**, and **no driver connection for 2 months**.
* It classifies the webcam as “inactive” and estimates resale at ₹2200.
* On the dashboard, you see this resale deal and can decide whether to sell or keep.

---

👉 With this, your gadgets stop being “forgotten junk” and start becoming **hidden cash you can unlock anytime**.

---
## How to run this project

```
cd frontend
npm install
npm run dev
```
the above snippet is for frontend

```
python -m hushh_mcp.server
```
to run the server

Now to run the chrome extension

- Open ```chrome://extensions/```
- Turn on developer mode
- select the folder ```hushh_mcp/chrome-extension```
- Do it after running the script
- click on the extension and click ```start monitoring```
- Thats it!

NOTE: DONT FORGET TO INSTALL DEPENDENCIES FROM ```requirements.txt``` for agents

## This is the flow of my project and it is explained in the video

![My Image](project_flow.jpg)

---
## Project directory
```
project-root/
│
├── frontend/                   # Frontend (React + Vite + Tailwind)
│   └── src/                    # Source code
│       └── pages/              # Page components
│           ├── Application.tsx
│           ├── Index.tsx
│           ├── Landing.tsx
│           ├── NotFound.tsx
│           ├── ReSale.tsx
│           └── Settings.tsx
│
├── hushh_mcp/                  # Backend core
│   ├── agents/                 # AI agents
│   │   ├── aggregator_agent.py
│   │   ├── calender_reader_agent.py
│   │   ├── context_agent.py
│   │   ├── cost_agent.py
│   │   ├── gmail_reader_agent.py
│   │   ├── receipt_agent.py
│   │   └── usage_agent.py
│   │
│   ├── jsons/                  # JSON outputs (data storage)
│   └── vault/                  # Encryption + secure storage
│       ├── encrypt.py
│       └── json_vault.py
│
├── tests/                      # Unit tests
│   ├── test_agents.py
│   ├── test_aggregator_agent.py
│   ├── test_calender_reader_agent.py
│   ├── test_context_agent.py
│   ├── test_cost_agent.py
│   ├── test_gmail_reader_agent.py
│   ├── test_receipt_agent.py
│   ├── test_usage_agent.py
│   └── test_vault.py
│
├── .env                        # Environment variables
├── .env.example                # Example env file
├── .gitignore                  # Git ignore rules
├── consent_token.json          # Consent token
├── project_flow.jpg            # Flow diagram
├── README.md                   # Documentation
├── requirements.txt            # Python dependencies
├── test.py                     # Test runner
└── token.json                  # API/Auth token
```