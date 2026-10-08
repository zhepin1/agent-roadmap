#!/usr/bin/env python3
"""W1D1 验收：第一次调用 DeepSeek 大模型 API，打印返回内容与 token 数。

运行前先设置环境变量（在 Git Bash / 终端里执行一次）：
    export DEEPSEEK_API_KEY="sk-你的真实key"

然后运行：
    python week01/first_api_call.py

说明：Key 只从环境变量读取，不会写进任何文件，也不会被提交到 GitHub。
"""

# ---- 导入标准库模块（Python 自带，无需 pip install）----
import json                # 把 Python 的 dict/list 转成 JSON 字符串，以及把返回的 JSON 解析回 dict
import os                  # 读取系统环境变量（在这里拿 API Key）
import sys                 # 出错时用 sys.exit() 退出程序
import urllib.request      # Python 自带的“发 HTTP 请求”工具（本脚本用它，不用装 httpx/requests）
import urllib.error        # urllib 出错时抛出的异常类型

# ---- 常量：全大写表示“约定不改的值” ----
API_URL = "https://api.deepseek.com/chat/completions"  # DeepSeek 的对话接口地址
MODEL = "deepseek-chat"                                 # 要用的模型名


def main():
    # ① 读取 API Key：os.environ 是一个“环境变量字典”，.get("名字") 按名字取值
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    # ② 防御：没设 Key 就报错并退出，避免后面空跑
    if not api_key:
        print("❌ 未找到环境变量 DEEPSEEK_API_KEY")
        print('请先运行： export DEEPSEEK_API_KEY="sk-你的真实key"')
        sys.exit(1)   # 数字 1 表示“异常退出”

    # ③ 要发给模型的问题（一个普通字符串变量）
    prompt = "用一句话向一个大二学生解释什么是 AI Agent。"
    # ④ 组装请求体 payload：一个「字典 dict」，里面又嵌套了列表和字典
    payload = {
        "model": MODEL,                                     # 用哪个模型
        "messages": [{"role": "user", "content": prompt}],  # 对话消息列表：一条 user 消息
        "stream": False,                                    # 不要流式，一次返回完整结果
    }
    # ⑤ 构造 HTTP 请求对象：把 URL、数据、请求头、方法(POST) 都装进去
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),   # dict → JSON 字符串 → 转成 bytes 才能发送
        headers={
            "Authorization": f"Bearer {api_key}",    # f-string：把 Key 拼进字符串；Bearer 是鉴权方式
            "Content-Type": "application/json",      # 告诉服务器“我发的是 JSON”
        },
        method="POST",
    )

    # ⑥ 真正发请求，并用 try/except 兜住各种出错（网络/鉴权/超时）
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:   # with：用完自动关连接；30 秒超时
            data = json.loads(resp.read().decode("utf-8"))      # 读回字节 → 解码字符串 → 解析成 dict
    except urllib.error.HTTPError as e:   # 服务器回了错误状态码（如 401 = Key 无效）
        body = e.read().decode("utf-8", errors="replace")
        print(f"❌ HTTP 错误 {e.code}: {body}")
        sys.exit(1)
    except Exception as e:                 # 其它任何意外（断网等）
        print(f"❌ 请求失败：{e}")
        sys.exit(1)

    # ⑦ 从返回的 dict 里取我们要的字段（dict 层层嵌套取值）
    content = data["choices"][0]["message"]["content"]   # 第 1 条回复的文本内容
    usage = data.get("usage", {})                        # token 用量；用 .get 防字段缺失报错

    # ⑧ 打印结果（print = 往终端输出）
    print("=" * 50)                          # 字符串 × 数字 = 重复 50 次，做分隔线
    print("📝 你的问题：", prompt)
    print("-" * 50)
    print("🤖 模型回复：")
    print(content)
    print("=" * 50)
    print("📊 Token 用量：")
    # f-string 里 {usage.get('prompt_tokens')} 从用量字典取值，取不到显示 None
    print(f"   输入(prompt) tokens     : {usage.get('prompt_tokens')}")
    print(f"   输出(completion) tokens : {usage.get('completion_tokens')}")
    print(f"   总计(total) tokens      : {usage.get('total_tokens')}")
    print(f"   模型: {data.get('model', MODEL)}")


# ⑨ Python 的“入口守卫”：只有直接运行本文件时才调用 main()
if __name__ == "__main__":
    main()
