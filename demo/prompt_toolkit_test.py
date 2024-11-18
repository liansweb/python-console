from prompt_toolkit import prompt, PromptSession, print_formatted_text
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML, FormattedText, ANSI
import subprocess
import os
import code
import platform

# 定义样式 - 使用更丰富的配色方案
style = Style.from_dict({
    'prompt': 'bg:#333333 #ffffff',
    'command': '#ansiyellow',
    'error': '#ansired',
    'success': '#ansigreen',
    'info': '#ansiblue',
})

# 扩展命令及其说明
COMMANDS = {
    'help': '显示帮助信息',
    'clear': '清屏',
    'exit': '退出程序',
    'python': '进入 Python REPL',
    'shell': '执行 shell 命令',
    'system': '显示系统信息',
}

# 创建命令补全器
completer = WordCompleter(list(COMMANDS.keys()))

def get_prompt_message():
    """返回格式化的提示符，包含系统信息"""
    username = os.getenv('USER', os.getenv('USERNAME', 'user'))
    return HTML(f'<prompt>{username}@{platform.node()}</prompt> > ')

def clear_screen():
    """清屏，支持不同操作系统"""
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def execute_shell_command(command):
    """执行 shell 命令并返回结果"""
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        if result.returncode == 0:
            return result.stdout
        return f"错误: {result.stderr}"
    except Exception as e:
        return f"执行出错: {str(e)}"

def show_system_info():
    """显示系统信息"""
    info = [
        f"操作系统: {platform.system()} {platform.release()}",
        f"Python版本: {platform.python_version()}",
        f"处理器: {platform.processor()}",
        f"机器类型: {platform.machine()}"
    ]
    return "\n".join(info)

def main():
    """主程序循环"""
    session = PromptSession()
    
    while True:
        try:
            command = session.prompt(
                get_prompt_message(),
                completer=completer,
                style=style
            ).strip()
            
            if not command:
                continue
                
            if command == 'exit':
                print_formatted_text(FormattedText([('class:success', '再见！')]), style=style)
                break
            elif command == 'help':
                print_formatted_text(FormattedText([('class:info', '可用命令：')]), style=style)
                for cmd, desc in COMMANDS.items():
                    print_formatted_text(FormattedText([
                        ('class:command', f"{cmd:10}"),
                        ('', f" - {desc}")
                    ]), style=style)
            elif command == 'clear':
                clear_screen()
            elif command == 'python':
                print_formatted_text(FormattedText([
                    ('class:info', '进入 Python REPL (使用 exit() 退出)')
                ]), style=style)
                code.interact(local=locals())
            elif command == 'system':
                print_formatted_text(FormattedText([
                    ('class:info', show_system_info())
                ]), style=style)
            elif command.startswith('shell'):
                if len(command) <= 6:
                    print_formatted_text(FormattedText([
                        ('class:error', '请在 shell 后面输入要执行的命令，例如：shell ls')
                    ]), style=style)
                    continue
                result = execute_shell_command(command[6:])
                print_formatted_text(result)
            else:
                print_formatted_text(FormattedText([
                    ('class:error', '未知命令。输入 "help" 获取帮助。')
                ]), style=style)
            
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        except Exception as e:
            print_formatted_text(FormattedText([
                ('class:error', f"错误: {str(e)}")
            ]), style=style)

if __name__ == '__main__':
    print_formatted_text(FormattedText([
        ('class:info', '欢迎使用终端示例程序！输入 "help" 获取帮助。')
    ]), style=style)
    main()