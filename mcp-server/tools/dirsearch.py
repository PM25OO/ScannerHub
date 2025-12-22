from app import mcp
import os
import platform
import subprocess

mcp_server_dir = os.path.dirname(os.path.dirname(__file__))
dsr_dir = os.path.abspath(os.path.join(mcp_server_dir, ".venv", "Lib", "site-packages", "dirsearch"))
dsr_script = os.path.join(dsr_dir, "dirsearch.py")
dsr_output = os.path.join(dsr_dir, "reports")

if platform.system() == "Windows":
    python_executable = os.path.join(mcp_server_dir, ".venv", "Scripts", "python.exe")
else:
    python_executable = os.path.join(mcp_server_dir, ".venv", "bin", "python")


@mcp.tool()
def dirsearch(domain: str) -> str:
    """
    使用 Dirsearch 工具对目标域名进行目录扫描，发现潜在的敏感目录和文件。
    异步启动 Dirsearch 扫描任务。

    Args:
        domain: 目标域名 (例如: example.com)

    Returns:
        任务启动状态信息。
    """
    if not domain or not domain.strip():
        return "域名不能为空。"

    target = domain.strip()
    if not target.startswith(("http://", "https://")):
        target = f"http://{target}"

    domain_underscored = domain.replace(".", "_")
    output_file = os.path.join(dsr_output, f"{domain_underscored}.md")

    if not os.path.isfile(python_executable):
        return f"找不到虚拟环境解释器: {python_executable}"

    if not os.path.isfile(dsr_script):
        return f"找不到 dirsearch 脚本: {dsr_script}"

    os.makedirs(dsr_output, exist_ok=True)

    cmd = [
        python_executable,
        dsr_script,
        "-u",
        target,
        "-o",
        output_file,
        "--format=md",
    ]

    creation_flags = 0
    if platform.system() == "Windows":
        creation_flags = subprocess.CREATE_NEW_CONSOLE

    try:
        subprocess.Popen(
            cmd,
            cwd=dsr_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            creationflags=creation_flags,
        )
    except Exception as exc:  # pragma: no cover - defensive: keep simple
        return f"启动 dirsearch 失败: {exc}"

    return (
        f"已启动 dirsearch 扫描: {domain}，输出文件: {output_file}。"
        " 请稍后使用 check_dsr_status() 查询状态。"
    )

@mcp.tool()
def check_dsr_status(domain: str) -> str:
    """
    检查output文件夹下是否存在指定域名的扫描结果。
    dirsearch 扫描完成后会生成一个名为'example_com.md'(点替换为下划线)的Markdown文件。

    Args:
        domain: 目标域名 (例如: example.com)

    Returns:
        结果文件是否存在的状态信息。
    """
    if not domain or not domain.strip():
        return "域名不能为空。"

    domain_underscored = domain.replace(".", "_")
    output_file = os.path.join(dsr_output, f"{domain_underscored}.md")

    if os.path.exists(output_file):
        return f"已找到扫描结果: {output_file}"  

    return "未找到扫描结果，任务可能仍在运行或尚未启动。"

@mcp.resource("mcp://reports/{domain_underscored}.md")
def get_report(domain_underscored: str) -> str:
    """
    按需读取指定的扫描报告内容
    
    Args:
        domain_underscored: 目标域名，点替换为下划线 (例如: example_com)
    """
    report_path = os.path.join(dsr_output, f"{domain_underscored}.md")
    try:
        with open(report_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return "Dirsearch 扫描结果尚未生成，请使用 check_dsr_status() 工具确认扫描状态。"