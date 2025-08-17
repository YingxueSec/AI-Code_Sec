# AI Code Audit System - 架构图表

本目录包含AI代码审计系统的各种架构图表，使用Mermaid格式编写。

## 📋 图表列表

### 1. 会话管理架构图
**文件**: `session_management_architecture.mmd`
**描述**: 展示完整的会话管理架构，包括用户层、审计引擎、会话层、隔离上下文、共享资源层和项目层的关系。

**主要内容**:
- 用户与会话的关系
- 双层会话管理架构 (SessionManager + SessionIsolationManager)
- 会话隔离环境的具体实现
- 共享资源的访问控制

### 2. 会话概念图
**文件**: `session_concept.mmd`
**描述**: 简化的会话概念说明图，解释"一个会话 = 一次项目审计任务"的核心概念。

**主要内容**:
- 会话的四个核心特征
- 会话示例展示
- 隔离环境内容
- 共享资源类型

### 3. 会话生命周期状态图
**文件**: `session_lifecycle.mmd`
**描述**: 展示会话从创建到销毁的完整生命周期状态转换。

**主要内容**:
- 会话状态转换流程
- 各状态的具体操作
- 异常处理和清理机制

### 4. 会话管理时序图
**文件**: `session_sequence.mmd`
**描述**: 详细的会话管理操作时序图，展示各组件间的交互流程。

**主要内容**:
- 会话创建流程
- 审计执行流程
- 并发会话处理
- 会话暂停/恢复
- 资源清理流程

## 🔧 如何使用这些图表

### 在线查看
可以将.mmd文件内容复制到以下在线工具中查看：
- [Mermaid Live Editor](https://mermaid.live/)
- [GitHub](https://github.com) (直接支持Mermaid渲染)

### 本地渲染
使用Mermaid CLI工具将图表转换为SVG或PNG格式：

```bash
# 安装Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# 转换为SVG
mmdc -i session_management_architecture.mmd -o session_management_architecture.svg

# 转换为PNG
mmdc -i session_management_architecture.mmd -o session_management_architecture.png
```

### 在文档中引用
在Markdown文档中可以直接引用：

```markdown
```mermaid
graph TB
    # 将.mmd文件内容粘贴到这里
```
```

## 📖 相关文档

- [会话管理设计文档](../docs/session_management.md)
- [系统架构文档](../README_Development.md)
- [API文档](../docs/api.md)

## 🔄 更新说明

这些图表会随着系统架构的演进而更新。如果发现图表与实际实现不符，请及时更新。

### 更新历史
- 2024-01-XX: 初始版本，包含会话管理相关的4个核心图表
- 待更新...

## 💡 贡献指南

如果需要添加新的图表或修改现有图表：

1. 使用Mermaid语法编写图表
2. 确保图表清晰易懂
3. 添加适当的注释和说明
4. 更新本README文件
5. 测试图表在各种渲染器中的显示效果

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 创建Issue
- 提交Pull Request
- 发送邮件至项目维护者
