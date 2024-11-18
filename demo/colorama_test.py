from colorama import init, Fore, Back, Style
import time
from typing import List, Tuple

def init_colorama():
    """初始化 colorama，确保跨平台兼容性"""
    init(autoreset=True)

def print_formatted(text: str, *styles: str) -> None:
    """使用指定样式打印文本
    
    Args:
        text: 要打印的文本
        styles: 要应用的样式序列
    """
    print(''.join(styles) + text)

def demo_color_matrix():
    """展示所有前景色和背景色的组合矩阵"""
    print("\n=== 颜色组合矩阵 ===")
    colors = [Fore.RED, Fore.GREEN, Fore.BLUE, Fore.YELLOW, Fore.MAGENTA, Fore.CYAN, Fore.WHITE]
    backgrounds = [Back.BLACK, Back.RED, Back.GREEN, Back.BLUE, Back.YELLOW]
    
    # 打印表头
    print("    ", end="")
    for bg in backgrounds:
        print(f"{bg}  背景  {Style.RESET_ALL}", end=" ")
    print()
    
    # 打印颜色矩阵
    for fg in colors:
        color_name = fg.replace(Fore.BLACK, "").replace("[", "").replace("m", "")
        print(f"{fg}文字{Style.RESET_ALL}", end=" ")
        for bg in backgrounds:
            print(f"{fg}{bg} 示例 {Style.RESET_ALL}", end=" ")
        print()

def demo_progress_bar():
    """展示带颜色的进度条效果"""
    print("\n=== 进度条演示 ===")
    width = 40
    for i in range(width + 1):
        progress = i / width
        bar = '█' * i + '░' * (width - i)
        percentage = int(progress * 100)
        print(f'\r{Fore.GREEN}进度: [{bar}] {percentage}%{Style.RESET_ALL}', end='')
        time.sleep(0.05)
    print()

def demo_loading_animation():
    """展示带颜色的加载动画"""
    print("\n=== 加载动画演示 ===")
    chars = '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
    for _ in range(30):
        for char, color in zip(chars, colors):
            print(f'\r{color}加载中 {char}{Style.RESET_ALL}', end='')
            time.sleep(0.05)
    print()

def demo_styled_text():
    """展示样式化的文本效果"""
    print("\n=== 样式化文本演示 ===")
    messages = [
        (Fore.GREEN + Style.BRIGHT, "✓ 成功", "操作已完成"),
        (Fore.RED + Style.BRIGHT, "✗ 错误", "发生异常"),
        (Fore.YELLOW + Style.BRIGHT, "⚠ 警告", "配置有误"),
        (Fore.BLUE + Style.BRIGHT, "ℹ 信息", "正在处理"),
    ]
    
    for style, prefix, msg in messages:
        print(f"{style}{prefix}{Style.RESET_ALL} {msg}")

def main():
    """主函数：按顺序展示所有演示效果"""
    init_colorama()
    print(Style.BRIGHT + "=== Colorama 功能演示 ===" + Style.RESET_ALL)
    
    demo_styled_text()
    demo_color_matrix()
    demo_progress_bar()
    demo_loading_animation()

if __name__ == '__main__':
    main()