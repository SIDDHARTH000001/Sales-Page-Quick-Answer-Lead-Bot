import json
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
import operator
import os
from langchain_google_genai import ChatGoogleGenerativeAI
import configparser
from tools import get_customer_support, get_context, save_lead_to_excel

    
try:
    config = configparser.ConfigParser()
    files_read = config.read("config.properties")  # returns list of read files
    if not files_read:
        raise FileNotFoundError("config.properties not found or could not be read")
    GEMINI_API_KEY = config.get("Credentials", "GEMINI_API_KEY")

except Exception as e:
    raise Exception(f"Error while trying to read config: {str(e)}")

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
)

tools = [get_customer_support, get_context, save_lead_to_excel]

tools_dict = {tool.name: tool for tool in tools}

llm_with_tools = llm.bind_tools(tools)


class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    
def call_model(state: AgentState):
    system_prompt = """
You are a professional virtual assistant for a B2B SaaS platform. 
Your goal is to answer visitor questions accurately using the provided knowledge base, 
which includes pricing, security & compliance, features, integrations, API limits, and support details.

Rules:
1. Only provide information that exists in the knowledge base or retrieved context.
2. If a question is outside the context of our SaaS platform, respond politely:
   "I'm sorry, I can only provide information about our platform and related services."
3. Always provide clear, concise, and well-structured answers.
4. Where applicable, cite the relevant feature, policy, or integration details from the knowledge base.
5. If the visitor shows high intent (e.g., asks about pricing, security, or integrations), 
   gently encourage them to request a quote or share their contact details.
6. Maintain a professional yet approachable tone — think knowledgeable SaaS pre-sales engineer.
"""
    
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def call_tool(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    
    tool_messages = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_to_call = tools_dict[tool_name]
        
        tool_result = tool_to_call.invoke(tool_call["args"])
        
        tool_messages.append(
            ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call["id"]
            )
        )
    
    return {"messages": tool_messages}

def should_continue(state: AgentState) -> Literal["tools", "end"]:
    messages = state["messages"]
    last_message = messages[-1]
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    else:
        return "end"

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", call_tool)
workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "end": END,
    }
)

workflow.add_edge("tools", "agent")

app = workflow.compile()


def ask_agent(query):
    initial_state = {
        "messages": [HumanMessage(content=query)]
    }
    print("answer sent...")
    return app.invoke(initial_state)['messages'][-1].content

    
