import asyncio
import json
import os
import time
import streamlit as st
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI, RateLimitError
from fastmcp import Client
from mcp_server import mcp
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Você é um assistente especializado em contratos públicos do Portal Nacional de Contratações Públicas (PNCP).

## Contexto
Base de dados: contratos de dispensa eletrônica do município de Recife/PE.

## Ferramentas disponíveis
- buscar_contratos: filtre por período (YYYY-MM-DD), órgão, situação e faixa de valor
- resumo_contratos: totais, valor estimado, ranking por órgão, distribuição por situação
- buscar_contrato_por_id: detalhes completos de um contrato pelo número de controle PNCP
- executar_etl: atualiza a base buscando novos contratos na API PNCP (formato YYYYMMDD)

## Formatação das respostas
- Valores monetários: R$ com separadores (ex: R$ 1.500.000,00)
- Datas: DD/MM/AAAA
- Confirme sempre o período consultado
- Múltiplos contratos: use lista organizada com objeto, órgão e valor
"""


def run_async(coro):
    with ThreadPoolExecutor() as pool:
        return pool.submit(asyncio.run, coro).result()


async def _list_tools():
    async with Client(mcp) as c:
        return await c.list_tools()


async def _call_tool(name: str, args: dict):
    async with Client(mcp) as c:
        return await c.call_tool(name, args)


def to_openai_tool(t) -> dict:
    return {
        "type": "function",
        "function": {
            "name": t.name,
            "description": t.description or "",
            "parameters": t.inputSchema,
        },
    }


def _create_with_retry(max_retries: int = 3, **kwargs):
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(**kwargs)
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait = 10 * (attempt + 1)
            st.toast(f"Rate limit — aguardando {wait}s...", icon="⏳")
            time.sleep(wait)


def chat(pergunta: str, historico: list) -> str:
    tools = run_async(_list_tools())
    openai_tools = [to_openai_tool(t) for t in tools]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + historico + [{"role": "user", "content": pergunta}]

    response = _create_with_retry(model=MODEL, messages=messages, tools=openai_tools)

    msg = response.choices[0].message
    messages.append(msg)

    if msg.tool_calls:
        for tc in msg.tool_calls:
            resultado = run_async(_call_tool(tc.function.name, json.loads(tc.function.arguments)))
            content = resultado.content[0].text if resultado and resultado.content else "sem resultado"
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": content,
            })

        final = _create_with_retry(model=MODEL, messages=messages)
        return final.choices[0].message.content

    return msg.content or ""


# --- UI ---

st.set_page_config(page_title="Chatbot PNCP", page_icon="📋", layout="centered")
st.title("📋 Contratos Públicos — PNCP")
st.caption("Consulte contratos de dispensa eletrônica de Recife/PE")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "display_messages" not in st.session_state:
    st.session_state.display_messages = []

for msg in st.session_state.display_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Pergunte sobre contratos..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.display_messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Consultando..."):
            resposta = chat(prompt, st.session_state.messages)
        st.markdown(resposta)

    st.session_state.display_messages.append({"role": "assistant", "content": resposta})
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": resposta})
