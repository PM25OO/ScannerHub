from app import mcp
import os
import subprocess
import sqlite3
import platform

current_script_path = os.path.abspath(__file__)

mcp_server_dir = os.path.dirname(current_script_path)
oneforall_dir = os.path.abspath(os.path.join(mcp_server_dir, "..", "OneForAll"))

# 根据平台动态确定Python虚拟环境路径
if platform.system() == "Windows":
    oneforall_python = os.path.join(oneforall_dir, ".venv", "Scripts", "python.exe")
else:
    oneforall_python = os.path.join(oneforall_dir, ".venv", "bin", "python")

oneforall_script = os.path.join(oneforall_dir, "oneforall.py")
oneforall_db = os.path.join(oneforall_dir, "results", "result.sqlite3")


processes = {}

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
        # Windows和Linux平台的进程启动方式不同
        if platform.system() == "Windows":
            # Windows平台：使用CREATE_NEW_PROCESS_GROUP启动独立进程
            proc = subprocess.Popen(
                [oneforall_python, oneforall_script, "--target", domain, "run"],
                cwd=oneforall_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
            )
        else:
            # Linux/Mac平台：使用start_new_session启动独立会话
            proc = subprocess.Popen(
                [oneforall_python, oneforall_script, "--target", domain, "run"],
                cwd=oneforall_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        processes[domain] = proc
        return f"🚀 已成功在后台启动对 {domain} 的扫描。请在 1-2 分钟后使用 search_db 工具查询结果。"
    except Exception as e:
        return f"❌ 启动失败: {str(e)}"
    
@mcp.tool()
def check_ofa_status(domain: str) -> str:
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
        # 连接数据库查询元数据，添加超时防止锁定
        conn = sqlite3.connect(oneforall_db, timeout=10.0)
        cursor = conn.cursor()
        
        # 查询 sqlite_master 表来检查特定表名是否存在
        # sqlite_master 是 SQLite 的内置表，存储了所有表的信息
        sql_check = "SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
        cursor.execute(sql_check, (table_name,))
        result = cursor.fetchone()
        
        conn.close()

        # 根据查询结果判断
        if result:
            return f"✅ 扫描已完成！\n数据库中已生成结果表: {table_name}\n你现在可以调用 search_db() 使用 SQL 语句来分析结果了。"
        else:
            return f"⏳ 扫描任务仍在进行中...\n目标表 {table_name} 尚未在数据库中生成。请稍后再试。"

    except sqlite3.OperationalError as e:
        if "locked" in str(e).lower():
            return f"⏳ 数据库被锁定，扫描仍在进行中。请稍后再试。"
        return f"❌ 数据库操作出错: {str(e)}"
    except sqlite3.Error as e:
        return f"❌ 数据库查询出错: {str(e)}"
    
@mcp.tool()
def search_db(sql: str) -> str:
    """
    在 OneForAll 的 SQLite 数据库中执行 SQL 查询语句。
    你可以使用此工具来检索、过滤、统计已扫描到的子域名信息。
    以下为表中部分字段说明：

    id: 标识作用无意义

    new: 标记是否是新发现的子域名
    
    alive: 是否存活，不存活的判定情况包含：无法解析IP、网络不可达、400、5XX等
    
    request: 记录HTTP请求是否成功字段，为空是无法解析IP，为0是网络不可达，为1是成功请求
    
    resolve: 记录DNS解析是否成功
    
    url: 请求的url链接
    
    subdomain: 子域名
    
    level: 是几级子域名
    
    cname: cname记录
    
    ip: 解析到的IP
    
    public: 是否是公网IP
    
    cdn: 解析的IP是否CDN
    
    port: 请求的网络端口
    
    status: HTTP响应的状态码
    
    reason: 网络连接情况及详情
    
    title: 网站标题
    
    banner: 网站指纹信息
    
    history: 请求时URL跳转历史
    
    response: 响应体文本内容
    
    times: 在爆破中ip重复出现的次数
    
    ttl: DNS解析返回的TTL值
    
    cidr: ip2location库查询出的CIDR
    
    asn: ip2location库查询出的ASN
    
    addr: ip2region库查询出的物理地址
    
    isp: ip2region库查询出的网络服务提供商
    
    resolver: 所使用的DNS解析服务器
    
    module: 发现本子域名所使用的模块
    
    source: 发现本子域名的具体来源
    
    elapse: 当前模块发现用时
    
    find: 当前模块发现的子域个数
    
    Args:
        sql: 标准 SQLite 查询语句 (例如: SELECT subdomain, ip FROM result WHERE subdomain LIKE '%admin%')
    """
    if not os.path.exists(oneforall_db):
        return f"❌ 数据库文件不存在：{oneforall_db}。请先执行扫描任务。"

    try:
        # 添加超时和只读模式防止锁定和争用
        conn = sqlite3.connect(f"file:{oneforall_db}?mode=ro", timeout=10.0, uri=True)
        cursor = conn.cursor()
        
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        # 获取列名
        column_names = [description[0] for description in cursor.description] if cursor.description else []
        
        conn.close()

        if not rows:
            return "查无结果。"

        # 格式化输出结果
        output = []
        if column_names:
            output.append(f"| {' | '.join(column_names)} |")
            output.append("|" + "---|" * len(column_names))
        
        for row in rows[:50]: # 限制返回前 50 条，避免内容过多超出 Claude 上下文
            output.append(f"| {' | '.join(map(str, row))} |")
        
        if len(rows) > 50:
            output.append(f"\n注：结果过多，已省略后 {len(rows)-50} 条。")

        return "\n".join(output)

    except sqlite3.OperationalError as e:
        if "readonly" in str(e).lower():
            # 降级方案：使用普通连接模式
            try:
                conn = sqlite3.connect(oneforall_db, timeout=10.0)
                cursor = conn.cursor()
                cursor.execute(sql)
                rows = cursor.fetchall()
                column_names = [description[0] for description in cursor.description] if cursor.description else []
                conn.close()
                
                if not rows:
                    return "查无结果。"
                
                output = []
                if column_names:
                    output.append(f"| {' | '.join(column_names)} |")
                    output.append("|" + "---|" * len(column_names))
                
                for row in rows[:50]:
                    output.append(f"| {' | '.join(map(str, row))} |")
                
                if len(rows) > 50:
                    output.append(f"\n注：结果过多，已省略后 {len(rows)-50} 条。")
                
                return "\n".join(output)
            except Exception as fallback_error:
                return f"❌ 数据库访问出错: {str(fallback_error)}"
        else:
            return f"❌ SQL 执行错误: {str(e)}"
    except sqlite3.Error as e:
        return f"❌ SQL 执行错误: {str(e)}"