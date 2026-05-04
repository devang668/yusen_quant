"""
钱包管理模拟服务
每个钱包对应一个独立的 JSON 文件
"""

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
import json
import os
import time
import random
import shutil

app = Flask(__name__)
CORS(app)

WALLETS_DIR = os.path.join(os.path.dirname(__file__), 'wallets')
DEFAULT_USDT = 10000.0
DEFAULT_ETH = 0.0

os.makedirs(WALLETS_DIR, exist_ok=True)

def get_eth_price():
    return round(random.uniform(2800, 3200), 2)

def generate_address():
    return '0x' + ''.join(random.choices('0123456789abcdef', k=40))

def generate_private_key():
    return '0x' + ''.join(random.choices('0123456789abcdef', k=64))

def wallet_file(address):
    return os.path.join(WALLETS_DIR, f"{address}.json")

def load_wallet(address):
    fpath = wallet_file(address)
    if os.path.exists(fpath):
        with open(fpath, 'r') as f:
            return json.load(f)
    return None

def save_wallet(wallet):
    fpath = wallet_file(wallet['address'])
    with open(fpath, 'w') as f:
        json.dump(wallet, f, indent=2)

def list_wallets():
    wallets = []
    for fname in os.listdir(WALLETS_DIR):
        if fname.endswith('.json'):
            fpath = os.path.join(WALLETS_DIR, fname)
            with open(fpath, 'r') as f:
                wallets.append(json.load(f))
    return wallets

# ============================================================
# 钱包接口
# ============================================================

@app.route('/')
def index():
    return send_file("index.html")

@app.route('/api/wallets')
def get_wallets():
    """获取所有钱包列表"""
    wallets = list_wallets()
    eth_price = get_eth_price()
    result = []
    for w in wallets:
        total = w.get('usdt', 0) + w.get('eth', 0) * eth_price
        result.append({
            "address": w['address'],
            "usdt": w.get('usdt', 0),
            "eth": w.get('eth', 0),
            "eth_price": eth_price,
            "total_value": round(total, 2),
            "created_at": w.get('created_at', 0)
        })
    result.sort(key=lambda x: x['total_value'], reverse=True)
    return jsonify(result)

@app.route('/api/wallet', methods=['POST'])
def create_wallet():
    """创建新钱包（生成独立JSON文件）"""
    new_wallet = {
        "address": generate_address(),
        "private_key": generate_private_key(),
        "usdt": DEFAULT_USDT,
        "eth": DEFAULT_ETH,
        "created_at": int(time.time() * 1000),
        "transactions": []
    }
    save_wallet(new_wallet)
    return jsonify({
        "address": new_wallet['address'],
        "private_key": new_wallet['private_key'],
        "usdt": new_wallet['usdt'],
        "eth": new_wallet['eth'],
        "created_at": new_wallet['created_at'],
        "message": "钱包创建成功，已保存为独立文件"
    })

@app.route('/api/wallet/<address>')
def get_wallet(address):
    """获取单个钱包"""
    w = load_wallet(address)
    if not w:
        return jsonify({"error": "钱包不存在"}), 404
    eth_price = get_eth_price()
    total = w.get('usdt', 0) + w.get('eth', 0) * eth_price
    return jsonify({
        "address": w['address'],
        "usdt": w.get('usdt', 0),
        "eth": w.get('eth', 0),
        "eth_price": eth_price,
        "total_value": round(total, 2),
        "created_at": w.get('created_at', 0),
        "transactions": w.get('transactions', [])
    })

# ============================================================
# 交易接口
# ============================================================

@app.route('/api/buy', methods=['POST'])
def buy_eth():
    """买入ETH"""
    body = request.json
    address = body.get('address')
    usdt_amount = float(body.get('usdt_amount', 0))

    if not address or usdt_amount <= 0:
        return jsonify({"error": "参数错误"}), 400

    w = load_wallet(address)
    if not w:
        return jsonify({"error": "钱包不存在"}), 404
    if w.get('usdt', 0) < usdt_amount:
        return jsonify({"error": "USDT余额不足"}), 400

    eth_price = get_eth_price()
    eth_amount = round(usdt_amount / eth_price, 6)

    w['usdt'] -= usdt_amount
    w['eth'] += eth_amount

    tx = {
        "id": len(w.get('transactions', [])) + 1,
        "type": "BUY",
        "amount": eth_amount,
        "price": eth_price,
        "cost": usdt_amount,
        "time": int(time.time() * 1000)
    }
    w.setdefault('transactions', []).append(tx)
    save_wallet(w)

    return jsonify({
        "message": "买入成功",
        "bought_eth": eth_amount,
        "spent_usdt": usdt_amount,
        "eth_price": eth_price,
        "wallet_usdt": w['usdt'],
        "wallet_eth": w['eth']
    })

@app.route('/api/sell', methods=['POST'])
def sell_eth():
    """卖出ETH"""
    body = request.json
    address = body.get('address')
    eth_amount = float(body.get('eth_amount', 0))

    if not address or eth_amount <= 0:
        return jsonify({"error": "参数错误"}), 400

    w = load_wallet(address)
    if not w:
        return jsonify({"error": "钱包不存在"}), 404
    if w.get('eth', 0) < eth_amount:
        return jsonify({"error": "ETH余额不足"}), 400

    eth_price = get_eth_price()
    usdt_amount = round(eth_amount * eth_price, 2)

    w['eth'] -= eth_amount
    w['usdt'] += usdt_amount

    tx = {
        "id": len(w.get('transactions', [])) + 1,
        "type": "SELL",
        "amount": eth_amount,
        "price": eth_price,
        "earned": usdt_amount,
        "time": int(time.time() * 1000)
    }
    w.setdefault('transactions', []).append(tx)
    save_wallet(w)

    return jsonify({
        "message": "卖出成功",
        "sold_eth": eth_amount,
        "earned_usdt": usdt_amount,
        "eth_price": eth_price,
        "wallet_usdt": w['usdt'],
        "wallet_eth": w['eth']
    })

@app.route('/api/transfer', methods=['POST'])
def transfer():
    """USDT转账"""
    body = request.json
    from_addr = body.get('from')
    to_addr = body.get('to')
    amount = float(body.get('amount', 0))

    if not from_addr or not to_addr or amount <= 0:
        return jsonify({"error": "参数错误"}), 400

    from_w = load_wallet(from_addr)
    to_w = load_wallet(to_addr)

    if not from_w:
        return jsonify({"error": "发送钱包不存在"}), 404
    if not to_w:
        return jsonify({"error": "接收钱包不存在"}), 404
    if from_w == to_w:
        return jsonify({"error": "不能给自己转账"}), 400
    if from_w.get('usdt', 0) < amount:
        return jsonify({"error": "USDT余额不足"}), 400

    from_w['usdt'] -= amount
    to_w['usdt'] += amount

    tx_from = {"id": len(from_w.get('transactions', [])) + 1, "type": "TRANSFER_OUT", "to": to_addr, "amount": amount, "time": int(time.time() * 1000)}
    tx_to = {"id": len(to_w.get('transactions', [])) + 1, "type": "TRANSFER_IN", "from": from_addr, "amount": amount, "time": int(time.time() * 1000)}

    from_w.setdefault('transactions', []).append(tx_from)
    to_w.setdefault('transactions', []).append(tx_to)

    save_wallet(from_w)
    save_wallet(to_w)

    return jsonify({"message": "转账成功", "tx": tx_from})

@app.route('/api/wallet/<address>', methods=['DELETE'])
def delete_wallet(address):
    """删除钱包"""
    fpath = wallet_file(address)
    if not os.path.exists(fpath):
        return jsonify({"error": "钱包不存在"}), 404
    os.remove(fpath)
    return jsonify({"message": "钱包已删除", "address": address})

# ============================================================
# 市场
# ============================================================

@app.route('/api/market/price')
def market_price():
    return jsonify({
        "symbol": "ETHUSDT",
        "price": get_eth_price(),
        "time": int(time.time() * 1000)
    })

# ============================================================
# 启动
# ============================================================

if __name__ == '__main__':
    print("=" * 50)
    print("  钱包管理服务已启动")
    print("  访问地址：http://127.0.0.1:5001")
    print("  钱包文件目录：wallets/")
    print("  每个钱包对应一个 .json 文件")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5001, debug=True)
