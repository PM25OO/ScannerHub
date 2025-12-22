# ScannerHub-渗透一把梭

<div style="width: 100%; max-width: 600px; margin: 0 auto;">
  <img src="logo.png" alt="ScannerHub Logo" style="width: 100%; height: auto; display: block; margin: 0 auto;">
</div>

--- 

~~(开始画饼)~~ 一款基于 LLM 驱动，综合了情报收集，威胁建模，漏洞分析，漏洞利用，后渗透攻击，报告与修复的 MCP 服务器。相比传统 Agent 模式，其跨平台互操作性，安全性与权限控制更具优势

## 致谢

子域收集：[shmilylty/OneForAll](https://github.com/shmilylty/OneForAll)  

路径发现：[maurosoria/dirsearch](https://github.com/maurosoria/dirsearch)

开发SDK：[modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)

## 目录结构

``````Plaintext
/Scan_Tool/
├── OneForAll/              # 子域收集脚本
│   ├── .venv/              # Python 3.8
│   ├── oneforall.py
│   └── ...
└── mcp-server/             # MCP Server
    ├── .venv/              # Python 3.12
    ├── mcp_server.py
    ├── pyproject.toml
    └── ...
``````

## 环境搭建

此项目使用 `uv` 进行管理

```Plaintext
# 渗透相关工具环境
cd ./OneForAll/
uv venv --python 3.8
source .venv/bin/activate
uv pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 检查环境
./oneforall.py --help

# mcp服务器环境
cd .mcp-server/
uv sync
```

## 从 JSON 导入MCP服务器
以vscode的 `mcp.json` 为例  
```json
{
    "servers": {
        "Scanner_Hub": {
            "command": "uv",           // Windows环境下可能需要替换为绝对路径
            "args": [
                "--directory",
                "PATH/TO/mcp-server",  // mcp-server文件夹的路径
                "run",
                "python",
                "-u",
                "main.py"
            ],
            "env": {
                "PYTHONUNBUFFERED": "1"
            }
        }
    }
}
```

## 原语汇总
### Tools
| 名称 | 参数 | 功能描述 |
| --- | --- | --- |
| test | 无 | 验证 OneForAll 脚本环境是否可用。 |
| submain_collect | domain: 目标主域名 | 异步启动 OneForAll 子域名收集任务。 |
| check_ofa_status | domain: 目标主域名 | 检查 OneForAll 结果表是否生成，判断任务是否完成。 |
| get_db_schema | 无 | 查看 OneForAll 结果库的表结构。 |
| search_db | sql: SQL 查询语句 | 在 OneForAll 结果库中执行查询，支持筛选/统计。 |
| dirsearch | domain: 目标域名/URL | 异步启动 dirsearch 目录扫描，生成 Markdown 报告。 |
| check_dsr_status | domain: 目标域名/URL | 检查 dirsearch 报告是否生成。 |

### Prompts
| 名称 | 参数 | 功能描述 |
| --- | --- | --- |
| pentest_expert_mode | domain：目标域名 | 进入渗透测试专家模式 |

### Resources
| 名称 | 参数 | 功能描述 |
| --- | --- | --- |
| get_report | domain_underscored | 读取指定域名的 dirsearch Markdown 扫描报告内容。 |

## TODO
- [x] 环境搭建
- [x] 子域收集功能
- [ ] 空间测绘功能
- [x] 指纹识别功能
- [x] 路径发现功能 
