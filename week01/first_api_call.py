#!/usr/bin/env python3
"""W1D1 验收：第一次调用 DeepSeek 大模型 API，打印返回内容与 token 数。

运行前先设置环境变量（在 Git Bash / 终端里执行一次）：
    export DEEPSEEK_API_KEY="sk-你的真实key"

然后运行：
    python week01/first_api_call.py

说明：Key 只从环境变量读取，不会写进任何文件，也不会被提交到 GitHub。
"""
import json
import os
import sys
import urllib.request
import urllib.error

API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"


def main():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 未找到环境变量 DEEPSEEK_API_KEY")
        print('请先运行： export DEEPSEEK_API_KEY="sk-你的真实key"')
        sys.exit(1)

    prompt = "用一句话向一个大二学生解释什么是 AI Agent。"
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"❌ HTTP 错误 {e.code}: {body}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 请求失败：{e}")
        sys.exit(1)

    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})

    print("=" * 50)
    print("📝 你的问题：", prompt)
    print("-" * 50)
    print("🤖 模型回复：")
    print(content)
    print("=" * 50)
    print("📊 Token 用量：")
    print(f"   输入(prompt) tokens     : {usage.get('prompt_tokens')}")
    print(f"   输出(completion) tokens : {usage.get('completion_tokens')}")
    print(f"   总计(total) tokens      : {usage.get('total_tokens')}")
    print(f"   模型: {data.get('model', MODEL)}")


if __name__ == "__main__":
    main()
