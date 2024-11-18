import click
from typing import Optional
import sys
from pathlib import Path
import json

class Config:
    """全局配置类"""
    def __init__(self):
        self.verbose = False

# 创建 Config 对象作为 Click 上下文
pass_config = click.make_pass_decorator(Config, ensure=True)

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='启用详细输出模式')
@pass_config
def cli(config: Config, verbose: bool):
    """终端工具集 - 提供文件处理、格式转换等实用功能"""
    config.verbose = verbose

@cli.command()
@click.option('--count', '-c', default=1, help='重复问候的次数')
@click.option('--name', '-n', prompt='请输入姓名', help='要问候的人名')
@click.option('--language', '-l', type=click.Choice(['zh', 'en']), default='zh', help='选择语言(zh/en)')
@pass_config
def hello(config: Config, count: int, name: str, language: str):
    """友好的问候程序，支持中英文"""
    greeting = '你好' if language == 'zh' else 'Hello'
    for i in range(count):
        message = f'{greeting} {name}!'
        if config.verbose:
            message = f'[{i+1}/{count}] {message}'
        click.echo(message)

@cli.command()
@click.argument('filename', type=click.Path(exists=True))
@click.option('--line-numbers/--no-line-numbers', '-n/-N', default=False, help='是否显示行号')
@click.option('--encoding', '-e', default='utf-8', help='文件编码')
@pass_config
def cat(config: Config, filename: str, line_numbers: bool, encoding: str):
    """读取并显示文件内容，支持行号显示和编码选择"""
    try:
        with open(filename, 'r', encoding=encoding) as f:
            if config.verbose:
                click.echo(f'正在读取文件: {filename} (编码: {encoding})')
            
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                if line_numbers:
                    click.echo(f'{i:4d}: {line}', nl=False)
                else:
                    click.echo(line, nl=False)
    except UnicodeDecodeError:
        click.echo(f'错误：无法使用 {encoding} 编码读取文件', err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f'错误：{str(e)}', err=True)
        sys.exit(1)

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
@click.option('--pretty', '-p', is_flag=True, help='格式化 JSON 输出')
@pass_config
def json_format(config: Config, input_file: str, output_file: str, pretty: bool):
    """JSON 文件格式化工具"""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            indent = 2 if pretty else None
            json.dump(data, f, ensure_ascii=False, indent=indent)
            
        if config.verbose:
            click.echo(f'已将 {input_file} 格式化并保存至 {output_file}')
    except json.JSONDecodeError:
        click.echo(f'错误：{input_file} 不是有效的 JSON 文件', err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f'错误：{str(e)}', err=True)
        sys.exit(1)

if __name__ == '__main__':
    cli()