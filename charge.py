import requests
import time
import sqlite3
import datetime
from flask import Flask, render_template_string
import plotly.graph_objs as go

# 定义接口 URL 和请求头
charging_url = "https://www.hfhmsh.com/gateway/agent/api/power/charging?pageNum=1&pageSize=100"
data_url = "https://www.hfhmsh.com/gateway/agent/api/power/"
headers = {
    'Host': 'www.hfhmsh.com',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Content-Type': 'application/json',
    'token': 'hZ5R0g2tr0ph7VyLiOXjn/kNuTxOCsHl',
    'Accept': '*/*',
    'Referer': 'https://servicewechat.com/wx2c6f3657c83fb2e9/7/page-frame.html',
}

# 获取正在充电的订单 ID
def get_charging_order_id():
    try:
        response = requests.get(charging_url, headers=headers)
        response.raise_for_status()
        data_json = response.json()
        print(data_json)
        
        # 提取第一个充电订单的 ID
        if data_json['data'] and len(data_json['data']) > 0:
            order_id = data_json['data'][0]['id']
            print(f"正在充电的订单 ID: {order_id}")
            return order_id
        else:
            print("没有正在充电的订单")
            return None
    except Exception as e:
        print(f"获取充电订单失败: {e}")
        return None

# Flask 应用初始化
app = Flask(__name__)


# SQLite 数据库初始化
def init_db():
    conn = sqlite3.connect('charge_data.db')
    c = conn.cursor()
    
    # 检查表是否存在
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='charge_data'")
    if not c.fetchone():
        # 如果表不存在，创建新表
        c.execute('''
            CREATE TABLE charge_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                power REAL,
                voltage REAL,
                electric REAL DEFAULT 0,
                money REAL DEFAULT 0,
                orderId INTEGER DEFAULT 0
            )
        ''')
        print("创建新的数据库表")
    else:
        # 表存在，检查并添加缺失的列
        c.execute("PRAGMA table_info(charge_data)")
        columns = [info[1] for info in c.fetchall()]
        print(f"现有列: {columns}")
        
        # 添加缺失的列
        if 'electric' not in columns:
            c.execute('ALTER TABLE charge_data ADD COLUMN electric REAL DEFAULT 0')
            print("添加 electric 列")
            
        if 'money' not in columns:
            c.execute('ALTER TABLE charge_data ADD COLUMN money REAL DEFAULT 0')
            print("添加 money 列")
            
        if 'orderId' not in columns:
            c.execute('ALTER TABLE charge_data ADD COLUMN orderId INTEGER DEFAULT 0')
            print("添加 orderId 列")
    
    conn.commit()
    conn.close()


# 插入数据到 SQLite 数据库
def save_data_to_db(power, voltage, electric, money, orderId, timestamp):
    conn = sqlite3.connect('charge_data.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO charge_data (timestamp, power, voltage, electric, money, orderId)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (timestamp, power, voltage, electric, money, orderId))
    conn.commit()
    conn.close()


# 获取API数据并保存到数据库
def get_data(order_id):
    if not order_id:
        print("没有有效的订单 ID")
        return
        
    try:
        url = f"{data_url}{order_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 如果返回码不是200, 会抛出异常
        data_json = response.json()

        # 提取数据
        power = data_json['data']['dynamic']['realdata']['power']
        voltage = data_json['data']['dynamic']['realdata']['voltage']
        electric = data_json['data']['dynamic']['realdata'].get('electric', 0)  # 用电量
        money = data_json['data']['dynamic']['realdata'].get('money', 0)  # 费用
        orderId = order_id  # 订单 ID
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 保存数据到数据库
        save_data_to_db(power, voltage, electric, money, orderId, timestamp)
        print(f"Data saved at {timestamp}: Power={power}, Voltage={voltage}, Electric={electric}, Money={money}, OrderId={orderId}")

    except Exception as e:
        print(f"Error occurred: {e}")


# 每隔10秒获取一次数据
def fetch_data_periodically(order_id):
    while True:
        get_data(order_id)
        time.sleep(10)  # 每隔10秒获取一次


# 读取数据库中的数据
def read_data_from_db():
    conn = sqlite3.connect('charge_data.db')
    c = conn.cursor()
    
    # 首先尝试查询新表结构
    try:
        c.execute('SELECT timestamp, power, voltage, electric, money, orderId FROM charge_data')
        rows = c.fetchall()
        conn.close()
        
        # 将数据转换为时间戳、功率、电压、用电量、费用和订单ID列表
        if rows:
            timestamps, power, voltage, electric, money, orderId = zip(*rows)
            return list(timestamps), list(power), list(voltage), list(electric), list(money), list(orderId)
        else:
            return [], [], [], [], [], []
    except sqlite3.OperationalError as e:
        # 如果新表结构不存在，则回退到旧表结构
        print(f"使用旧表结构: {e}")
        c.execute('SELECT timestamp, power, voltage, capacity FROM charge_data')
        rows = c.fetchall()
        conn.close()
        
        # 将数据转换为时间戳、功率、电压、容量列表（electric、money、orderId用默认值填充）
        if rows:
            timestamps, power, voltage, capacity = zip(*rows)
            # 对于旧数据，electric、money、orderId使用默认值
            return list(timestamps), list(power), list(voltage), [0]*len(timestamps), [0]*len(timestamps), [0]*len(timestamps)
        else:
            return [], [], [], [], [], []


# 创建 Plotly 图表
def create_chart():
    timestamps, power, voltage, electric, money, orderId = read_data_from_db()

    fig = go.Figure()

    # 添加Power曲线
    fig.add_trace(go.Scatter(x=timestamps, y=power, mode='lines', name='Power', line=dict(color='blue')))

    # 添加Voltage曲线
    fig.add_trace(go.Scatter(x=timestamps, y=voltage, mode='lines', name='Voltage', line=dict(color='red')))

    # 添加Electric曲线
    fig.add_trace(go.Scatter(x=timestamps, y=electric, mode='lines', name='Electric', line=dict(color='yellow')))

    # 添加Money曲线
    fig.add_trace(go.Scatter(x=timestamps, y=money, mode='lines', name='Money', line=dict(color='orange')))

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
    
    # 获取正在充电的订单 ID
    order_id = get_charging_order_id()

    # 启动定时数据获取线程
    import threading

    data_thread = threading.Thread(target=fetch_data_periodically, args=(order_id,), daemon=True)
    data_thread.start()

    # 启动 Flask 服务器
    app.run(debug=True, use_reloader=False)
