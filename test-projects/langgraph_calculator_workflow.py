"""
LangGraph Calculator Workflow Example

This is a real LangGraph workflow that performs arithmetic calculations.
Based on the LangGraph quickstart guide from https://docs.langchain.com/oss/python/langgraph/quickstart
"""

from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict, Annotated
import operator

# Define tools
@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`.
    
    Args:
        a: First integer
        b: Second integer
    """
    return a * b

@tool
def add(a: int, b: int) -> int:
    """Adds `a` and `b`.
    
    Args:
        a: First integer
        b: Second integer
    """
    return a + b

@tool
def divide(a: int, b: int) -> float:
    """Divide `a` by `b`.
    
    Args:
        a: Dividend (numerator)
        b: Divisor (denominator)
    """
    if b == 0:
        return "Error: Division by zero"
    return a / b

# Initialize model
model = init_chat_model("claude-sonnet-4-5-20250929", temperature=0)

# Augment the LLM with tools
tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)

# Define state
class MessagesState(TypedDict):
    messages: Annotated[list, operator.add]
    llm_calls: int

# Define model node
def llm_call(state: dict):
    """LLM decides whether to call a tool or not"""
    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content="You are a helpful assistant tasked with performing arithmetic on a set of inputs."
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get('llm_calls', 0) + 1
    }

# Define tool node
def tool_node(state: dict):
    """Performs the tool call"""
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))
    return {"messages": result}

# Define end logic
def should_continue(state: MessagesState):
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""
    messages = state["messages"]
    last_message = messages[-1]
    
    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "tool_node"
    # Otherwise, we stop (reply to the user)
    return END

# Build workflow
calculator_graph = StateGraph(MessagesState)

# Add nodes
calculator_graph.add_node("llm_call", llm_call)
calculator_graph.add_node("tool_node", tool_node)

# Add edges to connect nodes
calculator_graph.add_edge(START, "llm_call")
calculator_graph.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", END]
)
calculator_graph.add_edge("tool_node", "llm_call")

# Compile the graph
compiled_calculator_graph = calculator_graph.compile()

# This graph can be exported using:
# omium export-langgraph test-projects/langgraph_calculator_workflow.py:compiled_calculator_graph -o langgraph_workflow.json

