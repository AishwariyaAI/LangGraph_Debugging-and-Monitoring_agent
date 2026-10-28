import logging
import time
from typing import TypedDict, Callable, Any

from langgraph.graph import StateGraph, START, END


# -------------------------------
# 1. Configure Logging
# -------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# -------------------------------
# 2. Define Agent State
# -------------------------------

class AgentState(TypedDict):
    input: str
    result: str
    logs: list[str]
    errors: list[str]


# -------------------------------
# 3. Monitoring Wrapper
# -------------------------------

def monitor(
    node_name: str,
    function: Callable[[AgentState], dict[str, Any]]
):
    def wrapper(state: AgentState) -> dict[str, Any]:

        start_time = time.perf_counter()

        logging.info("Starting node: %s", node_name)

        try:
            updates = function(state)

            duration = time.perf_counter() - start_time

            message = (
                f"{node_name}: SUCCESS | "
                f"Execution time: {duration:.4f} seconds"
            )

            logging.info(message)

            return {
                **updates,
                "logs": state["logs"] + [message]
            }

        except Exception as error:

            duration = time.perf_counter() - start_time

            message = (
                f"{node_name}: FAILED | "
                f"Error: {type(error).__name__}: {error}"
            )

            logging.exception(
                "Node %s failed after %.4f seconds",
                node_name,
                duration
            )

            return {
                "result": state["result"],
                "logs": state["logs"] + [
                    f"{node_name}: FAILED | "
                    f"Execution time: {duration:.4f} seconds"
                ],
                "errors": state["errors"] + [message]
            }

    return wrapper


# -------------------------------
# 4. Define Workflow Nodes
# -------------------------------

def validate_input(state: AgentState) -> dict:

    if not state["input"].strip():
        raise ValueError("Input cannot be empty")

    return {}


def process_input(state: AgentState) -> dict:

    # Simulate a processing failure for testing.
    if state["input"].strip().lower() == "error":
        raise RuntimeError("Simulated processing failure")

    result = state["input"].upper()

    return {"result": result}


def debug_report(state: AgentState) -> dict:

    if state["errors"]:
        logging.warning(
            "Workflow finished with %d error(s)",
            len(state["errors"])
        )
    else:
        logging.info("Workflow completed successfully")

    return {}


# -------------------------------
# 5. Define Conditional Routing
# -------------------------------

def check_validation(state: AgentState) -> str:

    if state["errors"]:
        return "debug"

    return "process"


# -------------------------------
# 6. Build LangGraph Workflow
# -------------------------------

builder = StateGraph(AgentState)

builder.add_node(
    "validate",
    monitor("validate", validate_input)
)

builder.add_node(
    "process",
    monitor("process", process_input)
)

builder.add_node(
    "debug",
    monitor("debug", debug_report)
)

builder.add_edge(START, "validate")

builder.add_conditional_edges(
    "validate",
    check_validation,
    {
        "process": "process",
        "debug": "debug"
    }
)

builder.add_edge("process", "debug")
builder.add_edge("debug", END)

app = builder.compile()


# -------------------------------
# 7. Execute Agent
# -------------------------------

if __name__ == "__main__":

    user_input = input("Enter input to process: ")

    initial_state: AgentState = {
        "input": user_input,
        "result": "",
        "logs": [],
        "errors": []
    }

    final_state = app.invoke(initial_state)

    print("\n========== MONITORING REPORT ==========")

    print("\nInput:", final_state["input"])
    print("Result:", final_state["result"] or "No result")

    print("\nExecution Logs:")

    for log in final_state["logs"]:
        print("-", log)

    print("\nErrors:")

    if final_state["errors"]:
        for error in final_state["errors"]:
            print("-", error)
    else:
        print("No errors detected")

    print("\nStatus:",
          "FAILED" if final_state["errors"] else "SUCCESS")

    print("=======================================")