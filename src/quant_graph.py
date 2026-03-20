# -*- coding: utf-8 -*-
"""
src/quant_graph.py - Enterprise Multi-Agent Workflow
- Implements LangGraph state machine.
- Features a Code Execution Node (Python REPL) for quantitative validation.
- Supports dynamic bilingual output via 'lang' parameter.
"""
import os
from typing import TypedDict
from dotenv import load_dotenv

import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langchain_experimental.utilities import PythonREPL

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is missing. Please set it in .env")

genai.configure(api_key=api_key)

def _get_dynamic_model(preferred_type="flash"):
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods and preferred_type in m.name:
                return m.name
    except Exception:
        pass
    return 'gemini-1.5-flash'

dynamic_model = _get_dynamic_model("flash")
llm = ChatGoogleGenerativeAI(model=dynamic_model, temperature=0.1)
repl = PythonREPL()

# 🌟 1. 状态账本：加入 lang 字段
class QuantState(TypedDict):
    ticker: str
    current_price: float
    vix: float
    lang: str 
    macro_thesis: str
    code_snippet: str
    execution_result: str
    final_playbook: str

def strategist_node(state: QuantState):
    # 根据前端传来的 lang 决定输出语言
    target_lang = "Chinese" if state.get('lang') == "CN" else "English"
    prompt = f"""
    You are a Macro Strategist. 
    Ticker: {state['ticker']}, Price: {state['current_price']}, VIX: {state['vix']}
    Write a 2-sentence market outlook.
    OUTPUT LANGUAGE MUST BE: {target_lang}.
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"macro_thesis": response.content}

def risk_quant_node(state: QuantState):
    prompt = f"""
    You are a Quantitative Developer. 
    The Strategist says: {state['macro_thesis']}
    The VIX is currently {state['vix']}.
    
    TASK: Write a SHORT, valid Python script that calculates the implied daily move of this stock based on the VIX.
    Formula: Daily Move % = VIX / (252 ** 0.5)
    Print the result clearly. 
    
    RETURN ONLY VALID PYTHON CODE. DO NOT INCLUDE MARKDOWN TAGS LIKE ```python.
    """
    response = llm.invoke([SystemMessage(content="You return strictly executable python code, no markdown."),
                           HumanMessage(content=prompt)])
    code = response.content.replace("```python", "").replace("```", "").strip()
    return {"code_snippet": code}

def execution_environment_node(state: QuantState):
    code = state['code_snippet']
    try:
        result = repl.run(code)
        return {"execution_result": result}
    except Exception as e:
        return {"execution_result": f"Error executing code: {e}"}

def head_trader_node(state: QuantState):
    # 根据前端传来的 lang 决定最终交易策略的语言
    target_lang = "Chinese" if state.get('lang') == "CN" else "English"
    prompt = f"""
    You are the Head Options Trader.
    Strategist Thesis: {state['macro_thesis']}
    Quant Code Execution Output: {state['execution_result']}
    
    TASK: Based on the thesis and the mathematical proof from the execution output, recommend a specific Options Strategy (e.g., Iron Condor, Strangle). Keep it to 2 sentences.
    OUTPUT LANGUAGE MUST BE: {target_lang}.
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"final_playbook": response.content}

workflow = StateGraph(QuantState)

workflow.add_node("Strategist", strategist_node)
workflow.add_node("RiskQuant", risk_quant_node)
workflow.add_node("Sandbox", execution_environment_node)
workflow.add_node("HeadTrader", head_trader_node)

workflow.set_entry_point("Strategist")
workflow.add_edge("Strategist", "RiskQuant")
workflow.add_edge("RiskQuant", "Sandbox")
workflow.add_edge("Sandbox", "HeadTrader")
workflow.add_edge("HeadTrader", END)

quant_app = workflow.compile()


def run_quant_agent_team(ticker: str, current_price: float, vix: float, lang: str = "EN") -> dict:
    initial_state = {
        "ticker": str(ticker),
        "current_price": float(current_price),
        "vix": float(vix),
        "lang": str(lang),
        "macro_thesis": "",
        "code_snippet": "",
        "execution_result": "",
        "final_playbook": ""
    }
    return quant_app.invoke(initial_state)