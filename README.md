<img width="2557" height="1038" alt="image" src="https://github.com/user-attachments/assets/17f28628-4ead-4e89-97c3-056bd5726da2" />


# 📟 Finsight Nexus: Enterprise Multi-Agent AI Quant Terminal

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32.0-red)
![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-purple)
![Gemini](https://img.shields.io/badge/Google_Gemini-1.5_Flash-orange)
![License](https://img.shields.io/badge/License-MIT-green)

**Finsight Nexus** is an enterprise-grade, Bloomberg-style quantitative AI terminal. It bridges the gap between raw financial market data and actionable options trading strategies by leveraging a **Zero-Hallucination RAG Pipeline** and a **LangGraph-powered Multi-Agent Execution Desk**.

> 💡 **Architectural Highlight:** This system goes beyond standard LLM wrappers. It features autonomous agents that dynamically generate Python quantitative models, execute them in a local sandbox, and utilize the mathematical outputs to formulate mathematically-backed options playbooks.




---

## 🚀 Core Architecture & Features

### 1. 🧠 Zero-Hallucination RAG Strategist (Engine 1)
- **Semantic Signal Extraction:** Ingests up to 48 hours of live macro and ticker-specific news firehose, utilizing vector similarity search to extract the Top 10 highest-signal headlines.
- **Strict Grounding Guardrails:** Prompt-engineered with absolute zero-knowledge-leakage constraints. The AI is forced to formulate thesis *strictly* on retrieved news and real-time technical indicators (RSI, MACD, SMA20).
- **Evaluation Badge:** Features a UI-integrated `Faithfulness 10.0/10` health check badge to guarantee institutional-level trust.

### 2. ⚡ LangGraph Multi-Agent Execution Desk (Engine 2)
A 4-node sequential state machine (Ledger) that mimics a real Wall Street quant desk:
1. **Macro Strategist Agent:** Formulates a baseline thesis utilizing VIX and price action.
2. **Risk Quant Agent:** Translates the thesis into executable Python code (e.g., implied daily volatility models: `VIX / sqrt(252)`).
3. **Execution Sandbox (PythonREPL):** Dynamically executes the AI-generated code to prove the mathematical viability of the thesis.
4. **Head Trader Agent:** Formulates the final options derivative strategy (e.g., Long Strangle, Iron Condor) heavily weighted by the exact output from the Sandbox.

### 3. 🚄 High-Performance Concurrent Pipeline
- **I/O Bottleneck Eradication:** Integrates `concurrent.futures.ThreadPoolExecutor` to handle 30+ simultaneous Google Translate API requests, dropping translation latency from ~30 seconds to under 1.5 seconds.
- **Dynamic Model Routing:** Features a custom fail-safe radar (`_get_dynamic_model`) to automatically scan and hook into the active Gemini API endpoints, preventing `404 NOT_FOUND` LangChain region lock errors.

### 4. 🌐 Native Bilingual i18n UI
- 100% elastic UI supporting seamless English (EN) and Chinese (CN) toggling.
- Not just static UI translation: System state, Multi-Agent thinking processes, and final RAG outputs are dynamically prompted to output strictly in the selected target language.

---

## 🛠️ Tech Stack

* **Frontend / Dashboard:** Streamlit, Plotly (Advanced Subplot Candlesticks, MACD, Volume)
* **AI Orchestration:** LangChain Core, LangGraph, Google Generative AI (Native SDK)
* **Data Ingestion:** `yfinance`, `beautifulsoup4`, `requests`
* **Concurrency & i18n:** `concurrent.futures`, `deep-translator`
* **Execution Sandbox:** `langchain_experimental.utilities.PythonREPL`

---

