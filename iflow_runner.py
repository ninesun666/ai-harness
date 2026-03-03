"""
iFlow Runner - 自动化运行 iFlow CLI 的调度脚本

使用方式:
1. 单次运行: python iflow_runner.py --action run
2. 持续运行: python iflow_runner.py --action continuous --interval 300
3. 检查状态: python iflow_runner.py --action status

工作原理:
- 读取 feature_list.json 找到下一个待完成任务
- 通过 iflow CLI 的非交互模式 (-p) 执行任务
- 使用 --yolo 自动接受操作
- 执行完成后自动关闭
- 循环执行直到所有任务完成

注意事项:
- 需要 iflow CLI 已安装并在 PATH 中
- 使用 --yolo 模式会自动接受所有操作，请确保任务安全
"""

import argparse
import json
import subprocess
import sys
import time
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List


def find_iflow_path() -> Optional[str]:
    """
    查找 iflow 命令的完整路径
    
    Returns:
        iflow 命令的完整路径，如果找不到返回 None
    """
    # 1. 尝试直接查找
    iflow_path = shutil.which('iflow')
    if iflow_path:
        return iflow_path
    
    # 2. 尝试常见路径
    common_paths = [
        r'C:\nvm4w\nodejs\iflow.cmd',
        r'C:\nvm4w\nodejs\iflow',
        os.path.expandvars(r'%APPDATA%\npm\iflow.cmd'),
        os.path.expandvars(r'%APPDATA%\npm\iflow'),
        '/usr/local/bin/iflow',
        '/usr/bin/iflow',
    ]
    
    for path in common_paths:
        if os.path.isfile(path):
            return path
    
    # 3. 尝试从环境变量 PATH 中查找
    path_env = os.environ.get('PATH', '')
    for path_dir in path_env.split(os.pathsep):
        for name in ['iflow.cmd', 'iflow']:
            candidate = os.path.join(path_dir, name)
            if os.path.isfile(candidate):
                return candidate
    
    return None


class iFlowRunner:
    """
    iFlow CLI 自动化运行器
    
    核心思路:
    1. 读取项目状态和待办任务
    2. 生成执行 prompt
    3. 调用 iflow -p "prompt" --yolo 非交互执行
    4. 等待执行完成
    5. 循环执行
    """
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.iflow_path = find_iflow_path()
        
        if not self.iflow_path:
            print("⚠️ 警告: 未找到 iflow 命令，请确保已安装 iFlow CLI")
        else:
            print(f"✅ 找到 iflow: {self.iflow_path}")
        
    def get_next_task(self, project_name: str = "ninesun-blog") -> Optional[Dict]:
        """获取下一个待完成的任务"""
        # 支持相对路径和绝对路径
        if Path(project_name).is_absolute():
            feature_file = Path(project_name) / ".agent-harness" / "feature_list.json"
        else:
            feature_file = self.project_root / project_name / ".agent-harness" / "feature_list.json"
        
        if not feature_file.exists():
            # 尝试父目录
            feature_file = self.project_root.parent / project_name / ".agent-harness" / "feature_list.json"
        
        if not feature_file.exists():
            print(f"feature_list.json 不存在: {feature_file}")
            return None
        
        with open(feature_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        features = data.get("features", [])
        
        # 按优先级排序，找到第一个未完成的
        priority_order = {"high": 0, "medium": 1, "low": 2}
        
        pending = [
            f for f in features 
            if not f.get("passes", False)
        ]
        
        if not pending:
            return None
        
        # 排序并返回第一个
        pending.sort(key=lambda x: priority_order.get(x.get("priority", "medium"), 1))
        return pending[0]
    
    def generate_prompt(self, task: Dict, project_name: str = "ninesun-blog") -> str:
        """生成自动执行的 prompt"""
        prompt = f"""继续开发 **{project_name}** 项目的任务。

⚠️ 重要：这是 {project_name} 项目，请只操作 {project_name}/ 目录下的文件！

## 当前任务
- ID: {task.get('id', 'Unknown')}
- 描述: {task.get('description', 'Unknown')}
- 优先级: {task.get('priority', 'medium')}
- 类型: {task.get('category', 'functional')}

## 执行步骤
{self._format_steps(task.get('steps', []))}

## 执行要求
1. 读取 {project_name}/.agent-harness/feature_list.json 确认任务状态
2. 按照任务描述完成开发
3. 完成后运行测试验证 (如适用)
4. 更新 {project_name}/.agent-harness/feature_list.json 中的 passes 状态为 true
5. 更新 {project_name}/.agent-harness/claude-progress.txt 记录进度

## 重要提醒
- 只处理这一个任务
- 只操作 {project_name}/ 目录
- 完成后必须标记 passes: true
- 如果遇到阻塞问题，记录到 progress 文件中并停止
"""
        return prompt
    
    def _format_steps(self, steps: List[str]) -> str:
        """格式化步骤列表"""
        if not steps:
            return "无特定步骤，按需执行"
        return "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
    
    def run_iflow(self, prompt: str, timeout: int = 600, max_turns: int = 50, 
                  project_cwd: Optional[str] = None) -> Dict:
        """
        调用 iFlow CLI 执行任务
        
        Args:
            prompt: 执行的 prompt
            timeout: 超时时间 (秒)
            max_turns: 最大轮次
            project_cwd: 目标项目的工作目录（iFlow 会在此目录运行）
            
        Returns:
            执行结果
        """
        if not self.iflow_path:
            return {
                "success": False,
                "error": "iflow 命令未找到，请确保已安装 iFlow CLI"
            }
        
        # 确定工作目录：优先使用目标项目目录，否则使用 runner 的项目根目录
        work_dir = Path(project_cwd).resolve() if project_cwd else self.project_root
        
        output_file = self.project_root / f"iflow_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 使用找到的 iflow 完整路径
        cmd = [
            self.iflow_path,
            "-p", prompt,
            "--yolo",  # 自动接受所有操作
            f"--max-turns={max_turns}",
            f"-o", str(output_file),
        ]
        
        print(f"\n执行命令: {self.iflow_path} -p ... --yolo --max-turns={max_turns}")
        print(f"工作目录: {work_dir}")
        
        # 设置环境变量，确保能找到 node 和 npm
        env = os.environ.copy()
        node_paths = [
            r'C:\nvm4w\nodejs',
            os.path.expandvars(r'%APPDATA%\npm'),
        ]
        for path in node_paths:
            if os.path.isdir(path) and path not in env.get('PATH', ''):
                env['PATH'] = path + os.pathsep + env.get('PATH', '')
        
        try:
            start_time = time.time()
            
            result = subprocess.run(
                cmd,
                cwd=str(work_dir),  # 在目标项目目录运行 iFlow
                capture_output=True,
                text=True,
                timeout=timeout + 60,  # 额外给一些缓冲时间
                env=env
            )
            
            elapsed = time.time() - start_time
            
            # 读取输出文件
            output_data = None
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    output_data = json.load(f)
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "elapsed_seconds": round(elapsed, 1),
                "stdout": result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout,
                "stderr": result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr,
                "output_file": str(output_file) if output_file.exists() else None,
                "output_data": output_data
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"执行超时 (>{timeout}秒)"
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "iflow 命令未找到，请确保已安装 iFlow CLI"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def scan_projects(self) -> List[str]:
        """扫描所有可用项目"""
        projects = []
        
        # 扫描的目录列表：当前目录、父目录、用户指定目录
        scan_dirs = [
            self.project_root,  # 当前目录
            self.project_root.parent,  # 父目录 (常见场景：ai-harness 作为子目录)
        ]
        
        scanned = set()
        for scan_dir in scan_dirs:
            if not scan_dir.exists() or str(scan_dir) in scanned:
                continue
            scanned.add(str(scan_dir))
            
            try:
                for item in scan_dir.iterdir():
                    if item.is_dir() and not item.name.startswith('.') and item.name not in ['node_modules', '__pycache__', '.git']:
                        harness_dir = item / ".agent-harness"
                        feature_file = harness_dir / "feature_list.json"
                        if feature_file.exists():
                            # 返回绝对路径
                            projects.append(str(item.resolve()))
            except Exception as e:
                pass
        
        return sorted(set(projects))
    
    def get_project_status(self, project_name: str) -> Dict:
        """获取项目状态"""
        # 支持相对路径和绝对路径
        if Path(project_name).is_absolute():
            feature_file = Path(project_name) / ".agent-harness" / "feature_list.json"
        else:
            feature_file = self.project_root / project_name / ".agent-harness" / "feature_list.json"
        
        if not feature_file.exists():
            # 尝试父目录
            feature_file = self.project_root.parent / project_name / ".agent-harness" / "feature_list.json"
        
        if not feature_file.exists():
            return {"error": f"项目不存在: {project_name}"}
        
        try:
            with open(feature_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            features = data.get("features", [])
            completed = sum(1 for f in features if f.get("passes", False))
            total = len(features)
            
            # 获取下一个任务
            next_task = None
            for feature in features:
                if not feature.get("passes", False):
                    # 检查依赖是否满足
                    deps = feature.get("dependencies", [])
                    deps_satisfied = all(
                        any(f.get("id") == dep and f.get("passes", False) for f in features)
                        for dep in deps
                    )
                    if deps_satisfied:
                        next_task = feature
                        break
            
            return {
                "project": project_name,
                "total_tasks": total,
                "completed": completed,
                "pending": total - completed,
                "progress": f"{completed}/{total} ({round(completed/total*100) if total > 0 else 0}%)",
                "next_task": {
                    "id": next_task.get("id"),
                    "description": next_task.get("description"),
                    "priority": next_task.get("priority")
                } if next_task else None
            }
        except Exception as e:
            return {"error": str(e)}
    
    def run_single(self, project_name: str = "ninesun-blog", timeout: int = 600, max_turns: int = 50) -> Dict:
        """执行单次任务"""
        # 解析项目路径
        if Path(project_name).is_absolute():
            project_path = Path(project_name)
        else:
            # 先尝试在当前目录下查找
            project_path = self.project_root / project_name
            if not project_path.exists():
                # 再尝试父目录
                project_path = self.project_root.parent / project_name
        
        project_path = project_path.resolve()
        
        # 获取下一个任务
        task = self.get_next_task(project_name)
        
        if not task:
            return {
                "status": "completed",
                "message": "🎉 所有任务已完成！"
            }
        
        print(f"\n{'='*60}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始执行任务")
        print(f"项目路径: {project_path}")
        print(f"ID: {task.get('id')}")
        print(f"描述: {task.get('description')}")
        print(f"优先级: {task.get('priority')}")
        print(f"{'='*60}")
        
        # 生成 prompt
        prompt = self.generate_prompt(task, Path(project_path).name)
        
        # 调用 iFlow，传入项目目录作为工作目录
        result = self.run_iflow(prompt, timeout, max_turns, project_cwd=str(project_path))
        
        # 检查任务是否完成
        updated_task = self.get_next_task(project_name)
        
        return {
            "status": "success" if result["success"] else "failed",
            "task": task,
            "execution": result,
            "next_task": updated_task,
            "task_completed": updated_task is None or updated_task.get("id") != task.get("id")
        }
    
    def run_continuous(self, project_name: str = "ninesun-blog", interval: int = 60, 
                       max_iterations: int = 100, timeout: int = 600, max_turns: int = 50) -> None:
        """持续运行模式"""
        print(f"\n{'='*60}")
        print(f"iFlow Runner 持续运行模式")
        print(f"项目: {project_name}")
        print(f"检查间隔: {interval} 秒")
        print(f"单次超时: {timeout} 秒")
        print(f"最大轮次: {max_turns}")
        print(f"最大迭代: {max_iterations} 次")
        print(f"{'='*60}\n")
        
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                result = self.run_single(project_name, timeout, max_turns)
                
                print(f"\n--- 执行结果 ---")
                print(f"状态: {result.get('status')}")
                print(f"耗时: {result.get('execution', {}).get('elapsed_seconds', 'N/A')} 秒")
                print(f"任务完成: {result.get('task_completed', False)}")
                
                if result["status"] == "completed":
                    print("\n🎉 所有任务已完成！")
                    break
                
                if result.get("task_completed"):
                    print(f"\n✅ 任务 {result['task'].get('id')} 已完成，继续下一个...")
                    time.sleep(5)  # 短暂等待后继续
                    continue
                
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 等待 {interval} 秒后继续...")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n\n⏹️ 收到停止信号，退出...")
                break
            except Exception as e:
                print(f"\n❌ 错误: {e}")
                print(f"等待 {interval} 秒后重试...")
                time.sleep(interval)
        
        print(f"\n执行完毕。共完成 {iteration} 次迭代。")
    
    def status(self, project_name: str = "ninesun-blog") -> Dict:
        """获取当前状态"""
        task = self.get_next_task(project_name)
        
        feature_file = self.project_root / project_name / ".agent-harness" / "feature_list.json"
        
        if not feature_file.exists():
            return {
                "project": project_name,
                "error": f"feature_list.json 不存在"
            }
        
        with open(feature_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        features = data.get("features", [])
        completed = sum(1 for f in features if f.get("passes", False))
        total = len(features)
        
        return {
            "project": project_name,
            "total_tasks": total,
            "completed": completed,
            "pending": total - completed,
            "next_task": task,
            "progress": f"{completed}/{total} ({completed*100//total if total > 0 else 0}%)"
        }


def main():
    parser = argparse.ArgumentParser(description='iFlow Runner - 自动化运行 iFlow CLI')
    parser.add_argument('--project-root', default=str(Path.cwd()), help='项目根目录')
    parser.add_argument('--project', default=None, help='项目名称或路径')
    parser.add_argument('--action', choices=['run', 'continuous', 'status', 'scan'], 
                       default='status', help='执行的操作')
    parser.add_argument('--interval', type=int, default=60, help='持续模式间隔秒数')
    parser.add_argument('--timeout', type=int, default=600, help='单次执行超时秒数')
    parser.add_argument('--max-turns', type=int, default=50, help='单次执行最大轮次')
    parser.add_argument('--max-iterations', type=int, default=100, help='持续模式最大迭代次数')
    
    args = parser.parse_args()
    
    runner = iFlowRunner(args.project_root)
    
    # 扫描可用项目
    projects = runner.scan_projects()
    
    if args.action == 'scan' or args.action == 'status':
        print(f"📋 发现 {len(projects)} 个项目:\n")
        for proj in projects:
            status = runner.get_project_status(proj)
            print(f"  • {Path(proj).name}")
            print(f"    进度: {status.get('progress', 'N/A')}")
            if status.get('next_task'):
                print(f"    下一个任务: {status['next_task'].get('description', 'N/A')}")
            print()
        
        if args.action == 'scan':
            return
    
    # 如果没有指定项目，使用第一个可用项目
    project = args.project
    if not project:
        if projects:
            project = projects[0]
            print(f"🎯 自动选择项目: {Path(project).name}\n")
        else:
            print("❌ 未找到可用项目，请使用 --project 指定项目路径")
            return
    
    if args.action == 'status':
        result = runner.get_project_status(project)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.action == 'run':
        result = runner.run_single(project, args.timeout, args.max_turns)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    elif args.action == 'continuous':
        runner.run_continuous(project, args.interval, args.max_iterations, 
                             args.timeout, args.max_turns)


def run_interactive():
    """交互式菜单模式"""
    print("\n")
    print("=" * 60)
    print("       AI Harness - iFlow Auto Development Tool")
    print("=" * 60)
    print("  Let AI complete software development tasks autonomously")
    print("=" * 60)
    print()
    
    # 检查依赖
    iflow_path = find_iflow_path()
    if iflow_path:
        print(f"[OK] iFlow CLI: {iflow_path}")
    else:
        print("[!] iFlow CLI not installed")
        print("    Run: npm install -g @iflow-ai/iflow-cli")
        print()
    
    # 扫描可用项目
    runner = iFlowRunner(os.getcwd())
    projects = runner.scan_projects()
    
    if not projects:
        print("[!] No projects found")
        print("    Create .agent-harness/feature_list.json in your project")
        print()
        print("Press Enter to exit...")
        input()
        return
    
    print(f"\n[*] Found {len(projects)} projects:")
    for i, proj in enumerate(projects, 1):
        status = runner.get_project_status(proj)
        # 兼容 total_tasks 和 total 两种字段名
        total = status.get('total_tasks') or status.get('total', 0)
        completed = status.get('completed', 0)
        progress = f"{completed}/{total}"
        proj_name = Path(proj).name
        print(f"   {i}. {proj_name} ({progress})")
    
    print()
    print("-" * 60)
    print("Menu:")
    print("  [1] View Status    - Show project details")
    print("  [2] Run Once       - Execute one task")
    print("  [3] Continuous     - Run until all tasks done")
    print("  [4] New Project    - Create new project structure")
    print("  [Q] Exit")
    print("-" * 60)
    
    while True:
        print()
        choice = input("Select [1-4/Q]: ").strip().upper()
        
        if choice == 'Q' or choice == '':
            print("\nBye!")
            break
            
        elif choice == '1':
            # 查看状态
            proj = select_project(projects)
            if proj:
                print("\n" + "="*60)
                print(f"[*] Project: {proj}")
                print("="*60)
                status = runner.get_project_status(proj)
                print(json.dumps(status, ensure_ascii=False, indent=2))
                
        elif choice == '2':
            # 单次执行
            proj = select_project(projects)
            if proj:
                print(f"\n[>] Running: {proj}")
                print("="*60)
                result = runner.run_single(proj)
                print("\nResult:", json.dumps(result, ensure_ascii=False, indent=2))
                projects = runner.scan_projects()  # 刷新项目列表
                
        elif choice == '3':
            # 持续运行
            proj = select_project(projects)
            if proj:
                print(f"\n[>>] Continuous: {proj}")
                print("="*60)
                print("Press Ctrl+C to stop")
                print()
                runner.run_continuous(proj, interval=60)
                projects = runner.scan_projects()  # 刷新项目列表
                
        elif choice == '4':
            # 创建新项目
            proj_name = input("Project name: ").strip()
            if proj_name:
                create_new_project(proj_name)
                projects = runner.scan_projects()  # 刷新项目列表
                
        else:
            print("[!] Invalid choice")
        
        # 刷新项目列表显示
        print("\n" + "-" * 60)
        projects = runner.scan_projects()
        if projects:
            print(f"[*] Projects ({len(projects)}):")
            for i, proj in enumerate(projects, 1):
                status = runner.get_project_status(proj)
                total = status.get('total_tasks') or status.get('total', 0)
                completed = status.get('completed', 0)
                progress = f"{completed}/{total}"
                proj_name = Path(proj).name
                print(f"   {i}. {proj_name} ({progress})")


def select_project(projects: List[str]) -> Optional[str]:
    """选择项目"""
    if len(projects) == 1:
        return projects[0]
    
    print(f"\nSelect project [1-{len(projects)}]:")
    for i, proj in enumerate(projects, 1):
        proj_name = Path(proj).name
        print(f"   {i}. {proj_name}")
    
    try:
        idx = int(input("Number: ").strip())
        if 1 <= idx <= len(projects):
            return projects[idx - 1]
    except:
        pass
    
    print("[!] Invalid selection")
    return None


def create_new_project(name: str):
    """创建新项目结构"""
    import shutil
    
    project_dir = Path(name)
    harness_dir = project_dir / ".agent-harness"
    
    if project_dir.exists():
        print(f"[!] Directory already exists: {name}")
        return
    
    # 创建目录结构
    harness_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建 feature_list.json
    feature_list = {
        "project_spec": f"{name} - Project description",
        "created_at": datetime.now().isoformat(),
        "total_features": 0,
        "completed": 0,
        "pending": 0,
        "features": []
    }
    
    with open(harness_dir / "feature_list.json", 'w', encoding='utf-8') as f:
        json.dump(feature_list, f, ensure_ascii=False, indent=2)
    
    # 创建进度文件
    with open(harness_dir / "claude-progress.txt", 'w', encoding='utf-8') as f:
        f.write(f"# Progress Log - {name}\n")
        f.write(f"# Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
    
    print(f"[OK] Project created: {name}/")
    print(f"     .agent-harness/")
    print(f"       feature_list.json")
    print(f"       claude-progress.txt")
    print(f"       ├── feature_list.json")
    print(f"       └── claude-progress.txt")


if __name__ == "__main__":
    # 检查是否为交互模式
    if '--interactive' in sys.argv or '-i' in sys.argv:
        run_interactive()
    else:
        main()