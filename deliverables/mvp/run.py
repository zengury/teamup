#!/usr/bin/env python3
"""
SweetLoaf AI 组织转型系统 — 入口文件

启动方式:
    python run.py                  # 开发模式（默认端口 9527）
    python run.py --mock           # 模拟模式（无需外部API）
    PORT=8888 python run.py       # 指定端口
"""
import sys
import os
import socket

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()


def find_available_port(start_port: int) -> int:
    """从 start_port 开始找第一个可用端口"""
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(("0.0.0.0", port))
            if result != 0:
                return port
            port += 1


def print_routes():
    """打印所有已注册的路由"""
    rules = []
    for rule in app.url_map.iter_rules():
        methods = ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))
        if methods:
            rules.append((methods, rule.rule, rule.endpoint))
    print(f"  ┌─ 已注册路由 ({len(rules)} 条)")
    for methods, rule, endpoint in sorted(rules, key=lambda x: x[1]):
        print(f"  │  {methods:6s}  {rule:40s}  {endpoint}")
    print(f"  └─")


if __name__ == "__main__":
    # 检查命令行参数
    if "--mock" in sys.argv:
        os.environ["MOCK_MODE"] = "True"
        print("🧪 模拟模式启动中...")
    else:
        print("🍞 SweetLoaf AI 组织转型系统启动中...")

    # 确定端口
    default_port = int(os.environ.get("SWEETLOAF_PORT", 9527))
    port = find_available_port(default_port)

    if port != default_port:
        print(f"  ⚠️  端口 {default_port} 已被占用，自动切换至端口 {port}")

    host = os.environ.get("HOST", "0.0.0.0")
    debug = os.environ.get("DEBUG", "True").lower() == "true"

    print()
    print(f"  ✨ SweetLoaf 系统已启动！")
    print(f"  📍 访问地址: http://localhost:{port}/")
    print()
    print_routes()
    print()

    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
        )
    except KeyboardInterrupt:
        print()
        print("  👋 SweetLoaf 系统已关闭。再见！")
        sys.exit(0)
