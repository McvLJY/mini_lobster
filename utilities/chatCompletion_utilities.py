# 解析并打印内容
def print_response(response):
    print("Response Structure:")
    print("===================")

    # 打印顶层字段
    print(f"Content: {response.content}")
    print(f"Refusal: {response.refusal}")
    print(f"Role: {response.role}")
    print(f"Annotations: {response.annotations}")
    print(f"Audio: {response.audio}")
    print(f"Function Call: {response.function_call}")

    # 打印 tool_calls
    if response.tool_calls:
        print("\nTool Calls:")
        print("-----------")
        for tool_call in response.tool_calls:
            print(f"ID: {tool_call.id}")
            print(f"Type: {tool_call.type}")
            print(f"Index: {tool_call.index}")

            # 打印 function 的详细信息
            if tool_call.function:
                print("\nFunction Details:")
                print("-----------------")
                print(f"Name: {tool_call.function.name}")

                # 解析 arguments 并格式化输出
                try:
                    arguments = eval(tool_call.function.arguments)
                    print("Arguments (Formatted):")
                    for key, value in arguments.items():
                        print(f"  {key}:")
                        print(f"    {value}")
                except Exception as e:
                    print(f"Failed to parse arguments: {e}")

    print("\nEnd of Response")