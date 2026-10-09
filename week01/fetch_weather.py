# -*- coding: utf-8 -*-
"""W1D4 练习：用 httpx 调公开天气 API，把返回的 JSON 解析后存进 SQLite。

对应今日语法点：json 模块 + 用 httpx 发 GET 请求。
不用 Key、完全免费的数据源：Open-Meteo（open-meteo.com）。
"""
import httpx          # 第三方库，需要先 pip install httpx；比标准库 urllib 好用，后面还会用它做并发
import sqlite3        # Python 自带，操作 SQLite 数据库
import json           # 标准库，把 dict 转成字符串存进数据库
from datetime import datetime, timezone  # 标准库，记录"抓取时间"

# ---- 配置区：改这里就能换城市 / 参数 ----
API_URL = "https://api.open-meteo.com/v1/forecast"
PARAMS = {
    "latitude": 39.9042,    # 北京纬度
    "longitude": 116.4074,  # 北京经度
    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",  # 要哪些实时字段
    "timezone": "Asia/Shanghai",
}
DB_PATH = "weather.db"      # 数据库文件名（运行后自动生成）


def fetch_weather():
    """发 GET 请求，拿回天气数据（dict 形式）。"""
    # httpx.get 发请求；params 会自动拼成 ?latitude=...&longitude=...
    resp = httpx.get(API_URL, params=PARAMS, timeout=10)
    # 如果返回状态码不是 2xx（比如 404/500），这里会直接抛异常，避免拿到错误数据还继续
    resp.raise_for_status()
    # .json() 把返回的文本（JSON 格式）解析成 Python 的 dict / list
    return resp.json()


def save_to_db(record):
    """把一条天气记录存进 SQLite。"""
    # 连接数据库（文件不存在会自动创建）
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        # 建表：IF NOT EXISTS 保证重复运行不会报错
        cur.execute("""
            CREATE TABLE IF NOT EXISTS weather (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                city         TEXT,
                fetched_at   TEXT,
                temperature  REAL,
                humidity     REAL,
                wind_speed   REAL,
                raw          TEXT
            )
        """)
        # 插入一条记录；用 ? 占位符防止 SQL 注入（好习惯，以后写 Agent 也别直接拼字符串）
        cur.execute("""
            INSERT INTO weather (city, fetched_at, temperature, humidity, wind_speed, raw)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            record["city"],
            record["fetched_at"],
            record["temperature"],
            record["humidity"],
            record["wind_speed"],
            record["raw"],
        ))
        conn.commit()  # 提交事务，数据才真正写入
    finally:
        conn.close()   # 不管成功失败都关掉连接，释放资源


def main():
    data = fetch_weather()          # 1) 抓数据
    current = data["current"]       # 2) 从嵌套 dict 里取到"当前天气"那一层
    record = {
        "city": "北京",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "temperature": current["temperature_2m"],
        "humidity": current["relative_humidity_2m"],
        "wind_speed": current["wind_speed_10m"],
        "raw": json.dumps(data, ensure_ascii=False),  # 原始 JSON 存一份，方便以后查
    }
    save_to_db(record)              # 3) 存数据库
    # 4) 打印结果，f-string 把变量塞进字符串
    print(f"已保存 {record['city']} 的天气：")
    print(f"  温度 {record['temperature']} °C")
    print(f"  湿度 {record['humidity']} %")
    print(f"  风速 {record['wind_speed']} km/h")
    print(f"  抓取时间 {record['fetched_at']}")


if __name__ == "__main__":
    main()
