from app import mcp

@mcp.tool()
def dirsearch(domain: str) -> str:
    """
    使用 Dirsearch 工具对目标域名进行目录扫描，发现潜在的敏感目录和文件。

    Args:
        domain: 目标域名 (例如: example.com)

    Returns:
        扫描结果的摘要，包含发现的敏感目录和文件列表。
    """
    import subprocess

    dirsearch_script = "/path/to/dirsearch/dirsearch.py"  # 请替换为实际路径
    wordlist_path = "/path/to/wordlists/common.txt"  # 请替换为实际路径

    try:
        result = subprocess.run(
            ["python3", dirsearch_script, "-u", f"http://{domain}", "-w", wordlist_path, "--plain-text-report", "report.txt"],
            capture_output=True,
            text=True,
            timeout=300  # 设置超时时间为 5 分钟
        )

        if result.returncode != 0:
            return f"❌ Dirsearch 扫描失败: {result.stderr}"

        # 读取报告文件内容
        with open("report.txt", "r") as report_file:
            report_content = report_file.read()

        return f"✅ Dirsearch 扫描完成。报告内容:\n{report_content}"

    except subprocess.TimeoutExpired:
        return "❌ Dirsearch 扫描超时，请稍后重试。"
    except Exception as e:
        return f"❌ 扫描过程中发生错误: {str(e)}"