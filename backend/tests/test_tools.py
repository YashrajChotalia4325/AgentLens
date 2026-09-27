from agent.tools import calculator, lookup_order, run_tool, search_knowledge_base


def test_lookup_existing_order():
    order = lookup_order("1042")
    assert order["status"] == "shipped"
    assert order["tracking_number"] == "TRK-88213"


def test_lookup_accepts_hash_prefix():
    assert lookup_order("#1041")["customer"] == "Asha"


def test_lookup_missing_order_returns_error():
    assert "error" in lookup_order("9999")


def test_search_finds_return_policy():
    results = search_knowledge_base("return electronics headphones")["results"]
    assert results[0]["title"] == "Return policy"


def test_calculator_basic_math():
    assert calculator("19.99 * 2 + 4.99")["result"] == 44.97


def test_calculator_rejects_code():
    assert "error" in calculator("__import__('os').system('dir')")


def test_run_tool_handles_unknown_tool_and_bad_args():
    assert "error" in run_tool("delete_database", {})
    assert "error" in run_tool("lookup_order", {"wrong_arg": "1"})
