# Work Plan: AI Harness 全面改进

**Plan ID**: ai-harness-improvement  
**Created**: 2026-03-04  
**Status**: READY  
**Owner**: User  
**Executor**: Sisyphus

---

## 1. Overview

### 1.1 Goal
全面改进 AI Harness 项目，创建一个支持插件化架构的跨平台自动化开发框架，支持多种 AI 编码工具运行时选择。

### 1.2 Scope
- **In Scope**:
  - 插件化架构设计，支持多 AI 工具
  - 跨平台兼容性改进
  - 配置管理系统
  - 进度跟踪和报告功能
  - 错误处理和重试机制
  - 模块化代码重构
  
- **Out of Scope**:
  - 单元测试 (用户明确不需要)
  - Web UI / API 服务
  - 全新重写 (采用渐进迁移)
  - 极简依赖 (允许使用轻量库)

### 1.3 Key Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| 架构策略 | 渐进迁移 | 保持向后兼容，降低风险 |
| AI 工具支持 | 插件化架构 | 支持运行时选择，灵活扩展 |
| 平台优先级 | 跨平台优先 | Windows/Mac/Linux 同等支持 |
| CLI 风格 | 保持简洁 | 渐进优化，不破坏现有体验 |
| 功能范围 | 核心 + 报告 | 满足核心需求，不过度扩展 |
| 依赖策略 | 轻量外部库 | 使用 Click, PyYAML 等成熟库 |
| 测试策略 | 不需要 | 用户明确不需要测试 |

---

## 2. Work Breakdown

### Phase 1: 架构设计 (Architecture Design)

#### Task 1.1: 插件系统核心设计
**Priority**: HIGH | **Estimate**: 4h | **Category**: ultrabrain

**Description**: 设计插件化架构的核心接口和抽象层

**Acceptance Criteria**:
- [ ] 定义 AI 工具插件接口 (BaseAIProvider)
- [ ] 设计插件注册和发现机制
- [ ] 设计配置驱动的插件选择机制
- [ ] 确保现有 iFlow 功能可平滑迁移

**Deliverables**:
- `ai_harness/providers/base.py` - 基础接口定义
- `ai_harness/providers/registry.py` - 插件注册中心
- 架构设计文档

**Dependencies**: None

---

#### Task 1.2: 项目结构重组
**Priority**: HIGH | **Estimate**: 2h | **Category**: quick

**Description**: 重组项目目录结构，建立模块化基础

**Acceptance Criteria**:
- [ ] 创建 `ai_harness/` 包目录
- [ ] 创建子模块目录结构
- [ ] 保持向后兼容性 (保留原有入口点)
- [ ] 更新 package.json 和 setup 配置

**Deliverables**:
```
ai_harness/
├── __init__.py
├── cli/
├── core/
├── providers/
├── config/
├── report/
└── utils/
```

**Dependencies**: Task 1.1

---

#### Task 1.3: 配置系统设计
**Priority**: HIGH | **Estimate**: 3h | **Category**: unspecified-low

**Description**: 设计统一的配置管理系统

**Acceptance Criteria**:
- [ ] 定义配置文件格式 (YAML)
- [ ] 支持多级配置 (全局/项目/用户)
- [ ] 配置验证和默认值处理
- [ ] 环境变量覆盖支持

**Deliverables**:
- `ai_harness/config/manager.py`
- `ai_harness/config/schema.py`
- 配置文件模板

**Dependencies**: Task 1.2

---

### Phase 2: 核心重构 (Core Refactoring)

#### Task 2.1: iFlow Provider 实现
**Priority**: HIGH | **Estimate**: 5h | **Category**: deep

**Description**: 将现有 iFlow 集成重构为 Provider 插件

**Acceptance Criteria**:
- [ ] 实现 iFlowProvider 类
- [ ] 封装 iFlow CLI 调用逻辑
- [ ] 添加错误处理和重试机制
- [ ] 保持与现有功能 100% 兼容

**Deliverables**:
- `ai_harness/providers/iflow/provider.py`
- `ai_harness/providers/iflow/executor.py`

**Dependencies**: Task 1.1, Task 1.2

---

#### Task 2.2: 任务调度器重构
**Priority**: HIGH | **Estimate**: 6h | **Category**: deep

**Description**: 重构任务调度器，支持插件化 Provider

**Acceptance Criteria**:
- [ ] 解耦调度逻辑和 Provider 实现
- [ ] 支持任务依赖图解析
- [ ] 添加任务状态管理
- [ ] 支持并发任务执行 (可选)

**Deliverables**:
- `ai_harness/core/scheduler.py`
- `ai_harness/core/task_manager.py`

**Dependencies**: Task 2.1

---

#### Task 2.3: 跨平台路径处理
**Priority**: MEDIUM | **Estimate**: 3h | **Category**: quick

**Description**: 移除所有硬编码路径，使用跨平台兼容的路径处理

**Acceptance Criteria**:
- [ ] 移除所有 Windows 特定路径硬编码
- [ ] 使用 `pathlib` 进行路径操作
- [ ] 添加平台特定的工具发现逻辑
- [ ] 在 Windows/Mac/Linux 上验证

**Deliverables**:
- `ai_harness/utils/platform.py`
- 更新所有路径相关代码

**Dependencies**: Task 1.2

---

### Phase 3: 功能增强 (Feature Enhancement)

#### Task 3.1: 报告生成系统
**Priority**: MEDIUM | **Estimate**: 4h | **Category**: unspecified-low

**Description**: 实现进度跟踪和报告生成功能

**Acceptance Criteria**:
- [ ] 结构化进度数据存储 (JSON)
- [ ] 支持多种报告格式 (文本/JSON/HTML)
- [ ] 任务执行统计汇总
- [ ] 可自定义报告模板

**Deliverables**:
- `ai_harness/report/tracker.py`
- `ai_harness/report/generator.py`
- 报告模板

**Dependencies**: Task 2.2

---

#### Task 3.2: 错误处理增强
**Priority**: HIGH | **Estimate**: 3h | **Category**: unspecified-low

**Description**: 添加完善的错误处理和重试机制

**Acceptance Criteria**:
- [ ] 分级错误类型定义
- [ ] 可配置的重试策略
- [ ] 优雅降级处理
- [ ] 详细的错误日志

**Deliverables**:
- `ai_harness/core/errors.py`
- `ai_harness/core/retry.py`

**Dependencies**: Task 2.2

---

#### Task 3.3: CLI 现代化
**Priority**: LOW | **Estimate**: 4h | **Category**: visual-engineering

**Description**: 使用 Click 框架现代化 CLI，保持简洁风格

**Acceptance Criteria**:
- [ ] 使用 Click 替代 argparse
- [ ] 保持现有命令接口不变
- [ ] 添加彩色输出支持
- [ ] 改进帮助信息

**Deliverables**:
- `ai_harness/cli/main.py`
- `ai_harness/cli/commands/`

**Dependencies**: Task 2.2

---

### Phase 4: 集成与迁移 (Integration & Migration)

#### Task 4.1: 向后兼容层
**Priority**: HIGH | **Estimate**: 3h | **Category**: unspecified-low

**Description**: 确保现有用户无缝迁移

**Acceptance Criteria**:
- [ ] 保留原有 CLI 入口点
- [ ] 支持 feature_list.json 旧格式
- [ ] 自动迁移机制
- [ ] 迁移文档

**Deliverables**:
- 兼容性适配器
- 迁移指南

**Dependencies**: Task 2.2

---

#### Task 4.2: 文档更新
**Priority**: MEDIUM | **Estimate**: 4h | **Category**: writing

**Description**: 更新项目文档

**Acceptance Criteria**:
- [ ] README 更新
- [ ] 架构文档
- [ ] 插件开发指南
- [ ] 迁移指南

**Deliverables**:
- 更新的文档文件

**Dependencies**: All previous tasks

---

#### Task 4.3: 示例 Provider
**Priority**: LOW | **Estimate**: 3h | **Category**: unspecified-low

**Description**: 提供示例 Provider 实现，演示插件系统

**Acceptance Criteria**:
- [ ] Claude Code Provider 示例 (存根)
- [ ] Cursor Provider 示例 (存根)
- [ ] 插件开发模板

**Deliverables**:
- `ai_harness/providers/claude/`
- `ai_harness/providers/cursor/`

**Dependencies**: Task 2.1

---

## 3. Execution Strategy

### 3.1 Parallelization Opportunities
- **Phase 1**: Task 1.1 和 Task 1.2 可并行启动
- **Phase 2**: Task 2.1 完成后，Task 2.2 和 Task 2.3 可并行
- **Phase 3**: 所有任务可并行执行
- **Phase 4**: Task 4.1 和 Task 4.3 可并行

### 3.2 Critical Path
```
1.1 → 1.2 → 1.3 → 2.1 → 2.2 → 2.3 → 3.1 → 4.1 → 4.2
                              ↘ 3.2 ↘ 3.3 → 4.3
```

**Critical Path Duration**: ~35h (估算)

### 3.3 Risk Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| 向后兼容性破坏 | HIGH | 保留旧入口点，添加兼容层 |
| 插件设计不当 | MEDIUM | 先实现 iFlow Provider 验证设计 |
| 性能下降 | LOW | 保持轻量级，避免过度抽象 |
| 用户迁移困难 | MEDIUM | 提供迁移工具和详细文档 |

---

## 4. Acceptance Criteria

### 4.1 Must Have
- [ ] 插件化架构可用，支持运行时选择 AI 工具
- [ ] iFlow Provider 完整实现，功能与现有版本等效
- [ ] 跨平台兼容 (Windows/Mac/Linux)
- [ ] 配置文件支持 (YAML)
- [ ] 结构化进度跟踪
- [ ] 错误处理和重试机制
- [ ] 向后兼容现有 feature_list.json

### 4.2 Should Have
- [ ] 多种报告格式 (文本/JSON/HTML)
- [ ] 现代化 CLI (Click)
- [ ] 示例 Provider 实现
- [ ] 完整文档

### 4.3 Nice to Have
- [ ] 并发任务执行
- [ ] Web 报告查看器
- [ ] 插件热加载

---

## 5. Dependencies

### 5.1 External Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| Click | >=8.0 | CLI 框架 |
| PyYAML | >=6.0 | 配置文件解析 |
| colorama | >=0.4 | 跨平台彩色输出 |
| rich | >=13.0 | 富文本终端输出 (可选) |

### 5.2 Internal Dependencies
- Python >= 3.8
- iFlow CLI (现有集成)

---

## 6. Timeline

| Phase | Tasks | Estimate | Parallel Factor | Adjusted |
|-------|-------|----------|-----------------|----------|
| Phase 1 | 3 | 9h | 1.5x | 6h |
| Phase 2 | 3 | 14h | 1.3x | 11h |
| Phase 3 | 3 | 11h | 1.5x | 7h |
| Phase 4 | 3 | 10h | 1.2x | 8h |
| **Total** | **12** | **44h** | - | **32h** |

---

## 7. Notes

### 7.1 Assumptions
1. 用户熟悉现有 AI Harness 功能
2. 主要使用场景仍是 iFlow CLI
3. 未来可能添加其他 AI 工具支持
4. 用户有基本的 Python 环境

### 7.2 Open Questions (自评审已处理)
1. ~~是否需要支持远程执行？~~ → **已决定**: 不需要 (用户确认)
2. ~~是否需要插件热加载？~~ → **已决定**: 不需要 (MVP 阶段)
3. ~~报告的详细程度如何？~~ → **已决定**: 支持文本/JSON/HTML 三种格式

### 7.3 自评审: 缺口分类

#### ✅ 已自动解决 (AUTO-RESOLVED)
| 缺口 | 决定 | 依据 |
|------|------|------|
| 远程执行支持 | 不需要 | 用户明确 "暂不涉及" |
| 插件热加载 | 不需要 | MVP 阶段，保持简单 |
| 测试策略 | 不需要 | 用户明确不需要测试 |
| Web UI/API | 不需要 | 超出范围 |
| Python 版本 | 3.8+ | 保持现有要求 |

#### ✅ 用户已确认 (CONFIRMED)
| 缺口 | 决定 | 用户选择 |
|------|------|----------|
| Provider 发现机制 | 入口点注册 | 使用 setuptools entry_points |
| 配置文件位置 | 双层配置 | ~/.ai-harness/ + 项目级 .ai-harness/ |
| 报告默认格式 | JSON | 结构化，易于解析 |

#### ❓ 模糊点 (AMBIGUOUS)
| 问题 | 风险 | 建议 |
|------|------|------|
| "全面改进" 具体范围 | 可能范围蔓延 | 已通过 WBS 锁定范围 |
| "跨平台优先" 优先级 | Mac/Linux 支持程度 | 已在 Task 2.3 明确验证要求 |
| "渐进迁移" 时间线 | 迁移速度 | 已在 Phase 4 规划迁移步骤 |

#### 🔍 缺失的考虑点
| 缺失项 | 风险 | 补充 |
|--------|------|------|
| 性能基准 | 无法量化改进 | 添加简单性能追踪 |
| 错误恢复粒度 | 可能过度重试 | 分级错误类型已规划 |
| 插件版本管理 | 未来兼容性问题 | 建议在 Provider 接口添加版本字段 |

### 7.3 Constraints
- 必须保持 Python 3.8+ 兼容
- 不引入测试框架
- 不进行全新重写
- 轻量外部库限制

---

## 8. Momus 专家评审结果

**评审时间**: 2026-03-04  
**评审状态**: ✅ APPROVED

### 8.1 总体评估
**VERDICT**: OKAY - 计划完整，可执行

### 8.2 评审详情

#### ✅ 完整性检查
- [x] 所有需求已覆盖 (插件化、跨平台、配置、报告、错误处理)
- [x] 依赖关系正确识别
- [x] 风险评估充分

#### ✅ 可行性检查
- [x] 估算合理 (32h 经过并行优化)
- [x] 技术方案可行 (插件化架构成熟)
- [x] 依赖可控 (轻量库)

#### ✅ 质量检查
- [x] 接受标准清晰可测
- [x] 范围边界明确
- [x] 向后兼容性考虑充分

### 8.3 专家建议 (已整合)

| 建议 | 状态 | 处理 |
|------|------|------|
| 添加性能基准追踪 | ✅ 已采纳 | 在 Task 3.1 中添加 |
| 插件版本管理 | ✅ 已采纳 | 在 Provider 接口添加版本字段 |
| 错误恢复粒度 | ✅ 已采纳 | Task 3.2 已包含分级错误类型 |

### 8.4 Phase 批准状态

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: 架构设计 | ✅ APPROVED | 关键基础，优先执行 |
| Phase 2: 核心重构 | ✅ APPROVED | iFlow Provider 是验证点 |
| Phase 3: 功能增强 | ✅ APPROVED | 并行执行优化 |
| Phase 4: 集成迁移 | ✅ APPROVED | 向后兼容是关键 |

### 8.5 执行建议

1. **优先级**: 严格按照 WBS 顺序执行
2. **并行化**: 利用 Phase 2/3 的并行机会
3. **质量门**: 每个 Phase 完成后进行验证
4. **风险监控**: 关注向后兼容性和性能

---

*Plan Generated: 2026-03-04*  
*Last Updated: 2026-03-04*