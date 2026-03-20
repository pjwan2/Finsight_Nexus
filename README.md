<img width="1024" height="880" alt="image" src="https://github.com/user-attachments/assets/3c5f0a81-1e42-45cf-a8a4-15cd3fcf9422" />

# 📈 Finsight Nexus 3.0: Enterprise-Grade AI Quant Terminal

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Gemini](https://img.shields.io/badge/Google-Gemini_Flash-orange.svg)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**Finsight Nexus** is a local-first, zero-hallucination institutional quantitative trading terminal. It merges real-time macroeconomic data, semantic RAG (Retrieval-Augmented Generation), and multi-agent workflows to deliver actionable options playbooks and macro-strategic insights.



---

## 🚀 Key Features

* **Bloomberg-Style UI**: Lightning-fast, terminal-grade interface built on Streamlit, featuring real-time technical indicators (RSI, MACD, SMA) and live option chains.
* **Semantic Search RAG**: Bypasses naive chronological truncation. Utilizes high-dimensional vector embeddings (`models/embedding-001` to `004`) and Cosine Similarity to recall the absolute highest-signal news.
* **Zero-Hallucination Guardrails**: Powered by strictly prompted Gemini models at `temperature: 0.1` to ensure AI analysis is 100% grounded in retrieved facts.
* **LLM-as-a-Judge Evaluation**: Includes an enterprise-grade standalone CI/CD evaluation pipeline (`eval_rag.py`) to mathematically score *Faithfulness* and *Context Relevance*.
* **Dynamic Model Resolution**: Zero hardcoded API versions. The system dynamically probes for the latest available Google Gemini capabilities to prevent deprecation 404s.

## 🧠 Architecture Overview

The system operates on an advanced multi-stage pipeline:
1.  **Radar**: Ingests massive raw market feeds.
2.  **Semantic Retrieval**: Vectorizes inputs to filter out market noise.
3.  **Macro Synthesizer**: Generates crisp, fundamental analyses based strictly on retrieved context.
4.  **Execution Desk**: Translates macro views into precise option strikes (e.g., Bear Put Spreads, Iron Condors).

## 🛠️ Quick Start

1. Clone the repository:
   ```bash
   git clone [https://github.com/YourUsername/Finsight_Nexus.git](https://github.com/YourUsername/Finsight_Nexus.git)
   cd Finsight_Nexus
