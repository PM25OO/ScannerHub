from mcp.server.fastmcp import FastMCP
import os
import subprocess
import sqlite3

current_script_path = os.path.abspath(__file__)

mcp_server_dir = os.path.dirname(current_script_path)
oneforall_dir = os.path.abspath(os.path.join(mcp_server_dir, "..", "OneForAll"))
oneforall_python = os.path.join(oneforall_dir, ".venv", "bin", "python")
oneforall_script = os.path.join(oneforall_dir, "oneforall.py")
oneforall_db = os.path.join(oneforall_dir, "results", "result.sqlite3")

# subprocess.run([oneforall_python, oneforall_script, "--help"], cwd=oneforall_dir)

mcp = FastMCP("submain_collect")


@mcp.tool()
def test():
    """
    使用其它工具前，先测试能否正常运行子域收集脚本
    """
    result = subprocess.run(
        [oneforall_python, oneforall_script, "--help"],
        cwd=oneforall_dir,
        capture_output=True,
        text=True
    )
    output = result.stdout if result.stdout else result.stderr
    if output != '':
        return "✅ OneForAll 脚本运行正常。"
    else:
        return "❌ OneForAll 脚本运行异常，请检查环境配置。"

@mcp.tool()
def submain_collect(domain: str) -> str:
    """
    针对目标域名启动 OneForAll 子域名收集任务。
    这是一个耗时操作。该工具仅返回任务是否成功启动及执行状态。
    
    Args:
        domain: 要扫描的目标主域名 (例如: example.com)
    """
    try:
        # 执行 OneForAll 扫描命令
        # 注意：--show False 是为了减少不必要的输出，--fmt sqlite 是确保存入数据库
        result = subprocess.run(
            [oneforall_python, oneforall_script, "--target", domain, "run"],
            cwd=oneforall_dir,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
            timeout=600 # 设置 10 分钟超时，根据需求调整
        )

        if result.returncode == 0:
            return f"✅ 扫描任务完成：域名 {domain} 的结果已存入数据库。"
        else:
            return f"❌ 扫描任务失败 (Code {result.returncode})"

    except subprocess.TimeoutExpired:
        return f"⚠️ 扫描任务在 {domain} 上运行时间过长，已切入后台或被取消。"
    except Exception as e:
        return f"❌ 运行异常: {str(e)}"
    
@mcp.tool()
def search_db(sql: str) -> str:
    """
    在 OneForAll 的 SQLite 数据库中执行 SQL 查询语句。
    你可以使用此工具来检索、过滤、统计已扫描到的子域名信息。
    常用表名通常为 'result'。
    
    Args:
        sql: 标准 SQLite 查询语句 (例如: SELECT subdomain, ip FROM result WHERE subdomain LIKE '%admin%')
    """
    if not os.path.exists(oneforall_db):
        return f"❌ 数据库文件不存在：{oneforall_db}。请先执行扫描任务。"

    try:
        conn = sqlite3.connect(oneforall_db)
        cursor = conn.cursor()
        
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        # 获取列名
        column_names = [description[0] for description in cursor.description]
        
        conn.close()

        if not rows:
            return "查无结果。"

        # 格式化输出结果
        output = [f"| {' | '.join(column_names)} |"]
        output.append("|" + "---|" * len(column_names))
        for row in rows[:50]: # 限制返回前 50 条，避免内容过多超出 Claude 上下文
            output.append(f"| {' | '.join(map(str, row))} |")
        
        if len(rows) > 50:
            output.append(f"\n注：结果过多，已省略后 {len(rows)-50} 条。")

        return "\n".join(output)

    except sqlite3.Error as e:
        return f"❌ SQL 执行错误: {str(e)}"