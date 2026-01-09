from pywinauto import Desktop

print("正在尝试连接 'Single Map' 窗口...")

try:
    # 1. 连接到桌面上的 Tomey 窗口
    # backend="uia" 是较新的技术，支持 WPF/Qt 等现代程序
    # 如果这个报错或者找不到，可以将 "uia" 改为 "win32" 再试一次
    app = Desktop(backend="uia").window(title="Single Map")
    
    # 2. 检查窗口是否存在
    if app.exists():
        print("成功找到窗口！正在分析控件结构，这可能需要几秒钟...")
        
        # 3. 将窗口的内部结构打印到控制台
        # 这会列出所有的按钮、文本框、标签等信息
        app.print_control_identifiers()
        
        print("\n=== 分析结束 ===")
    else:
        print("未找到标题为 'Single Map' 的窗口，请检查软件是否打开。")

except Exception as e:
    print(f"发生错误: {e}")