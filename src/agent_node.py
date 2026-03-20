# -*- coding: utf-8 -*-
"""
src/agent_node.py - Enterprise RAG Edition (Semantic Search + Options Playbook)
- Implements Vector Embeddings and Cosine Similarity for high-precision recall.
- Generates macro analysis and actionable options playbooks.
- Employs 100% dynamic model retrieval (Text & Embedding) to prevent 404 deprecation errors.
"""
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
from concurrent.futures import ThreadPoolExecutor
# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# --- Dynamic Model Resolvers (Enterprise Best Practice: Zero Hardcoding) ---
def _get_dynamic_model(preferred_type="flash"):
    """Dynamically retrieves the latest text generation model."""
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods and preferred_type in m.name:
                return m.name
    except Exception as e:
        print(f"[SYS] Dynamic text model retrieval failed: {e}")
    return 'gemini-1.5-flash'

def _get_dynamic_embedding_model():
    """Dynamically retrieves the best available embedding model."""
    try:
        available_models = []
        for m in genai.list_models():
            if 'embedContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        # Prefer the latest 004 model if available in the user's region/tier
        for m_name in available_models:
            if 'text-embedding-004' in m_name:
                return m_name
        
        # Fallback to the first available embedding model
        if available_models:
            return available_models[0]
            
    except Exception as e:
        print(f"[SYS] Dynamic embedding model retrieval failed: {e}")
        
    # Absolute fallback
    return 'models/embedding-001'

# --- Core: Semantic Retrieval Layer ---
def semantic_search_news(ticker, news_list, top_k=5):
    """
    Converts news headlines into vectors and calculates cosine similarity 
    against a target query to recall the most relevant Top-K articles.
    """
    if not news_list:
        return []
    
    if len(news_list) <= top_k:
        return news_list

    try:
        query = f"Significant market news, fundamental performance, macroeconomic impact, or major events deeply affecting {ticker} stock price and options volatility."
        
        # 🌟 Inject Dynamic Embedding Model
        embed_model_name = _get_dynamic_embedding_model()
        
        query_embedding = genai.embed_content(
            model=embed_model_name,
            content=query,
            task_type="retrieval_query"
        )['embedding']
        
        headlines = [item.get('headline', '') for item in news_list]
        news_embeddings_response = genai.embed_content(
            model=embed_model_name,
            content=headlines,
            task_type="retrieval_document"
        )
        
        q_vec = np.array(query_embedding).reshape(1, -1)
        doc_vecs = np.array(news_embeddings_response['embedding'])
        
        similarities = cosine_similarity(q_vec, doc_vecs)[0]
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        return [news_list[i] for i in top_indices]
        
    except Exception as e:
        print(f"[RAG SYS] Semantic search failed: {e}. Falling back to chronological order.")
        return news_list[:top_k]

# --- RAG Stage 2: AI Macro Analyst ---

def fetch_ai_analysis(ticker, current_price, rsi, macd, sma, earnings, vix, news_list, lang="EN", *args, **kwargs):
    if not api_key:
        return "API Key missing. Please set GEMINI_API_KEY in .env file."
        
    try:

        high_signal_news = semantic_search_news(ticker, news_list, top_k=10)
        
        news_context = "\n".join([f"- {n.get('time_str', '')}: {n.get('headline', '')}" for n in high_signal_news])
        if not news_context:
            news_context = "No significant semantic news signals found."

        macro_context = f"VIX Level: {vix}, Upcoming Earnings: {earnings}, RSI: {rsi}, MACD: {macd}, SMA20: {sma}"

   
        target_lang = "Chinese" if lang == "CN" else "English"
        prefix = "[AI 宏观策略师]" if lang == "CN" else "[AI Macro Strategist]"


        prompt = f"""
        Act as an elite quantitative macro strategist.
        Target Asset: {ticker} (Current Price: {current_price})
        
        RELEVANT SEMANTIC NEWS CONTEXT:
        {news_context}
        
        MACROECONOMIC CONTEXT:
        {macro_context}
        
        CRITICAL INSTRUCTIONS (READ CAREFULLY OR YOU WILL BE PENALIZED):
        1. GROUNDING RULE: You MUST formulate your analysis STRICTLY and EXCLUSIVELY using the facts explicitly stated in the "RELEVANT SEMANTIC NEWS CONTEXT" and "MACROECONOMIC CONTEXT" provided above.
        2. ZERO KNOWLEDGE LEAKAGE: DO NOT use your internal training data. DO NOT invent, hallucinate, or reference events, historical data, executives, or financial metrics that are not explicitly present in the text above.
        3. If the provided context is completely unrelated or insufficient, explicitly state: "Insufficient semantic context to formulate a definitive macro thesis."
        4. OUTPUT LANGUAGE: You MUST output your final analysis STRICTLY in {target_lang}.
        
        TASK:
        Provide a crisp, professional analysis (under 150 words). 
        Format EXACTLY as follows:
        
        {prefix} (Your macro analysis based strictly on the provided signals).
        """
        
        dynamic_model_name = _get_dynamic_model("flash")
   

        model = genai.GenerativeModel(dynamic_model_name, generation_config={"temperature": 0.1})
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"AI Generation Fault: {str(e)}"

# --- Execution Desk: Options Playbook ---
def fetch_exact_option_playbook(ticker, current_price, option_chain, analysis, *args, **kwargs):
    if not api_key:
        return "API Key missing."
        
    try:
        if not option_chain:
            return "Insufficient options data to generate a playbook."

        prompt = f"""
        Act as an elite quantitative options execution desk.
        Target Asset: {ticker} (Current Price: {current_price})
        
        MACRO ANALYSIS CONTEXT:
        {analysis}
        
        AVAILABLE OPTIONS DATA (Nearest Theta & Leap Expiries):
        {option_chain}
        
        TASK:
        Based strictly on the MACRO ANALYSIS and the AVAILABLE OPTIONS DATA, recommend ONE specific options strategy. 
        Provide the exact strikes to use from the data provided. Keep it highly concise, actionable, and under 100 words.
        Format strictly as follows:
        
        🎯 STRATEGY: [Name of Strategy, e.g., Iron Condor, Bull Put Spread]
        📝 EXECUTION: [Exact strikes and expiry dates]
        💡 RATIONALE: [One sentence explaining why based on the analysis]
        """
        
        # 🌟 Inject Dynamic Text Model
        dynamic_model_name = _get_dynamic_model("flash")
        model = genai.GenerativeModel(dynamic_model_name)
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"Playbook Generation Fault: {str(e)}"

# --- Dashboard Compatibility: News Translation Passthrough ---
# --- Fast, Zero-Cost Translation (Powered by Google Translate API) ---
# --- Fast, Concurrent Zero-Cost Translation ---
def translate_news_headlines(news_list, lang="EN", *args, **kwargs):
    """
    Uses Google Translate API with Multithreading to translate 30+ items in parallel.
    Reduces 30 seconds of blocking I/O to ~1 second.
    """
    if lang == "EN" or not news_list: 
        return news_list
        
    try:
        translator = GoogleTranslator(source='auto', target='zh-CN')
        
      
        def translate_single(n):
            if n.get('headline'):
                try:
                    n['headline'] = translator.translate(n['headline'])
                except:
                    pass
            return n

 
        with ThreadPoolExecutor(max_workers=15) as executor:
      
            news_list = list(executor.map(translate_single, news_list))
                
    except Exception as e:
        print(f"[Translation System Warning] Fallback to English due to: {e}")
        
    return news_list