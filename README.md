# Scan_Tool 

( 开发中... )

### 致谢

子域收集：[shmilylty/OneForAll](https://github.com/shmilylty/OneForAll)  

路径发现：[maurosoria/dirsearch](https://github.com/maurosoria/dirsearch)

### 目录结构

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

### 环境搭建

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

### TODO
- [x] 环境搭建
- [ ] 子域收集功能
- [ ] 空间测绘功能
- [ ] 指纹识别功能
- [ ] 路径发现功能 
