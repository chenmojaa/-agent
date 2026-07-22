"""LangGraph graph: retrieve -> answer."""
from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from app.agent.state import AgentState
from app.agent.nodes.retrieve import retrieve_node
from app.agent.nodes.answer import answer_node


def build_graph():
  g = StateGraph(AgentState)
  g.add_node("retrieve", retrieve_node)
  g.add_node("answer", answer_node)
  g.add_edge(START, "retrieve")
  g.add_edge("retrieve", "answer")
  g.add_edge("answer", END)
  return g.compile()


graph = build_graph()
