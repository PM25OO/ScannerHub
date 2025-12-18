import os
import subprocess

# 1. 获取当前脚本文件（即 mcp-server 里的脚本）的绝对路径
current_script_path = os.path.abspath(__file__)

# 2. 获取 mcp-server 的目录路径
mcp_server_dir = os.path.dirname(current_script_path)

# 3. 通过相对关系定位到 OneForAll 的目录
# 假设目录结构是：
# Project/
# ├── OneForAll/
# └── mcp-server/
oneforall_dir = os.path.abspath(os.path.join(mcp_server_dir, "..", "OneForAll"))

# 4. 定位 OneForAll 的解释器和脚本
oneforall_python = os.path.join(oneforall_dir, ".venv", "bin", "python")
oneforall_script = os.path.join(oneforall_dir, "oneforall.py")


# 使用计算出的路径执行
subprocess.run([oneforall_python, oneforall_script, "--help"], cwd=oneforall_dir)