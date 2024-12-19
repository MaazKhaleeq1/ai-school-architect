# Step 1: Import necessary modules and classes
# Fill in any additional imports you might need
from typing import Annotated, Any, Dict, List, Optional, Sequence, TypedDict
import functools
import operator
import subprocess

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools.retriever import create_retriever_tool
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from langchain_experimental.tools import PythonREPLTool
from langgraph.graph import StateGraph, END

@tool
def commit_and_create_pr(
    branch_name: str,
    commit_message: str,
    pr_title: str,
    pr_body: str = "Auto-generated PR via langchain-based code agent."
) -> str:
    """
    Creates a new branch, commits the current working directory code changes,
    and opens a pull request. Uses local git + GitHub CLI.
    
    Prerequisites:
    - 'git' is installed and working locally.
    - 'gh' (GitHub CLI) is installed and authenticated.
    - You have write permissions to the repo (and an origin remote).
    """
    try:
        # Create a new branch
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        
        # Stage and commit changes
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
        # Push the branch
        subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)
        
        # Create a pull request
        pr_cmd = [
            "gh", "pr", "create",
            "--title", pr_title,
            "--body", pr_body,
            "--base", "main",  # or 'master', depending on your repo
            "--head", branch_name
        ]
        pr_output = subprocess.run(pr_cmd, check=True, capture_output=True, text=True)
        
        return f"Pull request created successfully:\n{pr_output.stdout}"
    except subprocess.CalledProcessError as e:
        return f"Error in commit_and_create_pr: {e}\n{e.output}"

# Step 2: Define tools
# Here, define any tools the agents might use. Example given:
tavily_tool = TavilySearchResults(max_results=5)

# This tool executes code locally, which can be unsafe. Use with caution:
python_repl_tool = PythonREPLTool()

# Step 3: Define the system prompt for the supervisor agent
# Customize the members list as needed.
members = ["Coder", "Researcher", "Reviewer", "QA Tester"]
system_prompt = (
    f"You are a supervisor tasked with managing a conversation between the"
    f" following workers:  {members}. Given the following user request,"
    f" respond with the worker to act next. Each worker will perform a"
    f" task and respond with their results and status. When finished,"
    f" respond with FINISH."
)

# Step 4: Define options for the supervisor to choose from
options = members + ["FINISH"]

# Step 5: Define the function for OpenAI function calling
# Define what the function should do and its parameters.
function_def = {
    "name": "route",
    "description": "Select the next role.",
    "parameters": {
        "title": "routeSchema",
        "type": "object",
        "properties": {
            "next": {
                "title": "Next",
                "anyOf": [
                    {"enum": options},
                ],
            }
        },
        "required": ["next"],
    },
}
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        (
            f"system",
            f"Given the conversation above, who should act next?"
            f" Or should we FINISH? Select one of: {options}",
        ),
    ]
).partial(options=str(options), members=", ".join(members))

# Step 6: Define the prompt for the supervisor agent
# Customize the prompt if needed.

# Step 7: Initialize the language model
# Choose the model you need, e.g., "gpt-4o"
llm = ChatOpenAI(model="gpt-4o")

# Step 8: Create the supervisor chain
# Define how the supervisor chain will process messages.
supervisor_chain = (
    prompt
    | llm.bind_functions(functions=[function_def], function_call="route")
    | JsonOutputFunctionsParser()
)

# Step 9: Define a typed dictionary for agent state
# The agent state is the input to each node in the graph
class AgentState(TypedDict):
    # The annotation tells the graph that new messages will always
    # be added to the current states
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # The 'next' field indicates where to route to next
    next: str


# Define the RAG-related components
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
document_vectorstore = PineconeVectorStore(index_name="lithium-faf-code", embedding=embeddings)
retriever = document_vectorstore.as_retriever()

# Step 10: Function to create an agent
# Fill in the system prompt and tools for each agent you need to create.
def create_agent(llm: ChatOpenAI, tools: list, system_prompt: str):
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_prompt,
            ),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    agent = create_openai_tools_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools)
    return executor

# Step 11: Function to create an agent node
# This function processes the state through the agent and returns the result.
def agent_node(state, agent, name):
    result = agent.invoke(state)
    return {"messages": [HumanMessage(content=result["output"], name=name)]}

# Step 12: Create agents and their corresponding nodes
# Define the specific role and tools for each agent.
retriever_tool = create_retriever_tool(
    retriever,
    "search_code",
    "Searches and returns relevant code from lithium-faf-code.",
)
research_agent = create_agent(llm, [tavily_tool, retriever_tool], "You are a researcher. You have the application code and web search tools at your disposal.")
research_node = functools.partial(agent_node, agent=research_agent, name="Researcher")

review_agent = create_agent(llm, [tavily_tool, retriever_tool],
                            """You are an senior developer. You excel at code reviews.
                            You use the application code and web search tools to identify potential issues and make sure code matches the existing standards.
                            You give detailed and specific actionable feedback.
                            You aren't rude, but you don't worry about being polite either.
                            Instead you just communicate directly about technical matters.
                            """)
review_node = functools.partial(agent_node, agent=review_agent, name="Reviewer")

test_agent = create_agent(
    llm,
    [python_repl_tool],  # DANGER DANGER runs arbitrary Python code
    "You may generate safe python code to test functions and classes using unittest or pytest.",
)
test_node = functools.partial(agent_node, agent=test_agent, name="QA Tester")

code_agent = create_agent(
    llm,
    [python_repl_tool, retriever_tool, commit_and_create_pr],  # ALSO DANGER DANGER
    """You may generate safe code to implement the requested feature or fix the bug.
    You leverage the existing codebase and Python REPL to write and test code.
    You generate unit tests that covers the new code completely.
    You follow the existing code style and conventions.
    You commit the code to a new branch and create a pull request at the end using the commit_and_create_pr tool.
    """,
)
code_node = functools.partial(agent_node, agent=code_agent, name="Coder")

# Step 13: Define the workflow using StateGraph
# Add nodes and their corresponding functions to the workflow.
workflow = StateGraph(AgentState)
workflow.add_node("Reviewer", review_node)
workflow.add_node("Researcher", research_node)
workflow.add_node("Coder", code_node)
workflow.add_node("QA Tester", test_node)
workflow.add_node("supervisor", supervisor_chain)

# Step 14: Add edges to the workflow
# Ensure that all workers report back to the supervisor.
for member in members:
    workflow.add_edge(member, "supervisor")

# Step 15: Define conditional edges
# The supervisor determines the next step or finishes the process.
conditional_map = {k: k for k in members}
conditional_map["FINISH"] = END
workflow.add_conditional_edges("supervisor", lambda x: x["next"], conditional_map)

# Step 16: Set the entry point
workflow.set_entry_point("supervisor")

# Step 17: Compile the workflow into a graph
# This creates the executable workflow.
graph = workflow.compile()
