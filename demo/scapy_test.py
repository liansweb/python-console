from scapy.all import sniff
from scapy.layers.http import HTTP, HTTPRequest, HTTPResponse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from collections import defaultdict
from urllib.parse import urlparse, parse_qs
from scapy.arch import get_if_list
from scapy.interfaces import NetworkInterface
import netifaces  # 需要安装: pip install netifaces
import platform
import sys

console = Console()
sessions = defaultdict(dict)

def parse_url(host, path):
    """解析 URL，返回 pathname 和 query 参数"""
    if not host or not path:
        return {'pathname': 'N/A', 'query': {}}
    
    full_url = f"http://{host}{path}"
    parsed = urlparse(full_url)
    return {
        'pathname': parsed.path,
        'query': parse_qs(parsed.query)
    }

def format_headers(headers):
    """格式化 HTTP 头部"""
    if not headers:
        return "N/A"
    return "\n".join(f"{k}: {v}" for k, v in headers.items())

def format_body(body):
    """格式化请求/响应体"""
    if not body:
        return "N/A"
    try:
        return body.decode('utf-8')
    except:
        return f"<Binary Data: {len(body)} bytes>"

def print_session(session_key):
    """打印完整的 HTTP 会话信息"""
    session = sessions[session_key]
    if 'request' not in session:
        return
    
    table = Table(show_header=False, box=None)
    table.add_column("Key", style="cyan", width=15)
    table.add_column("Value", style="green")
    
    # 请求信息
    req = session['request']
    url_info = parse_url(req.get('host'), req.get('path'))
    
    table.add_row("请求方法", req.get('method', 'N/A'))
    table.add_row("完整URL", f"http://{req.get('host', '')}{req.get('path', '')}")
    table.add_row("Host", req.get('host', 'N/A'))
    table.add_row("路径", url_info['pathname'])
    table.add_row("查询参数", str(url_info['query']) if url_info['query'] else 'N/A')
    table.add_row("请求头", format_headers(req.get('headers', {})))
    table.add_row("请求体", format_body(req.get('body')))
    
    # 响应信息
    if 'response' in session:
        resp = session['response']
        table.add_row("状态码", resp.get('status', 'N/A'))
        table.add_row("响应头", format_headers(resp.get('headers', {})))
        table.add_row("响应体", format_body(resp.get('body')))
    
    panel = Panel(
        table,
        title=f"HTTP 会话 - {session_key}",
        border_style="blue"
    )
    console.print(panel)
    del sessions[session_key]

def packet_handler(packet):
    if HTTP not in packet:
        return
        
    if HTTPRequest in packet:
        http_layer = packet[HTTPRequest]
        src = f"{packet.src}:{packet.sport}"
        dst = f"{packet.dst}:{packet.dport}"
        session_key = f"{src} -> {dst}"
        
        # 提取请求头
        headers = {}
        for field in http_layer.fields:
            if field != 'Method' and field != 'Path' and field != 'Http-Version':
                value = http_layer.fields[field]
                if value:
                    headers[field] = value.decode() if isinstance(value, bytes) else str(value)
        
        # 存储请求信息
        sessions[session_key]['request'] = {
            'method': http_layer.Method.decode() if http_layer.Method else "N/A",
            'host': http_layer.Host.decode() if http_layer.Host else "N/A",
            'path': http_layer.Path.decode() if http_layer.Path else "N/A",
            'headers': headers,
            'body': bytes(packet[HTTP].payload) if packet[HTTP].payload else None
        }
            
    elif HTTPResponse in packet:
        http_layer = packet[HTTPResponse]
        src = f"{packet.src}:{packet.sport}"
        dst = f"{packet.dst}:{packet.dport}"
        session_key = f"{dst} -> {src}"
        
        # 提取响应头
        headers = {}
        for field in http_layer.fields:
            if field != 'Status-Line' and field != 'Status-Code' and field != 'Http-Version':
                value = http_layer.fields[field]
                if value:
                    headers[field] = value.decode() if isinstance(value, bytes) else str(value)
        
        # 存储响应信息
        if session_key in sessions:
            sessions[session_key]['response'] = {
                'status': http_layer.Status_Code.decode() if http_layer.Status_Code else "N/A",
                'headers': headers,
                'body': bytes(packet[HTTP].payload) if packet[HTTP].payload else None
            }
            print_session(session_key)

def get_available_interfaces():
    """获取系统可用的网卡列表"""
    interfaces = []
    
    # 获取所有活跃的网卡接口
    active_ifaces = netifaces.interfaces()
    
    for iface_name in get_if_list():
        # 检查接口是否活跃且有 IP 地址
        if iface_name in active_ifaces:
            try:
                # 获取接口的 IP 地址信息
                addrs = netifaces.ifaddresses(iface_name)
                if netifaces.AF_INET in addrs:  # 检查是否有 IPv4 地址
                    iface = NetworkInterface(iface_name)
                    interfaces.append({
                        'name': iface_name,
                        'description': getattr(iface, 'description', iface_name),
                        'ip': addrs[netifaces.AF_INET][0]['addr']
                    })
            except (ValueError, KeyError):
                continue
    
    return interfaces

def select_interface():
    """让用户选择要使用的网卡"""
    interfaces = get_available_interfaces()
    
    if not interfaces:
        console.print("[bold red]未找到可用的网卡接口[/bold red]")
        sys.exit(1)
    
    console.print("[bold blue]可用的网卡接口：[/bold blue]")
    for idx, iface in enumerate(interfaces, 1):
        console.print(f"{idx}. {iface['name']} - {iface['description']}")
        console.print(f"   IP: {iface['ip']}")
    
    while True:
        try:
            choice = int(input("\n请选择要使用的网卡 (输入序号): "))
            if 1 <= choice <= len(interfaces):
                return interfaces[choice-1]['name']
            else:
                console.print("[bold red]无效的选择，请重试[/bold red]")
        except ValueError:
            console.print("[bold red]请输入有效的数字[/bold red]")

try:
    selected_iface = select_interface()
    console.print(f"[bold blue]开始捕获 HTTP 流量 (使用网卡: {selected_iface})...[/bold blue]")
    sniff(iface=selected_iface, 
          prn=packet_handler, 
          store=0,
          filter="tcp",
          count=1000,
          timeout=240)
except KeyboardInterrupt:
    console.print("\n[bold red]捕获已停止[/bold red]")
