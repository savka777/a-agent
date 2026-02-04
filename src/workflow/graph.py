from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from workflow.nodes import init_node, research_node, user_output_node
from workflow.routing import should_use_tools
from state.schema import AgentState
from agents.tools import RESEARCH_TOOLS


def create_app_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    # Nodes
    workflow.add_node('init', init_node)
    workflow.add_node('research', research_node)
    workflow.add_node('tools', ToolNode(RESEARCH_TOOLS))
    workflow.add_node('user_communication', user_output_node)

    # Edges
    workflow.set_entry_point('init')
    workflow.add_edge('init', 'research')

    # After research LLM call: check for tool calls
    #   -> has tool calls  -> 'tools' node executes them
    #   -> no tool calls   -> 'user_communication' formats the output
    workflow.add_conditional_edges('research', should_use_tools)

    # After tools execute, go back to research LLM to process results
    workflow.add_edge('tools', 'research')

    # After user communication, we're done
    workflow.add_edge('user_communication', END)

    return workflow

def compile_workflow():
    graph = create_app_graph()
    return graph.compile()


compiled_graph = None


def get_compiled_graph():
    global compiled_graph
    if compiled_graph is None:
        compiled_graph = compile_workflow()
    return compiled_graph


async def run_workflow(user_query: str) -> AgentState:
    from state.schema import create_init_state

    initial_state = create_init_state(
        user_request=user_query
    )

    graph = get_compiled_graph()
    print(graph.get_graph().draw_ascii())

    final_state = await graph.ainvoke(initial_state)
    return final_state
