#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI代码安全审计系统 - 模块入口
支持 python -m ai_code_audit 调用方式
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入并运行主程序
from main import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
