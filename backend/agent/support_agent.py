"""A small tool-calling agent, written as a plain loop.

The loop:
  1. Send the conversation to the LLM along with the tool schemas.
  2. If the LLM asks for tools, run them and add the results to the conversation.
  3. Repeat until the LLM replies with plain text (the final answer) or we hit max_steps.

Every LLM call and tool call is wrapped in tracer.step(...), so the run can be
inspected afterwards.
"""

import json

from agent.tools import TOOL_SCHEMAS, run_tool
from agent.versions import get_version
from llm import chat
from tracing.tracer import Tracer

# The demo orders and policies are frozen at this date, so questions like
# "can I still return order 1041?" always have the same correct answer.
# If we used the real date, our test cases would start failing over time.
STORE_DATE = "2026-09-25"


def run_agent(user_input, version="v1"):
    config = get_version(version)
    tracer = Tracer(config["agent_name"], version, config["model"], user_input)

    try:
        answer, status = _agent_loop(user_input, config, tracer)
        return tracer.finish(answer, status=status)
    except Exception as e:
        # A crash (network error, bad API key...) is still a run worth recording.
        return tracer.finish("", status="error", error_message=f"{type(e).__name__}: {e}")


def _agent_loop(user_input, config, tracer):
    model = config["model"]
    messages = [
        {"role": "system", "content": config["system_prompt"].format(today=STORE_DATE)},
        {"role": "user", "content": user_input},
    ]

    for _ in range(config["max_steps"]):
        # list(messages) takes a snapshot; `messages` keeps growing after this step.
        with tracer.step("llm", "llm_call", input={"messages": list(messages)}) as step:
            response = chat(model, messages, tools=TOOL_SCHEMAS)
            step.record_llm_response(model, response)
            step.name = "planner" if response.tool_calls else "final_answer"

        messages.append(response.assistant_message)
        if not response.tool_calls:
            return response.text, "success"

        for call in response.tool_calls:
            with tracer.step("tool", call.name, input=call.arguments) as step:
                result = run_tool(call.name, call.arguments)
                step.output = result
                if "error" in result:
                    step.error = result["error"]

            messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})

    return "Sorry, I couldn't complete this request. Please contact support.", "max_steps"
