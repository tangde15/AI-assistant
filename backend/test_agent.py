# test_agent.py
from agent import create_rag_agent

def test_agent_basic():
    agent = create_rag_agent()
    print("=== Agent 创建成功 ===")
    print(agent)

    print("\n=== 测试普通问答 ===")
    res = agent.invoke({
        "messages": [
            {"role": "user", "content": "你是谁？"}
        ]
    })
    print("AI 回答：", res["messages"][-1].content)

def test_agent_search():
    agent = create_rag_agent()

    print("\n=== 测试是否触发联网搜索 ===")
    res = agent.invoke({
        "messages": [
            {"role": "user", "content": "2024年全球经济热点有哪些？"}
        ]
    })

    print("\n--- 最终回答 ---")
    print(res["messages"][-1].content)

    print("\n--- 所有消息（检查是否有工具调用） ---")
    for msg in res["messages"]:
        print(f"[{msg.type}] {getattr(msg, 'content', None)}")


if __name__ == "__main__":
    test_agent_basic()
    test_agent_search()
