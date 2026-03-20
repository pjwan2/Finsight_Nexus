# -*- coding: utf-8 -*-
"""
src/eval_rag.py - Enterprise RAG Evaluation Pipeline
- Implements 'LLM-as-a-Judge' paradigm to quantify RAG performance.
- Evaluates Faithfulness (Hallucination rate) and Answer Relevance.
- Uses dynamic model retrieval to prevent deprecation 404s.
"""
import os
import sys
import json
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv

# Import the actual functions AND the dynamic model resolver from our core system
try:
    from agent_node import semantic_search_news, fetch_ai_analysis, _get_dynamic_model
except ImportError:
    print("[ERROR] Must be run from the root directory: python src/eval_rag.py")
    sys.exit(1)

# Initialize API
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")
genai.configure(api_key=api_key)

# --- 1. The Golden Dataset (Test Cases) ---
EVAL_DATASET = [
    {
        "ticker": "NVDA",
        "current_price": 900.50,
        "vix": 15.2,
        "mock_news": [
            {"headline": "Nvidia announces record breaking Q3 earnings, beating all estimates", "time_str": "10:00"},
            {"headline": "US government plans to restrict further AI chip sales to China", "time_str": "11:00"},
            {"headline": "Apple releases new iPad", "time_str": "12:00"}, # Noise
            {"headline": "Federal Reserve keeps interest rates steady", "time_str": "13:00"}
        ]
    },
    {
        "ticker": "TSLA",
        "current_price": 170.20,
        "vix": 26.5, # High VIX scenario
        "mock_news": [
            {"headline": "Tesla pauses production at Gigafactory Berlin due to supply chain issues", "time_str": "09:00"},
            {"headline": "Elon Musk tweets about new AI features for FSD v12", "time_str": "09:30"},
            {"headline": "Global EV sales expected to slow down this quarter", "time_str": "10:00"}
        ]
    }
]

# --- 2. The LLM Judge (Automated Evaluator) ---
def evaluate_rag_output(ticker, context_used, generated_analysis):
    """
    Acts as an impartial judge to score the RAG output on Faithfulness and Relevance.
    """
    judge_prompt = f"""
    You are an impartial, strict enterprise Quality Assurance AI for a financial quantitative system.
    You need to evaluate the following AI-generated financial analysis based on the provided context.

    TICKER: {ticker}
    RETRIEVED CONTEXT (The Ground Truth):
    {context_used}

    GENERATED ANALYSIS (The Output to Evaluate):
    {generated_analysis}

    Evaluate on two metrics (Score 0 to 10):
    1. FAITHFULNESS (Anti-Hallucination): Does the generated analysis rely EXCLUSIVELY on the retrieved context? If it mentions facts, events, or numbers not present in the context, penalize it heavily.
    2. RELEVANCE: Is the analysis highly actionable, professional, and free of redundant fluff?

    Return your evaluation STRICTLY as a valid JSON object, with no markdown formatting or extra text.
    Format:
    {{
        "faithfulness_score": 9,
        "relevance_score": 8,
        "reasoning": "Brief explanation of deductions..."
    }}
    """
    
    try:
        # 🌟 USE DYNAMIC MODEL FOR THE JUDGE TOO!
        dynamic_model_name = _get_dynamic_model("flash")
        model = genai.GenerativeModel(dynamic_model_name, generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(judge_prompt)
        result = json.loads(response.text)
        return result
    except Exception as e:
        return {"faithfulness_score": 0, "relevance_score": 0, "reasoning": f"Eval Failed: {e}"}

# --- 3. The Evaluation Execution Loop ---
def run_evaluation_pipeline():
    print("\n" + "="*50)
    print("🚀 INIT: Enterprise RAG Evaluation Pipeline")
    print("="*50 + "\n")
    
    results = []
    
    for idx, test_case in enumerate(EVAL_DATASET):
        ticker = test_case["ticker"]
        print(f"[{idx+1}/{len(EVAL_DATASET)}] Testing RAG System for Ticker: {ticker}...")
        
# Step A: Test Retrieval (Semantic Search)
        retrieved_news = semantic_search_news(ticker, test_case["mock_news"], top_k=3)
        news_str = "\n".join([f"- {n['headline']}" for n in retrieved_news])
        
        # 🌟 NEW: Compile the FULL context (News + Macro) for the Judge
        full_ground_truth = f"""
        [NEWS]
        {news_str}
        
        [MACRO]
        Current Price: {test_case['current_price']}, VIX: {test_case["vix"]}, RSI: 50, MACD: 0, SMA20: {test_case['current_price']}, Earnings: N/A
        """
        
        # Step B: Test Generation (AI Brain)
        analysis = fetch_ai_analysis(
            ticker=ticker, 
            current_price=test_case["current_price"], 
            rsi=50, macd=0, sma=test_case["current_price"], earnings="N/A", 
            vix=test_case["vix"], 
            news_list=retrieved_news 
        )
        
        # Step C: Run the LLM Judge (Now with full vision!)
        eval_metrics = evaluate_rag_output(ticker, full_ground_truth, analysis)
        
        # Log results
        results.append({
            "Ticker": ticker,
            "Faithfulness (0-10)": eval_metrics.get("faithfulness_score", 0),
            "Relevance (0-10)": eval_metrics.get("relevance_score", 0),
            "Judge Reasoning": eval_metrics.get("reasoning", "")[:80] + "..." # Truncate for display
        })
    
    # --- 4. Generate Enterprise Metrics Report ---
    print("\n" + "="*50)
    print("📊 FINAL EVALUATION REPORT")
    print("="*50)
    
    df = pd.DataFrame(results)
    print(df.to_markdown(index=False))
    
    avg_faith = df["Faithfulness (0-10)"].mean()
    avg_rel = df["Relevance (0-10)"].mean()
    
    print("\n" + "🎯 SYSTEM HEALTH METRICS:")
    print(f"Average Faithfulness (Anti-Hallucination): {avg_faith}/10.0")
    print(f"Average Answer Relevance:                  {avg_rel}/10.0")
    
    if avg_faith < 8.0:
        print("\n⚠️ WARNING: System is prone to hallucination. Guardrails need tightening.")
    else:
        print("\n✅ PASSED: RAG System meets enterprise reliability standards.")
    print("\n")

if __name__ == "__main__":
    run_evaluation_pipeline()