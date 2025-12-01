import subprocess
import os
import sys
import time
import glob
import platform

# --- 路径设置 ---
# SCRIPT_DIR: .../AgentChat/scripts
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# PROJECT_ROOT: .../AgentChat (项目根目录)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
# BASE_DIR: .../AgentChat/src
BASE_DIR = os.path.join(PROJECT_ROOT, "src")

BACKEND_DIR = os.path.join(BASE_DIR, "backend")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# 系统判断
IS_WINDOWS = platform.system() == 'Windows'

processes = []


def install_dependencies():
    """第一步：在根目录查找 requestment.txt 并安装"""
    print(f"📂 项目根目录定位为: {PROJECT_ROOT}")
    print(f"🚀 [Step 1] 正在查找依赖文件...")

    # --- 修改点：现在去 PROJECT_ROOT (根目录) 找文件，而不是 src 下 ---
    # 匹配 requestment.txt, requirements.txt, request.txt 等
    req_files = glob.glob(os.path.join(PROJECT_ROOT, "request*.txt"))

    # 如果找不到 request*，再试一次 requirements.txt (防止名字完全不匹配)
    if not req_files:
        req_files = glob.glob(os.path.join(PROJECT_ROOT, "requirements.txt"))

    if not req_files:
        print(f"⚠️ 警告：在项目根目录 {PROJECT_ROOT} 下未找到 request*.txt 或 requirements.txt")
        print("跳过依赖安装，尝试直接启动服务...")
        return

    req_file = req_files[0]
    print(f"📦 发现依赖文件: {req_file}")
    print("⏳ 正在安装依赖 (pip install)...")

    try:
        # 使用绝对路径安装，不用担心当前在哪里
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file], check=True)
        print("✅ 依赖安装完成！")
    except subprocess.CalledProcessError:
        print("❌ 依赖安装失败，脚本终止。")
        sys.exit(1)


def start_services():
    """第二步 & 第三步：并发启动后端和前端"""
    try:
        # --- 启动后端 ---
        print(f"🚀 [Step 2] 启动后端 (cwd: {BACKEND_DIR})...")
        if not os.path.exists(BACKEND_DIR):
            print(f"❌ 错误：找不到后端目录 {BACKEND_DIR}")
            return

        backend_process = subprocess.Popen(
            ["uvicorn", "agentchat.main:app", "--port", "7860"],
            cwd=BACKEND_DIR,  # 保持在 /src/backend 运行
            shell=False
        )
        processes.append(backend_process)

        time.sleep(2)

        # --- 启动前端 ---
        print(f"🚀 [Step 3] 启动前端 (cwd: {FRONTEND_DIR})...")
        if not os.path.exists(FRONTEND_DIR):
            print(f"❌ 错误：找不到前端目录 {FRONTEND_DIR}")
            return

        npm_cmd = "npm"
        use_shell = False
        if IS_WINDOWS:
            use_shell = True

        frontend_process = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=FRONTEND_DIR,  # 保持在 /src/frontend 运行
            shell=use_shell
        )
        processes.append(frontend_process)

        print("\n✨ 服务已启动！日志将混合显示在下方。")
        print("🛑 按 Ctrl+C 可停止服务。\n")

        while True:
            time.sleep(1)
            if backend_process.poll() is not None:
                print("⚠️ 后端服务已退出。")
                break
            if frontend_process.poll() is not None:
                print("⚠️ 前端服务已退出。")
                break

    except KeyboardInterrupt:
        print("\n🛑 接收到停止信号...")
    finally:
        cleanup()


def cleanup():
    print("🧹 正在关闭后台服务...")
    for p in processes:
        if p.poll() is None:
            p.terminate()
    print("👋 再见！")


if __name__ == "__main__":
    # 简单检查
    if not os.path.exists(BASE_DIR):
        print(f"❌ 错误：找不到 src 文件夹 {BASE_DIR}")
        sys.exit(1)

    install_dependencies()
    start_services()