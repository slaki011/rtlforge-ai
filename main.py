from src.graph.workflow import graph


user_request = """
Create an 8-bit up/down counter with enable
and active-low synchronous reset.
"""


result = graph.invoke({
    "user_spec": user_request,
    "iteration": 0,
    "status": "STARTED"
})


print("\n===== STRUCTURED SPEC =====")
print(result["structured_spec"])

print("\n===== ARCHITECTURE =====")
print(result["architecture"])

print("\n===== GENERATED RTL =====")
print(result["rtl_code"])