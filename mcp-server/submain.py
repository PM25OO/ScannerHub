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


mcp = FastMCP("submain_collect")

processes = {}

@mcp.prompt()
def pentest_expert_mode(domain: str) -> str:
    """
    进入渗透测试专家模式，针对特定域名进行全自动化的资产发现与风险评估。
    """
    return f"""
你现在是一名拥有 10 年经验的【资深渗透测试工程师】。
你的目标是完成针对域名 `{domain}` 的全面资产梳理。

### 你的行动准则：
1. **自主性**：如果用户让你“分析资产”，你应当自主调用 `submain_collect` 启动扫描，而不是询问用户是否开始。
2. **状态感知**：启动扫描后，你应该主动调用 `check_status` 观察进度。如果未完成，请告知用户预计等待时间，并引导用户在稍后继续。
3. **深度追溯**：一旦 `check_status` 返回成功，你必须立即自主调用 `search_db` 进行多维度分析。

### 你的分析路径（逻辑链）：
- **第一步：基础资产统计**。统计总子域名数、独立 IP 数。
- **第二步：敏感资产发现**。主动执行 SQL 查询那些包含 "admin", "test", "dev", "api", "v1" 等关键字的子域名。
- **第三步：风险评估**。查询那些指向了特定敏感服务或具有非 80/443 端口的资产。
- **第四步：总结报告**。不需要用户提醒，直接根据数据库内容输出一份资产分布报告。

### 限制：
- 始终以专业的、结构化的安全报告格式回答。
- 如果 SQL 执行报错，请根据错误信息尝试修正 SQL 并再次尝试，不要轻易放弃。

现在，请开始针对 `{domain}` 的渗透测试任务。
"""

@mcp.tool()
def test():
    """
    若其他工具出错，利用此工具测试能否正常运行子域收集脚本
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
    异步启动 OneForAll 扫描任务。
    立即返回启动状态，不会阻塞等待结果。
    
    Args:
        domain: 要扫描的目标主域名 (例如: example.com)
    """
    if domain in processes and processes[domain].poll() is None:
        return f"域名 {domain} 的扫描任务已经在运行中，请稍后检查。"
    try:
        proc = subprocess.Popen(
            [oneforall_python, oneforall_script, "--target", domain, "run"],
            cwd=oneforall_dir,
            stdout=subprocess.DEVNULL, # 避免输出塞满缓冲区
            stderr=subprocess.DEVNULL,
            start_new_session=True     # 在后台独立运行
        )
        processes[domain] = proc
        return f"🚀 已成功在后台启动对 {domain} 的扫描。请在 1-2 分钟后使用 search_db 工具查询结果。"
    except Exception as e:
        return f"❌ 启动失败: {str(e)}"
    
@mcp.tool()
def check_status(domain: str) -> str:
    """
    通过检查数据库中是否存在对应的结果表来确认扫描状态。
    OneForAll 完成后会生成一个名为 'domain_name' (点替换为下划线) 的表。
    
    Args:
        domain: 目标域名 (例如: example.com)
    """
    # 处理表名逻辑：将 example.com 转换为 example_com
    table_name = domain.replace('.', '_')

    # 检查数据库文件是否存在
    if not os.path.exists(oneforall_db):
        return f"数据库文件尚未生成。扫描任务可能仍在初始化，或尚未产生任何结果数据。"

    try:
        # 连接数据库查询元数据
        conn = sqlite3.connect(oneforall_db)
        cursor = conn.cursor()
        
        # 查询 sqlite_master 表来检查特定表名是否存在
        # sqlite_master 是 SQLite 的内置表，存储了所有表的信息
        sql_check = "SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
        cursor.execute(sql_check, (table_name,))
        result = cursor.fetchone()
        
        conn.close()

        # 4. 根据查询结果判断
        if result:
            return f"扫描已完成！\n数据库中已生成结果表: {table_name}\n你现在可以调用 search_db() 使用 SQL 语句来分析结果了。"
        else:
            return f"扫描任务仍在进行中...\n目标表 {table_name} 尚未在数据库中生成。请稍后再试。"

    except sqlite3.Error as e:
        return f"数据库查询出错: {str(e)}"
    
@mcp.tool()
def search_db(sql: str) -> str:
    """
    在 OneForAll 的 SQLite 数据库中执行 SQL 查询语句。
    你可以使用此工具来检索、过滤、统计已扫描到的子域名信息。
    
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