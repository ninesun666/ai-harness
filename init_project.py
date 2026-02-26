"""
AI Harness 项目初始化脚本

功能:
- 扫描同级和上级目录
- 交互式选择目标项目目录
- 自动生成 .agent-harness 模板文件
- 支持自动检测项目类型 (Java/Maven, Node.js, Python 等)

使用方式:
1. 双击 init.bat
2. python init_project.py
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple


# ANSI 颜色代码
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header():
    """打印标题"""
    print("\n")
    print("=" * 60)
    print(f"{Colors.CYAN}       AI Harness - Project Initializer{Colors.RESET}")
    print("=" * 60)
    print("  Generate .agent-harness templates for your projects")
    print("=" * 60)
    print()


def detect_project_type(project_dir: Path) -> Dict:
    """
    检测项目类型和技术栈
    
    Returns:
        包含项目类型、语言、框架等信息的字典
    """
    info = {
        "type": "unknown",
        "language": "unknown",
        "framework": "unknown",
        "build_tool": "unknown",
        "modules": [],
    }
    
    # Java/Maven 项目
    pom_file = project_dir / "pom.xml"
    if pom_file.exists():
        info["type"] = "java-maven"
        info["language"] = "Java"
        info["build_tool"] = "Maven"
        
        # 尝试解析 pom.xml 获取更多信息
        try:
            content = pom_file.read_text(encoding='utf-8')
            
            # 检测 Spring Boot
            if 'spring-boot' in content.lower() or 'org.springframework.boot' in content:
                info["framework"] = "Spring Boot"
            
            # 检测多模块项目
            if '<modules>' in content:
                info["modules"] = extract_maven_modules(content)
                
        except:
            pass
        
        return info
    
    # Java/Gradle 项目
    gradle_file = project_dir / "build.gradle" or project_dir / "build.gradle.kts"
    if gradle_file.exists():
        info["type"] = "java-gradle"
        info["language"] = "Java"
        info["build_tool"] = "Gradle"
        return info
    
    # Node.js 项目
    package_json = project_dir / "package.json"
    if package_json.exists():
        info["type"] = "nodejs"
        info["language"] = "JavaScript/TypeScript"
        info["build_tool"] = "npm/yarn/pnpm"
        
        try:
            data = json.loads(package_json.read_text(encoding='utf-8'))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            
            # 检测框架
            if "react" in deps:
                info["framework"] = "React"
            elif "vue" in deps:
                info["framework"] = "Vue"
            elif "next" in deps:
                info["framework"] = "Next.js"
            elif "express" in deps:
                info["framework"] = "Express"
            elif "@nestjs/core" in deps:
                info["framework"] = "NestJS"
                
        except:
            pass
        
        return info
    
    # Python 项目
    requirements = project_dir / "requirements.txt"
    pyproject = project_dir / "pyproject.toml"
    setup_py = project_dir / "setup.py"
    
    if requirements.exists() or pyproject.exists() or setup_py.exists():
        info["type"] = "python"
        info["language"] = "Python"
        info["build_tool"] = "pip/poetry"
        
        # 检测框架
        try:
            if requirements.exists():
                content = requirements.read_text(encoding='utf-8').lower()
                if "django" in content:
                    info["framework"] = "Django"
                elif "flask" in content:
                    info["framework"] = "Flask"
                elif "fastapi" in content:
                    info["framework"] = "FastAPI"
        except:
            pass
        
        return info
    
    # Go 项目
    go_mod = project_dir / "go.mod"
    if go_mod.exists():
        info["type"] = "go"
        info["language"] = "Go"
        info["build_tool"] = "go mod"
        return info
    
    # Rust 项目
    cargo_toml = project_dir / "Cargo.toml"
    if cargo_toml.exists():
        info["type"] = "rust"
        info["language"] = "Rust"
        info["build_tool"] = "Cargo"
        return info
    
    return info


def extract_maven_modules(pom_content: str) -> List[str]:
    """从 pom.xml 提取模块列表"""
    import re
    modules = []
    match = re.search(r'<modules>(.*?)</modules>', pom_content, re.DOTALL)
    if match:
        module_matches = re.findall(r'<module>(.*?)</module>', match.group(1))
        modules = [m.strip() for m in module_matches]
    return modules


def scan_candidate_dirs(script_dir: Path) -> List[Tuple[Path, str]]:
    """
    扫描候选目录
    
    Returns:
        [(目录路径, 显示标签), ...]
    """
    candidates = []
    
    # 1. 同级目录
    parent = script_dir.parent
    if parent.exists():
        for item in parent.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                if item.name not in ['node_modules', '__pycache__', '.git', 'dist', 'build', 'target']:
                    candidates.append((item, f"同级: {item.name}"))
    
    # 2. 上级目录的子目录
    grandparent = parent.parent
    if grandparent.exists() and grandparent != parent:
        for item in grandparent.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                if item.name not in ['node_modules', '__pycache__', '.git', 'dist', 'build', 'target']:
                    if item != parent:  # 避免重复
                        candidates.append((item, f"上级: {item.name}"))
    
    # 3. 常见开发目录
    common_dev_dirs = [
        Path.home() / "projects",
        Path.home() / "workspace",
        Path.home() / "code",
        Path.home() / "dev",
        Path("C:/Users") / os.environ.get("USERNAME", "") / "Desktop" / "workspace",
    ]
    
    for dev_dir in common_dev_dirs:
        if dev_dir.exists():
            for item in dev_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    if item not in [c[0] for c in candidates]:
                        candidates.append((item, f"开发目录: {item.name}"))
    
    # 去重并排序
    seen = set()
    unique_candidates = []
    for path, label in candidates:
        if str(path) not in seen:
            seen.add(str(path))
            unique_candidates.append((path, label))
    
    return sorted(unique_candidates, key=lambda x: x[0].name.lower())


def get_project_description(project_dir: Path, project_info: Dict) -> str:
    """生成项目描述"""
    name = project_dir.name
    
    # 尝试从现有文档获取描述
    readme = project_dir / "README.md"
    if readme.exists():
        try:
            content = readme.read_text(encoding='utf-8')
            # 提取第一段作为描述
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and len(line) > 10:
                    return f"{name} - {line[:100]}"
        except:
            pass
    
    # 根据 tech stack 生成描述
    lang = project_info.get("language", "unknown")
    framework = project_info.get("framework", "")
    
    if framework:
        return f"{name} - {lang} 项目 ({framework})"
    else:
        return f"{name} - {lang} 项目"


def generate_feature_list(project_dir: Path, project_info: Dict) -> Dict:
    """生成 feature_list.json 内容"""
    name = project_dir.name
    description = get_project_description(project_dir, project_info)
    
    # 构建模块列表
    modules = []
    if project_info.get("modules"):
        for i, mod_name in enumerate(project_info["modules"], 1):
            modules.append({
                "id": f"M{i:03d}",
                "name": mod_name,
                "description": f"{mod_name} 模块",
                "status": "pending"
            })
    else:
        modules.append({
            "id": "M001",
            "name": "main",
            "description": "主模块",
            "status": "pending"
        })
    
    # 构建 tech_stack
    tech_stack = {
        "language": project_info.get("language", "unknown"),
    }
    if project_info.get("framework"):
        tech_stack["framework"] = project_info.get("framework")
    if project_info.get("build_tool"):
        tech_stack["build"] = project_info.get("build_tool")
    
    feature_list = {
        "project_spec": description,
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "tech_stack": tech_stack,
        "modules": {
            "description": "项目模块",
            "list": modules
        },
        "total_features": 0,
        "completed": 0,
        "in_progress": 0,
        "pending": 0,
        "features": []
    }
    
    return feature_list


def generate_agent_instructions(project_dir: Path, project_info: Dict) -> str:
    """生成 AGENT_INSTRUCTIONS.md 内容"""
    name = project_dir.name
    lang = project_info.get("language", "unknown")
    framework = project_info.get("framework", "")
    build_tool = project_info.get("build_tool", "")
    
    # 根据项目类型生成不同的构建命令
    build_cmd = ""
    test_cmd = ""
    
    if project_info["type"] == "java-maven":
        build_cmd = "mvn clean compile -DskipTests"
        test_cmd = "mvn test"
    elif project_info["type"] == "java-gradle":
        build_cmd = "./gradlew build -x test"
        test_cmd = "./gradlew test"
    elif project_info["type"] == "nodejs":
        build_cmd = "npm run build"
        test_cmd = "npm test"
    elif project_info["type"] == "python":
        build_cmd = "pip install -r requirements.txt"
        test_cmd = "pytest"
    elif project_info["type"] == "go":
        build_cmd = "go build ./..."
        test_cmd = "go test ./..."
    elif project_info["type"] == "rust":
        build_cmd = "cargo build"
        test_cmd = "cargo test"
    
    content = f'''# Agent Instructions
# 此文件定义 coding agent 的工作流程和行为规范

## 项目信息

- **项目名称**: {name}
- **开发语言**: {lang}
- **框架**: {framework or "无特定框架"}
- **构建工具**: {build_tool}

## 会话开始流程

每个 coding agent 会话必须按以下顺序开始：

1. **定位环境**
   ```bash
   pwd  # 确认工作目录
   ```

2. **读取进度**
   - 阅读 `.agent-harness/claude-progress.txt`
   - 查看 `git log --oneline -10`
   - 了解最近的工作内容

3. **检查功能状态**
   - 阅读 `.agent-harness/feature_list.json`
   - 找到最高优先级的未完成功能

4. **验证环境**
   ```bash
   # 编译项目确保无错误
   {build_cmd or "请根据项目类型运行对应的构建命令"}
   ```

5. **开始工作**
   - 选择一个功能开始实现
   - 遵循增量开发原则

## 会话结束流程

每个 coding agent 会话必须按以下顺序结束：

1. **编译验证**
   ```bash
   {build_cmd or "请根据项目类型运行对应的构建命令"}
   ```

2. **测试验证**
   ```bash
   {test_cmd or "请根据项目类型运行对应的测试命令"}
   ```

3. **更新状态**
   - 更新 `feature_list.json` 中的功能状态
   - 只在确认通过后设置 `passes: true`

4. **提交代码**
   ```bash
   git add .
   git commit -m "feat: [功能描述]"
   ```

5. **记录进度**
   - 更新 `claude-progress.txt`
   - 记录完成的工作和遇到的问题

## 重要原则

### 增量开发
- 每次只处理一个功能
- 小步快跑，频繁提交

### 编译优先
- 每次修改后都要编译验证
- 确保没有编译错误后再提交

### 状态清晰
- 代码提交信息要清晰描述改动
- 让下一个 agent 能快速理解当前状态

## 禁止行为

1. 删除 feature_list.json 中的功能
2. 在未测试时将 passes 设为 true
3. 一次性实现多个功能
4. 提交无法编译的代码
'''
    
    return content


def generate_progress_log(project_dir: Path, project_info: Dict) -> str:
    """生成 claude-progress.txt 内容"""
    name = project_dir.name
    lang = project_info.get("language", "unknown")
    framework = project_info.get("framework", "")
    
    tech_info = lang
    if framework:
        tech_info += f" + {framework}"
    
    content = f'''# Claude Progress Log

================================================================================
PROJECT: {name}
================================================================================
技术栈: {tech_info}
================================================================================

[初始化] {datetime.now().strftime('%Y-%m-%d %H:%M')}
Status: PROJECT_INITIALIZED
Summary:
  - 创建 .agent-harness 目录结构
  - 生成 feature_list.json 任务清单模板
  - 生成 AGENT_INSTRUCTIONS.md 工作流程规范
  - 项目准备就绪，等待添加任务

================================================================================
FEATURE STATUS
================================================================================
COMPLETED: 0
PENDING:   0

NEXT FEATURES:
  - 在 feature_list.json 中添加任务

================================================================================
'''
    
    return content


def init_project(project_dir: Path) -> bool:
    """
    初始化项目的 .agent-harness 目录
    
    Returns:
        是否成功
    """
    # 检测项目类型
    project_info = detect_project_type(project_dir)
    
    print(f"\n{Colors.BLUE}[检测项目]{Colors.RESET}")
    print(f"  目录: {project_dir}")
    print(f"  类型: {project_info['type']}")
    print(f"  语言: {project_info['language']}")
    if project_info.get('framework'):
        print(f"  框架: {project_info['framework']}")
    if project_info.get('build_tool'):
        print(f"  构建: {project_info['build_tool']}")
    
    # 检查是否已存在
    harness_dir = project_dir / ".agent-harness"
    if harness_dir.exists():
        print(f"\n{Colors.YELLOW}[警告]{Colors.RESET} .agent-harness 目录已存在")
        choice = input("是否覆盖? [y/N]: ").strip().lower()
        if choice != 'y':
            print("已取消")
            return False
        # 备份旧文件
        backup_dir = project_dir / f".agent-harness.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.move(str(harness_dir), str(backup_dir))
        print(f"已备份到: {backup_dir.name}")
    
    # 创建目录
    harness_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成文件
    try:
        # feature_list.json
        feature_list = generate_feature_list(project_dir, project_info)
        with open(harness_dir / "feature_list.json", 'w', encoding='utf-8') as f:
            json.dump(feature_list, f, ensure_ascii=False, indent=2)
        
        # AGENT_INSTRUCTIONS.md
        instructions = generate_agent_instructions(project_dir, project_info)
        with open(harness_dir / "AGENT_INSTRUCTIONS.md", 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        # claude-progress.txt
        progress = generate_progress_log(project_dir, project_info)
        with open(harness_dir / "claude-progress.txt", 'w', encoding='utf-8') as f:
            f.write(progress)
        
        print(f"\n{Colors.GREEN}[成功]{Colors.RESET} 已生成以下文件:")
        print(f"  .agent-harness/")
        print(f"  ├── feature_list.json")
        print(f"  ├── AGENT_INSTRUCTIONS.md")
        print(f"  └── claude-progress.txt")
        
        return True
        
    except Exception as e:
        print(f"\n{Colors.RED}[错误]{Colors.RESET} 生成文件失败: {e}")
        return False


def run_interactive():
    """交互式模式"""
    print_header()
    
    # 获取脚本所在目录
    script_dir = Path(__file__).parent.resolve()
    
    print(f"{Colors.CYAN}[扫描目录]{Colors.RESET}")
    print(f"  从 {script_dir.parent} 扫描...")
    print()
    
    # 扫描候选目录
    candidates = scan_candidate_dirs(script_dir)
    
    if not candidates:
        print(f"{Colors.YELLOW}[提示]{Colors.RESET} 未找到候选目录")
        print("请输入目标目录路径:")
        custom_path = input("> ").strip()
        if custom_path:
            custom_dir = Path(custom_path)
            if custom_dir.exists() and custom_dir.is_dir():
                candidates = [(custom_dir, "自定义路径")]
            else:
                print(f"{Colors.RED}[错误]{Colors.RESET} 目录不存在")
                return
        else:
            return
    
    # 过滤掉已有 .agent-harness 的目录
    has_harness = []
    no_harness = []
    for path, label in candidates:
        if (path / ".agent-harness").exists():
            has_harness.append((path, label))
        else:
            no_harness.append((path, label))
    
    # 显示候选目录
    print(f"\n{Colors.BOLD}候选项目目录:{Colors.RESET}")
    print("-" * 60)
    
    idx = 1
    
    # 未初始化的目录 (优先)
    if no_harness:
        print(f"\n{Colors.GREEN}[待初始化]{Colors.RESET}")
        for path, label in no_harness[:15]:
            info = detect_project_type(path)
            type_tag = f"[{info['type']}]" if info['type'] != 'unknown' else ""
            print(f"  {Colors.GREEN}{idx}{Colors.RESET}. {path.name} {type_tag}")
            print(f"      {label}")
            idx += 1
    
    # 已初始化的目录
    if has_harness:
        print(f"\n{Colors.YELLOW}[已初始化]{Colors.RESET}")
        for path, label in has_harness[:10]:
            info = detect_project_type(path)
            type_tag = f"[{info['type']}]" if info['type'] != 'unknown' else ""
            print(f"  {Colors.YELLOW}{idx}{Colors.RESET}. {path.name} {type_tag} (已有 .agent-harness)")
            print(f"      {label}")
            idx += 1
    
    print("-" * 60)
    print(f"  {Colors.CYAN}0{Colors.RESET}. 输入自定义路径")
    print(f"  {Colors.CYAN}Q{Colors.RESET}. 退出")
    print("-" * 60)
    
    # 选择
    total = len(no_harness) + len(has_harness)
    choice = input(f"\n请选择 [1-{total}/0/Q]: ").strip().upper()
    
    if choice == 'Q' or choice == '':
        print("\n已退出")
        return
    
    if choice == '0':
        print("\n请输入目标目录路径:")
        custom_path = input("> ").strip()
        if not custom_path:
            print("已取消")
            return
        target_dir = Path(custom_path)
        if not target_dir.exists():
            print(f"{Colors.RED}[错误]{Colors.RESET} 目录不存在: {custom_path}")
            return
    else:
        try:
            num = int(choice)
            if num < 1 or num > total:
                print(f"{Colors.RED}[错误]{Colors.RESET} 无效选择")
                return
            
            # 根据编号确定是哪个目录
            if num <= len(no_harness):
                target_dir, _ = no_harness[num - 1]
            else:
                target_dir, _ = has_harness[num - len(no_harness) - 1]
        except ValueError:
            print(f"{Colors.RED}[错误]{Colors.RESET} 无效输入")
            return
    
    # 初始化
    print(f"\n{'='*60}")
    print(f"{Colors.BOLD}初始化项目{Colors.RESET}: {target_dir.name}")
    print(f"{'='*60}")
    
    success = init_project(target_dir)
    
    if success:
        print(f"\n{Colors.GREEN}{'='*60}")
        print(f"初始化完成！")
        print(f"{'='*60}{Colors.RESET}")
        print(f"\n下一步:")
        print(f"  1. 编辑 {target_dir.name}/.agent-harness/feature_list.json 添加任务")
        print(f"  2. 运行 start.bat 开始自动化开发")


def main():
    """主入口"""
    # Windows 控制台编码
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass
    
    run_interactive()


if __name__ == "__main__":
    main()
