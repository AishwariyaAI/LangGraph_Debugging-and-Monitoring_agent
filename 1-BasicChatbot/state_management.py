from typing import TypedDict
from langgraph.graph import StateGraph

class GraphState(TypedDict):
    question: str
    answer: str

def chatbot(state: GraphState):
    return {
        "answer": f"You asked: {state['question']}"
    }

builder = StateGraph(GraphState)

builder.add_node("chatbot", chatbot)

builder.set_entry_point("chatbot")
builder.set_finish_point("chatbot")

graph = builder.compile()

result = graph.invoke(
    {
        "question": "Explain Retrieval-Augmented Generation."
    }
)

print(result)