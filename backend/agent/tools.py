"""Tools the support agent can call.

Each tool is a plain Python function plus a JSON schema that tells the LLM
what the tool does and which arguments it takes.
"""

import ast
import json
import operator
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

with open(DATA_DIR / "knowledge_base.json", encoding="utf-8") as f:
    KNOWLEDGE_BASE = json.load(f)

with open(DATA_DIR / "orders.json", encoding="utf-8") as f:
    ORDERS = {order["order_id"]: order for order in json.load(f)}

STOPWORDS = {"the", "a", "an", "is", "are", "can", "i", "my", "do", "you", "to", "of", "for", "and", "or", "it", "how", "what", "in", "on"}


def _words(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS}


def search_knowledge_base(query):
    # Simple keyword overlap. Good enough for 7 documents, and easy to reason about
    # when we later check whether the agent's answer is grounded in what it retrieved.
    query_words = _words(query)
    scored = []
    for doc in KNOWLEDGE_BASE:
        overlap = len(query_words & _words(doc["title"] + " " + doc["text"]))
        if overlap > 0:
            scored.append((overlap, doc))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    results = [{"title": doc["title"], "text": doc["text"]} for _, doc in scored[:2]]
    if not results:
        return {"results": [], "message": "No matching help articles found."}
    return {"results": results}


def lookup_order(order_id):
    order_id = str(order_id).strip().lstrip("#")
    order = ORDERS.get(order_id)
    if order is None:
        return {"error": f"Order {order_id} not found."}
    return order


ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def _evaluate(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_OPERATORS:
        return ALLOWED_OPERATORS[type(node.op)](_evaluate(node.left), _evaluate(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_OPERATORS:
        return ALLOWED_OPERATORS[type(node.op)](_evaluate(node.operand))
    raise ValueError("Only numbers and + - * / are allowed.")


def calculator(expression):
    # We never call eval() on model output. Parsing into an AST and only allowing
    # arithmetic nodes means "__import__('os').system(...)" is rejected.
    try:
        result = _evaluate(ast.parse(expression, mode="eval").body)
    except (SyntaxError, ValueError, ZeroDivisionError) as e:
        return {"error": f"Could not calculate '{expression}': {e}"}
    return {"expression": expression, "result": round(result, 2)}


TOOL_FUNCTIONS = {
    "search_knowledge_base": search_knowledge_base,
    "lookup_order": lookup_order,
    "calculator": calculator,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search the store's help articles (returns, refunds, shipping, warranty, payments, cancellations).",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "What to search for"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": "Get the details and status of a customer's order by order ID.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string", "description": "The order ID, e.g. 1042"}},
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate an arithmetic expression such as '19.99 * 2 + 4.99'.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
        },
    },
]


def run_tool(name, arguments):
    # Errors are returned to the model as data instead of crashing the run.
    # That lets the model recover (e.g. ask the user for a valid order ID).
    function = TOOL_FUNCTIONS.get(name)
    if function is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return function(**arguments)
    except TypeError as e:
        return {"error": f"Bad arguments for {name}: {e}"}
