import requests
import time
import sqlite3
import datetime
from flask import Flask, render_template_string
import plotly.graph_objs as go

# 定义接口 URL 和请求头
url = "https://www.hfhmsh.com/gateway/agent/api/power/65935145"
headers = {
    'Host': 'www.hfhmsh.com',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Content-Type': 'application/json',
    'token': 'hZ5R0g2tr0ph7VyLiOXjn/kNuTxOCsHl',
    'Accept': '*/*',
    'Referer': 'https://servicewechat.com/wx2c6f3657c83fb2e9/7/page-frame.html',
}

# Flask 应用初始化
app = Flask(__name__)


# SQLite 数据库初始化
def init_db():
    conn = sqlite3.connect('charge_data.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS charge_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            power REAL,
            voltage REAL,
            capacity REAL
        )
    ''')
    conn.commit()
    conn.close()


# 插入数据到 SQLite 数据库
def save_data_to_db(power, voltage, capacity, timestamp):
    conn = sqlite3.connect('charge_data.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO charge_data (timestamp, power, voltage, capacity)
        VALUES (?, ?, ?, ?)
    ''', (timestamp, power, voltage, capacity))
    conn.commit()
    conn.close()


# 获取API数据并保存到数据库
def get_data():
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 如果返回码不是200, 会抛出异常
        data_json = response.json()

        # 提取数据
        power = data_json['data']['dynamic']['realdata']['power']
        voltage = data_json['data']['dynamic']['realdata']['voltage']
        capacity = data_json['data']['dynamic']['realdata']['powerCapacity']
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 保存数据到数据库
        save_data_to_db(power, voltage, capacity, timestamp)
        print(f"Data saved at {timestamp}: Power={power}, Voltage={voltage}, Capacity={capacity}")

    except Exception as e:
        print(f"Error occurred: {e}")


# 每隔10秒获取一次数据
def fetch_data_periodically():
    while True:
        get_data()
        time.sleep(10)  # 每隔10秒获取一次


# 读取数据库中的数据
def read_data_from_db():
    conn = sqlite3.connect('charge_data.db')
    c = conn.cursor()
    c.execute('SELECT timestamp, power, voltage, capacity FROM charge_data')
    rows = c.fetchall()
    conn.close()

    # 将数据转换为时间戳、功率、电压和容量列表
    timestamps, power, voltage, capacity = zip(*rows) if rows else ([], [], [], [])
    return list(timestamps), list(power), list(voltage), list(capacity)


# 创建 Plotly 图表
def create_chart():
    timestamps, power, voltage, capacity = read_data_from_db()

    fig = go.Figure()

    # 添加Power曲线
    fig.add_trace(go.Scatter(x=timestamps, y=power, mode='lines', name='Power', line=dict(color='blue')))

    # 添加Voltage曲线
    fig.add_trace(go.Scatter(x=timestamps, y=voltage, mode='lines', name='Voltage', line=dict(color='red')))

    # 添加Capacity曲线
    fig.add_trace(go.Scatter(x=timestamps, y=capacity, mode='lines', name='Capacity', line=dict(color='green')))

    fig.update_layout(
        title="Charge Data Over Time",
        xaxis_title="Timestamp",
        yaxis_title="Value",
        template="plotly_dark",
    )

    return fig.to_html(full_html=False)


# Flask 路由
@app.route('/')
def index():
    chart = create_chart()
    return render_template_string('''
        <html>
            <head>
                <title>Charge Data Dashboard</title>
            </head>
            <body>
                <h1>Charge Data Dashboard</h1>
                <h2>Power, Voltage, and Capacity Trends</h2>
                {{ chart | safe }}
            </body>
        </html>
    ''', chart=chart)


if __name__ == '__main__':
    # 初始化数据库
    init_db()

    # 启动定时数据获取线程
    import threading

    data_thread = threading.Thread(target=fetch_data_periodically, daemon=True)
    data_thread.start()

    # 启动 Flask 服务器
    app.run(debug=True, use_reloader=False)
