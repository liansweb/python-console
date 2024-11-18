from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.widgets import (Frame, ListBox, Layout, Label, TextBox, Button, 
                               Widget, Text, PopUpDialog, Divider)
from asciimatics.exceptions import NextScene, StopApplication
from scapy.all import sniff, IP, TCP, UDP, Raw, conf, get_if_list, logging as scapy_logging
from scapy.layers.http import HTTP, HTTPRequest, HTTPResponse
from threading import Thread, Lock
import queue
import time
import re
from collections import defaultdict
import argparse
import netifaces
from asciimatics.event import KeyboardEvent
import psutil
import socket
import threading
from datetime import datetime
import logging
import sys

# 添加日志配置
def setup_logging():
    """配置日志记录"""
    # 创建logger
    logger = logging.getLogger('wireshark_tui')
    logger.setLevel(logging.DEBUG)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    
    # 创建文件处理器
    log_file = f'wireshark_tui_{datetime.now().strftime("%Y%m%d")}.log'
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # 添加处理器到logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # 抑制 scapy 的调试输出
    scapy_logging.getLogger("scapy").setLevel(logging.ERROR)
    
    return logger

class HTTPSession:
    """HTTP会话管理类"""
    def __init__(self):
        self.sessions = {}  # 使用字典存储会话
        self.session_id = 0
        
    def add_packet(self, packet):
        """添加数据包到会话"""
        if not (TCP in packet and Raw in packet):
            return
        
        payload = packet[Raw].load
        if not (b'HTTP/' in payload or b'GET ' in payload or b'POST ' in payload):
            return
        
        # 使 IP:Port 对作为会话标识
        session_key = None
        try:
            if b'HTTP/' in payload and b'\r\n\r\n' in payload:
                # 响应包
                client = f"{packet[IP].dst}:{packet[TCP].dport}"
                server = f"{packet[IP].src}:{packet[TCP].sport}"
                session_key = f"{client}-{server}"
            elif b'GET ' in payload or b'POST ' in payload:
                # 请求包
                client = f"{packet[IP].src}:{packet[TCP].sport}"
                server = f"{packet[IP].dst}:{packet[TCP].dport}"
                session_key = f"{client}-{server}"
        except:
            return
        
        if session_key:
            if session_key not in self.sessions:
                self.sessions[session_key] = {
                    'id': self.session_id,
                    'request': None,
                    'response': None,
                    'timestamp': time.time()
                }
                self.session_id += 1
            
            try:
                decoded_payload = payload.decode('utf-8', errors='ignore')
                if b'GET ' in payload or b'POST ' in payload:
                    self.sessions[session_key]['request'] = decoded_payload
                else:
                    self.sessions[session_key]['response'] = decoded_payload
            except:
                pass
        
    def get_http_streams(self):
        """重组HTTP流"""
        # 按时间戳排序并格式化会话
        sorted_sessions = sorted(
            self.sessions.items(),
            key=lambda x: x[1]['timestamp'],
            reverse=True
        )
        return [(session['id'], self._format_session(req, resp))
                for _, session in sorted_sessions
                if (req := session['request']) is not None
                or (resp := session['response']) is not None]
        
    def _format_session(self, request, response):
        """格式化会话"""
        formatted = []
        if request:
            formatted.extend([
                "=== Request ===",
                request.split('\r\n\r\n')[0],  # 只显示头部
                ""
            ])
        if response:
            formatted.extend([
                "=== Response ===",
                response.split('\r\n\r\n')[0],  # 只显示头部
                ""
            ])
        return '\n'.join(formatted)

class PacketFilter:
    """数据包过滤器"""
    def __init__(self):
        self.logger = logging.getLogger('wireshark_tui.filter')
        self.filter_expr = None
        
        # 定义支持的过滤器格式
        self.filter_patterns = {
            'ip.src': (r'ip\.src\s*=*\s*(\d+\.\d+\.\d+\.\d+)', 
                      lambda p, m: IP in p and p[IP].src == m.group(1)),
            'ip.dst': (r'ip\.dst\s*=*\s*(\d+\.\d+\.\d+\.\d+)', 
                      lambda p, m: IP in p and p[IP].dst == m.group(1)),
            'tcp.port': (r'tcp\.port\s*=*\s*(\d+)', 
                        lambda p, m: TCP in p and (p[TCP].sport == int(m.group(1)) or 
                                                 p[TCP].dport == int(m.group(1)))),
            'udp.port': (r'udp\.port\s*=*\s*(\d+)', 
                        lambda p, m: UDP in p and (p[UDP].sport == int(m.group(1)) or 
                                                 p[UDP].dport == int(m.group(1)))),
            'http': (r'http', 
                    lambda p, _: TCP in p and Raw in p and 
                    (b'HTTP/' in p[Raw].load or b'GET ' in p[Raw].load or 
                     b'POST ' in p[Raw].load)),
            'tcp': (r'tcp', lambda p, _: TCP in p),
            'udp': (r'udp', lambda p, _: UDP in p)
        }

    def set_filter(self, expr):
        """设置过滤器表达式"""
        self.logger.debug(f"设置过滤器: {expr}")
        if not expr:
            self.filter_expr = None
            return True
            
        # 规范化表达式
        expr = expr.strip().lower()
        
        # 验证过滤器格式
        valid = False
        for pattern, _ in self.filter_patterns.values():
            if re.match(pattern, expr):
                valid = True
                break
                
        if not valid:
            raise ValueError(
                "不支持的过滤器语法\n"
                "支持的格式:\n"
                "- ip.src=x.x.x.x\n"
                "- ip.dst=x.x.x.x\n"
                "- tcp.port=xxx\n"
                "- udp.port=xxx\n"
                "- http\n"
                "- tcp\n"
                "- udp"
            )
            
        self.filter_expr = expr
        return True

    def match(self, packet):
        """匹配数据包"""
        if not self.filter_expr:
            return True
            
        try:
            # 遍历所有过滤器模式
            for pattern, matcher in self.filter_patterns.values():
                match = re.match(pattern, self.filter_expr)
                if match:
                    return matcher(packet, match)
            return False
            
        except Exception as e:
            self.logger.debug(f"过滤匹配错误: {e}")
            return False

class PacketCapture:
    def __init__(self):
        self.logger = logging.getLogger('wireshark_tui.capture')
        self.packets = queue.Queue()  # 所有数据包
        self.filtered_packets = queue.Queue()  # 过滤后的数据包
        self.http_streams = []  # HTTP流量
        self._http_requests = {}  # 临时存储HTTP请求
        self.filter = None
        self.interface = None
        self.capture_thread = None
        self._running = True
        self._stop_sniffer = threading.Event()
        self._filter_map = {
            'http': 'tcp port 80 or tcp port 8080 or tcp port 443',
            'https': 'tcp port 443',
            'dns': 'udp port 53',
            'ftp': 'tcp port 21',
            'ssh': 'tcp port 22',
            'telnet': 'tcp port 23',
            'smtp': 'tcp port 25',
            'pop3': 'tcp port 110',
            'imap': 'tcp port 143'
        }
        # 添加临时文件清理标志
        conf.verb = 0  # 禁用详细输出
        conf.use_pcap = False  # 禁用 pcap 文件
        conf.use_dnet = False  # 禁用 dnet
        conf.save_packets = False  # 禁止保存数据包
        conf.temp_files = []  # 清空临时文件列表
        self.packet_filter = PacketFilter()
        
    def _convert_filter_expression(self, expr):
        """转换过滤器表达式为 BPF 格式"""
        try:
            self.logger.debug(f"开始转换过滤器表达式: {expr}")
            expr = expr.lower().strip()
            
            # 检查是否是预定义的协议
            if expr in self._filter_map:
                self.logger.debug(f"使用预定义过滤器: {self._filter_map[expr]}")
                return self._filter_map[expr]
            
            # 修复常见的输入错误
            expr = expr.replace('srp.', 'tcp.')  # 修复 srp 为 tcp
            expr = expr.replace('=', ' == ')  # 修复单等号
            
            # 转换常见的过滤语法
            expr = expr.replace('ip.src', 'src host')
            expr = expr.replace('ip.dst', 'dst host')
            expr = expr.replace('tcp.port', 'tcp port')
            expr = expr.replace('udp.port', 'udp port')
            expr = expr.replace('tcp.srcport', 'tcp src port')
            expr = expr.replace('tcp.dstport', 'tcp dst port')
            expr = expr.replace('udp.srcport', 'udp src port')
            expr = expr.replace('udp.dstport', 'udp dst port')
            
            # 转换比较运算符
            expr = expr.replace('==', ' ')
            expr = expr.replace('!=', ' not ')
            expr = expr.replace('&&', 'and')
            expr = expr.replace('||', 'or')
            
            self.logger.debug(f"转换后的过滤器表达式: {expr}")
            return expr
            
        except Exception as e:
            self.logger.debug(f"过滤器转换错误: {str(e)}")
            raise ValueError(f"过滤器转换错误: {str(e)}")

    def set_filter(self, filter_expr):
        """设置过滤器"""
        try:
            self.logger.debug(f"设置过滤器: {filter_expr}")
            if self.packet_filter.set_filter(filter_expr):
                # 清空过滤队列
                while not self.filtered_packets.empty():
                    self.filtered_packets.get()
                return True
        except Exception as e:
            self.logger.error(f"设置过滤器失败: {e}")
            raise ValueError(str(e))
            
    def _match_filter(self, packet):
        """检查数据包是否匹配过滤器"""
        self.logger.debug(f"开始过滤数据包: {packet.summary()}")
        if not self.filter:
            self.logger.debug("无过滤器，直接通过")
            return True
        
        try:
            # 使用内存中的过滤而不是临时文件
            if 'ip.src' in self.filter:
                src = re.search(r'ip.src\s*==\s*(\S+)', self.filter).group(1)
                if IP not in packet or packet[IP].src != src:
                    return False
                
            if 'ip.dst' in self.filter:
                dst = re.search(r'ip.dst\s*==\s*(\S+)', self.filter).group(1)
                if IP not in packet or packet[IP].dst != dst:
                    return False
                
            if 'tcp.port' in self.filter:
                port = int(re.search(r'tcp.port\s*==\s*(\d+)', self.filter).group(1))
                if TCP not in packet or (packet[TCP].sport != port and packet[TCP].dport != port):
                    return False
                
            if 'udp.port' in self.filter:
                port = int(re.search(r'udp.port\s*==\s*(\d+)', self.filter).group(1))
                if UDP not in packet or (packet[UDP].sport != port and packet[UDP].dport != port):
                    return False
                
            if 'http' in self.filter.lower():
                if not (TCP in packet and Raw in packet and 
                       (b'HTTP/' in packet[Raw].load or 
                        b'GET ' in packet[Raw].load or 
                        b'POST ' in packet[Raw].load)):
                    return False
                
            return True
        
        except Exception as e:
            self.logger.debug(f"过滤匹配错误: {e}")
            return False

    def start_capture(self, interface=None):
        """启动数据包捕获"""
        self.interface = interface
        if self.capture_thread and self.capture_thread.is_alive():
            return
        
        # 清理之前可能存在的临时文件
        self._cleanup_temp_files()
        
        self._running = True
        self._stop_sniffer.clear()
        self.capture_thread = threading.Thread(
            target=self._capture_packets,
            args=(self.packet_callback,)
        )
        self.capture_thread.daemon = True
        self.capture_thread.start()

    def _cleanup_temp_files(self):
        """清理临时文件"""
        import os
        import glob
        import tempfile

        # 清理 scapy 的临时文件
        temp_dir = tempfile.gettempdir()
        patterns = [
            os.path.join(temp_dir, "scapy_*.cap"),
            os.path.join(temp_dir, "scapy_*.pcap"),
            os.path.join(temp_dir, "scapy_*.pkt"),
        ]
        
        for pattern in patterns:
            try:
                for file_path in glob.glob(pattern):
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass
            except Exception as e:
                print(f"清理临时文件出错: {e}")

    def _capture_packets(self, callback):
        """持续捕获数据包"""
        try:
            self.logger.debug("开始捕获数据包")
            
            # 配置 sniff 参数
            kwargs = {
                'prn': callback,
                'store': 0,  # 不存储数据包
                'iface': self.interface,
                'stop_filter': lambda _: self._stop_sniffer.is_set(),
                'filter': "ip",  # 只捕获 IP 数据包
                'count': 0,  # 持续捕获
                'quiet': True,  # 抑制输出
                'monitor': False,  # 禁用监控模式
            }
            
            # 使用 AsyncSniffer 来避免临时文件创建
            from scapy.sendrecv import AsyncSniffer
            sniffer = AsyncSniffer(**kwargs)
            sniffer.start()
            
            # 等待停止信号
            while not self._stop_sniffer.is_set():
                time.sleep(0.1)
            
            sniffer.stop()
            
        except Exception as e:
            self.logger.debug(f"Capture error: {e}")

    def stop_capture(self):
        """停止捕获并清理资源"""
        self._running = False
        self._stop_sniffer.set()
        
        if self.capture_thread:
            try:
                # 停止捕获线程
                if self.interface:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.sendto(b'', ('localhost', 0))
                    sock.close()
                self.capture_thread.join(timeout=1.0)
            except Exception as e:
                print(f"Stop capture error: {e}")
            finally:
                self.capture_thread = None
                # 清理临时文件
                self._cleanup_temp_files()

        # 清理数据包队列
        while not self.packets.empty():
            try:
                self.packets.get_nowait()
            except queue.Empty:
                break
                
        while not self.filtered_packets.empty():
            try:
                self.filtered_packets.get_nowait()
            except queue.Empty:
                break
    def _cleanup_temp_files(self):
        """清理临时文件"""
        import os
        import glob
        import tempfile

        # 清理 scapy 的临时文件
        temp_dir = tempfile.gettempdir()
        patterns = [
            os.path.join(temp_dir, "scapy_*.cap"),
            os.path.join(temp_dir, "scapy_*.pcap"),
            os.path.join(temp_dir, "scapy_*.pkt"),
        ]
        
        for pattern in patterns:
            try:
                for file_path in glob.glob(pattern):
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass
            except Exception as e:
                print(f"清理临时文件出错: {e}")

    def packet_callback(self, packet):
        """处理捕获的数据包"""
        if not self._running:
            return
            
        try:
            # 提取基本信息
            packet_info = {
                'time': time.time(),  # 使用当前时间
                'src': packet[IP].src if IP in packet else '',
                'dst': packet[IP].dst if IP in packet else '',
                'raw_packet': packet  # 保存原始数据包
            }
            
            # 添加协议特定信息
            if TCP in packet:
                packet_info['protocol'] = 'TCP'
                packet_info['sport'] = packet[TCP].sport
                packet_info['dport'] = packet[TCP].dport
            elif UDP in packet:
                packet_info['protocol'] = 'UDP'
                packet_info['sport'] = packet[UDP].sport
                packet_info['dport'] = packet[UDP].dport
                
            # 添加到主队列
            try:
                self.packets.put_nowait(packet_info)
            except queue.Full:
                try:
                    self.packets.get_nowait()
                    self.packets.put_nowait(packet_info)
                except queue.Empty:
                    pass
                    
            # 应用过滤器
            if self.packet_filter.filter_expr:
                if self._match_filter(packet_info):
                    try:
                        self.filtered_packets.put_nowait(packet_info)
                    except queue.Full:
                        try:
                            self.filtered_packets.get_nowait()
                            self.filtered_packets.put_nowait(packet_info)
                        except queue.Empty:
                            pass
                            
        except Exception as e:
            self.logger.error(f"数据包处理错误: {e}")
            
    def _match_filter(self, packet_info):
        """匹配过滤器"""
        try:
            if not self.packet_filter.filter_expr:
                return True
                
            filter_expr = self.packet_filter.filter_expr.lower()
            
            # TCP 端口过滤
            if 'tcp.port' in filter_expr:
                if packet_info.get('protocol') != 'TCP':
                    return False
                port = int(re.search(r'tcp\.port\s*==\s*(\d+)', filter_expr).group(1))
                return (packet_info.get('sport') == port or 
                       packet_info.get('dport') == port)
                       
            # UDP 端口过滤
            if 'udp.port' in filter_expr:
                if packet_info.get('protocol') != 'UDP':
                    return False
                port = int(re.search(r'udp\.port\s*==\s*(\d+)', filter_expr).group(1))
                return (packet_info.get('sport') == port or 
                       packet_info.get('dport') == port)
                       
            # IP 源地址过滤
            if 'ip.src' in filter_expr:
                ip = re.search(r'ip\.src\s*==\s*([0-9.]+)', filter_expr).group(1)
                return packet_info.get('src') == ip
                
            # IP 目标地址过滤
            if 'ip.dst' in filter_expr:
                ip = re.search(r'ip\.dst\s*==\s*([0-9.]+)', filter_expr).group(1)
                return packet_info.get('dst') == ip
                
            # 协议过滤
            if filter_expr == 'tcp':
                return packet_info.get('protocol') == 'TCP'
            if filter_expr == 'udp':
                return packet_info.get('protocol') == 'UDP'
                
            return False
            
        except Exception as e:
            self.logger.error(f"过滤匹配错误: {e}")
            return False

class HTTPStream:
    """表示一个完整的 HTTP 请求-响应对"""
    def __init__(self, request, response):
        self.logger = logging.getLogger('wireshark_tui.http_stream')
        self.logger.debug("创建新的 HTTP 流")
        self.logger.debug(f"请求信息: {request}")
        self.logger.debug(f"响应信息: {response}")
        self.request = request
        self.response = response
        self.time = request['time']

    def __str__(self):
        return f"{self.request['method']} {self.request['path']} -> {self.response['status_code']}"

class BaseFrame(Frame):
    """基础框架类，提供通用板配置"""
    def __init__(self, screen, height, width, title, reduce_cpu=False):
        self.logger = logging.getLogger('wireshark_tui.base_frame')
        self.logger.debug(f"初始化 BaseFrame: title={title}, height={height}, width={width}")
        super().__init__(screen, height, width, title=title, reduce_cpu=reduce_cpu)
        self.logger.debug("BaseFrame 初始化完成")
        
        # 新的配色方案
        self.palette = {
            # 基础界面元素 - 白底黑字
            "background": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE),
            "shadow": (Screen.COLOUR_BLACK, None, Screen.COLOUR_BLACK),
            "disabled": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE),
            "invalid": (Screen.COLOUR_RED, Screen.A_BOLD, Screen.COLOUR_WHITE),
            "label": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE),
            "borders": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE),
            "scroll": (Screen.COLOUR_BLUE, Screen.A_NORMAL, Screen.COLOUR_WHITE),
            
            # 标题
            "title": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_WHITE),
            
            # 列表项
            "list_item": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE),
            "focus_list_item": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLUE),  # 蓝底白字
            "selected_list_item": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE),
            "selected_focus_list_item": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLUE),  # 蓝底白字
            
            # 按钮
            "button": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),  # 蓝底白字
            "focus_button": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLUE),  # 蓝底白字加粗
            "hover_button": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLUE),  # 蓝底字加粗
            "disabled_button": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE),
            
            # 编辑框
            "edit_text": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE),
            "focus_edit_text": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
            
            # 字段
            "field": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE),
            "focus_field": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
            "selected_field": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE),
            "selected_focus_field": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLUE),
        }

class InterfaceSelector(Frame):
    def __init__(self, screen, interfaces, on_select):
        super().__init__(
            screen,
            screen.height // 2,
            screen.width // 2,
            title="Select Network Interface",
            reduce_cpu=True,
            can_scroll=False
        )
        
        self._selected = None
        self._on_select = on_select
        
        # 创建布局
        layout = Layout([1], fill_frame=True)
        self.add_layout(layout)
        
        # 创建接口列表
        self.interfaces_list = ListBox(
            height=screen.height // 3,
            options=interfaces,
            on_select=self._select_interface
        )
        layout.add_widget(self.interfaces_list)
        
        # 按钮布局
        button_layout = Layout([1, 1])
        self.add_layout(button_layout)
        button_layout.add_widget(Button("OK", self._ok), 0)
        button_layout.add_widget(Button("Cancel", self._cancel), 1)
        
        self.fix()

    def _select_interface(self):
        if self.interfaces_list.value is not None:
            self._selected = self.interfaces_list.value

    def _ok(self):
        if self._selected:
            self._on_select(self._selected)
        raise StopApplication("User selected interface")

    def _cancel(self):
        raise StopApplication("User cancelled")

def get_interfaces():
    """获取所有网络接口"""
    interfaces = []
    # 使用 psutil 获取网卡信息
    for name, stats in psutil.net_if_stats().items():
        # 只获取启用的接口
        if stats.isup:
            # 获取接口的地址信息
            addrs = psutil.net_if_addrs().get(name, [])
            # 尝试获取 IPv4 地址
            ipv4 = next((addr.address for addr in addrs 
                        if addr.family == socket.AF_INET), "无 IPv4 地址")
            desc = f"{ipv4}"
            # 只返回接口名称作为值
            interfaces.append((f"{name}: {desc}", name))  # 修改这里，值只保留 name
    return interfaces

def select_interface(screen):
    """网卡选择界面"""
    selected_interface = None
    
    def on_select(interface):
        nonlocal selected_interface
        selected_interface = interface
    
    # 获取可用的网卡列表
    interfaces = get_interfaces()
    if not interfaces:
        raise RuntimeError("未找到可用的网络接口")
    
    # 创建选择器和场景
    selector = InterfaceSelector(screen, interfaces, on_select)
    scenes = [
        Scene([selector], -1, name="Interface")
    ]
    
    # 播放场景
    screen.play(scenes, stop_on_resize=True)
    
    return selected_interface

class PacketDetailView(BaseFrame):
    """数据包详情视图"""
    def __init__(self, screen, packet):
        self.logger = logging.getLogger('wireshark_tui.packet_detail')
        self.logger.debug("初始化数据包详情视图")
        super().__init__(screen,
                        screen.height * 2 // 3,
                        screen.width * 2 // 3,
                        hover_focus=True,
                        title="Packet Details")
        self.packet = packet
        
        # 创建布
        layout = Layout([1])
        self.add_layout(layout)
        
        # 添加详情文本框
        self.details = TextBox(
            screen.height * 2 // 3 - 4,
            as_string=True,
            line_wrap=True,
            readonly=True
        )
        layout.add_widget(self.details)
        
        # 添加关闭按钮
        layout2 = Layout([1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Close", self._close), 2)
        
        self.fix()
        self.logger.debug(f"显示数据包: {packet}")
        self._update_details()

    def _update_details(self):
        self.logger.debug("更新数据包详情")
        details = []
        # IP层信息
        if IP in self.packet:
            self.logger.debug("处理IP层信息")
            details.append("=== IP Layer ===")
            details.append(f"Source: {self.packet[IP].src}")
            details.append(f"Destination: {self.packet[IP].dst}")
            details.append(f"Protocol: {self.packet[IP].proto}")
            
        # TCP/UDP层信息
        if TCP in self.packet:
            details.append("\n=== TCP Layer ===")
            details.append(f"Source Port: {self.packet[TCP].sport}")
            details.append(f"Destination Port: {self.packet[TCP].dport}")
            details.append(f"Sequence: {self.packet[TCP].seq}")
            details.append(f"Flags: {self.packet[TCP].flags}")
        elif UDP in self.packet:
            details.append("\n=== UDP Layer ===")
            details.append(f"Source Port: {self.packet[UDP].sport}")
            details.append(f"Destination Port: {self.packet[UDP].dport}")
            
        # HTTP层信息
        if Raw in self.packet:
            raw_data = self.packet[Raw].load
            if b'HTTP/' in raw_data or b'GET ' in raw_data or b'POST ' in raw_data:
                details.append("\n=== HTTP Layer ===")
                try:
                    details.append(raw_data.decode('utf-8', errors='ignore'))
                except:
                    details.append(str(raw_data))
        self.logger.debug("详情更新完成")
        self.details.value = "\n".join(details)

    def _close(self):
        """关闭详情视图"""
        raise NextScene("Main")

class HTTPStreamView(BaseFrame):
    """HTTP流查看器"""
    def __init__(self, screen, streams, on_close):
        super().__init__(
            screen,
            screen.height,
            screen.width,
            "HTTP Streams Viewer"
        )
        
        # 创建分栏布局
        main_layout = Layout([30, 70], fill_frame=True)  # 30%宽度给列表，70%给内容
        self.add_layout(main_layout)
        
        # 左侧会话列表
        left_layout = Layout([1])
        main_layout.add_widget(Label("Sessions:"), 0)
        self.session_list = ListBox(
            height=screen.height - 5,
            options=[(f"Session {id}", id) for id, _ in streams],
            on_select=self._on_session_select
        )
        main_layout.add_widget(self.session_list, 0)
        
        # 右侧内容区域
        self.content = TextBox(
            screen.height - 5,
            as_string=True,
            label="HTTP Content",
            name="content"
        )
        main_layout.add_widget(self.content, 1)
        
        # 底部按钮
        button_layout = Layout([1, 1, 1])
        self.add_layout(button_layout)
        button_layout.add_widget(Button("Previous", self._previous_session), 0)
        button_layout.add_widget(Button("Next", self._next_session), 1)
        button_layout.add_widget(Button("Close", self._close), 2)
        
        self.fix()
        
        # 显示操作说明
        self.content.value = (
            "HTTP Stream Viewer 操作说明:\n\n"
            "- 使用 ↑/↓ 键选择会话\n"
            "- Enter 键查看会话详情\n"
            "- Previous/Next 按钮或 ←/→ 键切换会话\n"
            "- ESC 或 Close 按钮关闭查看器"
        )
    
    def _on_session_select(self):
        self.logger.debug("选择了新的 HTTP 流")
        if self.session_list.value is not None:
            self.logger.debug(f"选择的流索引: {self.session_list.value}")
            self._show_session(self.session_list.value)
    
    def _previous_session(self):
        if self.session_list.value is not None:
            self._show_session(self.session_list.value - 1)
    
    def _next_session(self):
        if self.session_list.value is not None:
            self._show_session(self.session_list.value + 1)
    
    def _show_session(self, session_id):
        for id, content in self.streams:
            if id == session_id:
                self.content.value = content
                break
    
    def _close(self):
        """关闭视图"""
        self.on_close()

class HTTPStreamViewer(Frame):
    def __init__(self, screen, streams):
        super().__init__(screen, screen.height, screen.width, title="HTTP Streams")
        
        # 使用相同的白底配色方案
        self.palette = {
            "background": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE),
            "shadow": (Screen.COLOUR_BLACK, None, Screen.COLOUR_BLACK),
            "title": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_WHITE),
            "label": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE),
            "borders": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE),
            "list_item": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE),
            "focus_list_item": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLUE),
            "button": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
            "focus_button": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLUE),
        }
        
        # 创建两列布局
        layout = Layout([1, 2], fill_frame=True)
        self.add_layout(layout)
        
        # 左侧列表
        self.stream_list = ListBox(
            height=screen.height - 4,
            options=[(str(stream), i) for i, stream in enumerate(streams)],
            on_select=self._on_stream_select
        )
        layout.add_widget(self.stream_list, 0)
        
        # 右侧详情视图
        self.stream_view = TextBox(
            height=screen.height - 4,
            as_string=True,
            readonly=True
        )
        layout.add_widget(self.stream_view, 1)
        
        # 底部按钮
        button_layout = Layout([1])
        self.add_layout(button_layout)
        button_layout.add_widget(Button("Back", self._back))
        
        self.fix()
        self._streams = streams

    def _on_stream_select(self):
        self.logger.debug("选择了新的 HTTP 流")
        if self.stream_list.value is not None:
            self.logger.debug(f"选择的流索引: {self.stream_list.value}")
            stream = self._streams[self.stream_list.value]
            details = self._format_http_stream(stream)
            self.logger.debug("更新流详情显示")
            self.stream_view.value = details

    def _format_http_stream(self, stream):
        formatted = []
        # 请求部分
        formatted.append("=== HTTP Request ===")
        formatted.append(f"Time: {stream.request['time']}")
        formatted.append(f"Method: {stream.request['method']}")
        formatted.append(f"Path: {stream.request['path']}")
        formatted.append(f"Source: {stream.request['src']}:{stream.request['sport']}")
        formatted.append("\nHeaders:")
        for header, value in stream.request['headers'].items():
            formatted.append(f"  {header}: {value}")
        if stream.request['body']:
            formatted.append("\nBody:")
            formatted.append(stream.request['body'])
        
        # 响应部分
        formatted.append("\n=== HTTP Response ===")
        formatted.append(f"Status: {stream.response['status_code']}")
        formatted.append("\nHeaders:")
        for header, value in stream.response['headers'].items():
            formatted.append(f"  {header}: {value}")
        if stream.response['body']:
            formatted.append("\nBody:")
            formatted.append(stream.response['body'])
        
        return "\n".join(formatted)

    def _back(self):
        raise NextScene("Main")

class WiresharkTUI(Frame):
    def __init__(self, screen, packet_capture):
        self.logger = logging.getLogger('wireshark_tui.ui')
        self.logger.debug("初始化 WiresharkTUI")
        super().__init__(screen, screen.height, screen.width, title="Terminal Wireshark")
        self.packet_capture = packet_capture
        self.logger.debug("WiresharkTUI 初始化完成")
        self._last_frame = 0
        self._packets = []  # 所有数据包
        self._filtered_packets = []  # 过滤后的数据包
        self._filter_logs = []  # 过滤日志
        self._running = True
        
        # 创建主布局
        layout1 = Layout([1], fill_frame=False)
        self.add_layout(layout1)
        
        # 过滤器区域
        layout1.add_widget(Label("Filter Expression:"))
        self.filter_text = Text()
        layout1.add_widget(self.filter_text)
        self.filter_status = Label("")
        layout1.add_widget(self.filter_status)
        
        # 数据包列表区域
        layout1.add_widget(Label("Captured Packets:"))
        self.packet_listbox = ListBox(
            height=10,
            options=[],
            on_select=self._on_packet_select
        )
        layout1.add_widget(self.packet_listbox)
        
        # HTTP流列表区域
        layout1.add_widget(Label("HTTP Streams: (Enter to view details)"))
        self.http_listbox = ListBox(
            height=6,
            options=[],
            on_select=None,
            on_change=self._on_http_change
        )
        layout1.add_widget(self.http_listbox)
        
        # 日志和详情区域
        layout2 = Layout([1, 1])
        self.add_layout(layout2)
        
        # 左侧日志框
        layout2.add_widget(Label("Log: (Enter to view details)"), 0)
        self.log_listbox = ListBox(
            height=8,
            options=[],
            on_select=None,
            on_change=self._on_log_change
        )
        layout2.add_widget(self.log_listbox, 0)
        
        # 右侧详情框
        layout2.add_widget(Label("Details:"), 1)
        self.details_view = TextBox(
            height=8,
            as_string=True,
            readonly=True
        )
        layout2.add_widget(self.details_view, 1)
        
        # 按钮布局
        layout3 = Layout([1, 1, 1])
        self.add_layout(layout3)
        layout3.add_widget(Button("Apply Filter", self._apply_filter), 0)
        layout3.add_widget(Button("Clear", self._clear_filter), 1)
        layout3.add_widget(Button("Help", self._show_help), 2)
        
        # 状态栏
        status_layout = Layout([1])
        self.add_layout(status_layout)
        self.status_label = Label("就绪")
        status_layout.add_widget(self.status_label)
        
        self.fix()

    def _add_filter_log(self, message):
        """添加过滤日志"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}"
            self._filter_logs.append(log_entry)
            
            # 更新日志列表框
            self.log_listbox.options = [
                (log, i) for i, log in enumerate(self._filter_logs)
            ]
            
            # 自动滚动到最新的日志
            if self.log_listbox.options:
                self.log_listbox.value = len(self.log_listbox.options) - 1
                
        except Exception as e:
            print(f"Error adding log: {e}")

    def _show_help(self):
        """显示帮助信息"""
        self.scene.add_effect(
            PopUpDialog(
                self._screen,
                "帮助信息",
                [
                    "使用说明:",
                    "",
                    "1. 过滤器法:",
                    "   - ip.src==1.1.1.1  (源IP)",
                    "   - ip.dst==1.1.1.1  (目标IP)",
                    "   - tcp.port==80     (TCP端口)",
                    "   - udp.port==53     (UDP端口)",
                    "   - http             (HTTP流量)",
                    "   - tcp              (TCP流量)",
                    "",
                    "2. 快捷键:",
                    "   - ↑/↓: 选择数据包",
                    "   - Enter: 查看详情",
                    "   - Tab: 切换焦点",
                    "   - Esc: 退出程序",
                    "",
                    "3. 界面说明:",
                    "   - 上方为数据包列表",
                    "   - 中间为HTTP流列表",
                    "   - 下方左侧为操作日志",
                    "   - 下方右侧为详细信息"
                ],
                ["确定"],
                on_close=self._on_help_close
            )
        )

    def _on_help_close(self, _):
        """处理帮助对话框关闭事件"""
        pass

    def _update_lists(self):
        """更新各个列表"""
        if not self._running:
            return

        try:
            self.logger.debug("开始更新列表")
            # 更新捕获的数据包列表
            packets_updated = False
            while not self.packet_capture.packets.empty():
                try:
                    packet = self.packet_capture.packets.get_nowait()
                    self._packets.insert(0, packet)
                    packets_updated = True
                    self.logger.debug(f"添加新数据包: {packet}")
                except queue.Empty:
                    break

            # 更新过滤后的数据包列表
            while not self.packet_capture.filtered_packets.empty():
                try:
                    packet = self.packet_capture.filtered_packets.get_nowait()
                    self._filtered_packets.insert(0, packet)
                    self._add_filter_log(
                        f"匹配数据包: {packet['src']}:{packet.get('sport','')} -> {packet['dst']}:{packet.get('dport','')}"
                    )
                except queue.Empty:
                    break
            self.logger.debug(f"当前数据包总数: {len(self._packets)}")
            self.logger.debug(f"过滤后数据包数: {len(self._filtered_packets)}")
            self.logger.debug(f"HTTP流数量: {len(self.packet_capture.http_streams)}")

            # 限制表大小
            max_packets = 100000
            if len(self._packets) > max_packets:
                self._packets = self._packets[:max_packets]
            if len(self._filtered_packets) > max_packets:
                self._filtered_packets = self._filtered_packets[:max_packets]

            # 更新数据包列表显示
            if packets_updated:
                self.packet_listbox.options = [
                    (f"#{len(self._packets)-i-1} {packet['src']}:{packet.get('sport','')} -> {packet['dst']}:{packet.get('dport','')}", i)
                    for i, packet in enumerate(self._packets)
                ]

            # 更新HTTP流列表
            self.http_listbox.options = [
                (f"Stream #{i}: {stream.request['method']} {stream.request['path']} -> {stream.response['status_code']}", i)
                for i, stream in enumerate(self.packet_capture.http_streams)
            ]

            # 更新状态栏
            self.status_label.text = (
                f"已捕获: {len(self._packets)} 个数据包, "
                f"过滤: {len(self._filtered_packets)} 个匹配, "
                f"HTTP: {len(self.packet_capture.http_streams)} 个流"
            )

        except Exception as e:
            self.logger.debug(f"更新列表错误: {e}", exc_info=True)
            self._add_filter_log(f"更新错误: {str(e)}")

    def _apply_filter(self):
        """应用过滤器"""
        filter_expr = self.filter_text.value
        self.logger.debug(f"应用新过滤器: {filter_expr}")
        try:
            self.packet_capture.set_filter(filter_expr)
            self.filter_status.text = f"当前过滤器: {filter_expr}" if filter_expr else "无过滤器"
            self._add_filter_log(f"应用过滤器: {filter_expr}")
            self._filtered_packets = []
            self._running = True
            self.logger.debug("过滤器应用成功")
        except ValueError as e:
            # 使用 PopUpDialog 显示错误信息
            self.scene.add_effect(
                PopUpDialog(
                    self._screen,
                    "过滤器错误",
                    [str(e)],
                    ["确定"]
                )
            )
            self.filter_status.text = "过滤器无效"
            self._add_filter_log(f"过滤器错误: {str(e)}")

    def _clear_filter(self):
        """清除过滤器"""
        self.filter_text.value = ""
        self.packet_capture.set_filter(None)
        self.filter_status.text = "已清除过滤器"
        self._add_filter_log("清除过滤器")
        self._filtered_packets = []
        self._running = True

    def _on_packet_select(self):
        """处理数据包选择"""
        if self.packet_listbox.value is not None:
            try:
                packet = self._packets[self.packet_listbox.value]
                details = self._format_packet_details(packet)
                self.details_view.value = details
                self.status_label.text = f"已选择数据包 #{self.packet_listbox.value}"
            except Exception as e:
                self.status_label.text = f"显示数据包详情时出错: {str(e)}"

    def _on_http_change(self):
        """处理 HTTP 流选变化"""
        pass  # 只在按 Enter 时处理

    def _on_log_change(self):
        """处理志选择变化"""
        pass  # 只在按 Enter 时处理

    def process_event(self, event):
        """处理键盘事件"""
        if event is not None and isinstance(event, KeyboardEvent):
            if event.key_code == ord('\n'):  # Enter 键
                # 根据当前焦点显示详情
                focused_widget = self.find_focused_widget()
                if focused_widget == self.http_listbox:
                    self._show_http_details()
                elif focused_widget == self.log_listbox:
                    self._show_log_details()
        return super().process_event(event)

    def find_focused_widget(self):
        """查找当前获得焦点的控件"""
        for layout in self._layouts:
            if hasattr(layout, '_columns'):
                for columns in layout._columns:
                    for widget in columns:
                        if widget and widget._has_focus:
                            return widget
        return None

    def _show_http_details(self):
        """显示 HTTP 流详情"""
        if self.http_listbox.value is not None:
            stream = self.packet_capture.http_streams[self.http_listbox.value]
            details = []
            details.append("=== HTTP 请求 ===")
            details.append(f"时间: {datetime.fromtimestamp(stream.request['time'])}")
            details.append(f"来源: {stream.request['src']}:{stream.request['sport']}")
            details.append(f"方法: {stream.request['method']}")
            details.append(f"路径: {stream.request['path']}")
            details.append("\n请求头:")
            for header, value in stream.request['headers'].items():
                details.append(f"  {header}: {value}")
            if stream.request['body']:
                details.append("\n请求体:")
                details.append(stream.request['body'])
            
            details.append("\n=== HTTP 响应 ===")
            details.append(f"状态码: {stream.response['status_code']}")
            details.append("\n响应头:")
            for header, value in stream.response['headers'].items():
                details.append(f"  {header}: {value}")
            if stream.response['body']:
                details.append("\n响应体:")
                details.append(stream.response['body'])
            
            self.details_view.value = "\n".join(details)

    def _show_log_details(self):
        """显示过滤日志详情"""
        if self.log_listbox.value is not None:
            try:
                packet = self._filtered_packets[self.log_listbox.value]
                details = self._format_packet_details(packet)
                self.details_view.value = details
            except Exception as e:
                self.details_view.value = f"显示详情时出错: {str(e)}"

    def _update_lists(self):
        """更新各个列表"""
        if not self._running:
            return

        try:
            # 更新捕获的数据包列表
            packets_updated = False
            while not self.packet_capture.packets.empty():
                try:
                    packet = self.packet_capture.packets.get_nowait()
                    self._packets.insert(0, packet)
                    packets_updated = True
                except queue.Empty:
                    break

            # 更新过滤后的数据包列表
            filtered_updated = False
            while not self.packet_capture.filtered_packets.empty():
                try:
                    packet = self.packet_capture.filtered_packets.get_nowait()
                    self._filtered_packets.insert(0, packet)
                    filtered_updated = True
                except queue.Empty:
                    break

            # 如果有更新，则刷新显示
            if packets_updated:
                self._update_packet_list()
            if filtered_updated:
                self._update_filtered_list()

            # 更新状态栏
            self.status_label.text = (
                f"已捕获: {len(self._packets)} 个数据包, "
                f"过滤: {len(self._filtered_packets)} 个匹配, "
                f"HTTP: {len(self.packet_capture.http_streams)} 个流"
            )

        except Exception as e:
            self.logger.debug(f"更新列表错误: {e}")
            self._add_filter_log(f"更新错误: {str(e)}")

    def _update_packet_list(self):
        """更新数据包列表显示"""
        self.packet_listbox.options = [
            (f"#{len(self._packets)-i-1} {packet['src']}:{packet.get('sport','')} -> "
             f"{packet['dst']}:{packet.get('dport','')}", i)
            for i, packet in enumerate(self._packets[:1000])  # 限制显示最新的1000个
        ]

    def _update_filtered_list(self):
        """更新过滤后的数据包列表"""
        if self.filter_text.value:
            self.packet_listbox.options = [
                (f"#{len(self._filtered_packets)-i-1} {packet['src']}:{packet.get('sport','')} -> "
                 f"{packet['dst']}:{packet.get('dport','')}", i)
                for i, packet in enumerate(self._filtered_packets[:1000])
            ]

    def _format_packet_details(self, packet):
        """格式化数据包详情"""
        try:
            details = []
            details.append("=== 数据包详情 ===")
            details.append(f"时间: {datetime.fromtimestamp(packet.time).strftime('%Y-%m-%d %H:%M:%S.%f')}")
            details.append(f"长度: {len(packet)} 字节")
            
            # 添加各层的信息
            if packet.haslayer('Ether'):
                details.append("\n=== 以太网层 ===")
                ether = packet['Ether']
                details.append(f"源MAC: {ether.src}")
                details.append(f"目标MAC: {ether.dst}")
            
            if packet.haslayer('IP'):
                details.append("\n=== IP 层 ===")
                ip = packet['IP']
                details.append(f"源IP: {ip.src}")
                details.append(f"目标IP: {ip.dst}")
                details.append(f"协议: {ip.proto}")
                details.append(f"TTL: {ip.ttl}")
            
            if packet.haslayer('TCP'):
                details.append("\n=== TCP 层 ===")
                tcp = packet['TCP']
                details.append(f"源端口: {tcp.sport}")
                details.append(f"目标端口: {tcp.dport}")
                details.append(f"序列号: {tcp.seq}")
                details.append(f"确认号: {tcp.ack}")
                details.append(f"标志: {tcp.flags}")
                details.append(f"窗口大小: {tcp.window}")
            
            if packet.haslayer('UDP'):
                details.append("\n=== UDP 层 ===")
                udp = packet['UDP']
                details.append(f"源端口: {udp.sport}")
                details.append(f"目标端口: {udp.dport}")
                details.append(f"长度: {udp.len}")
            
            if packet.haslayer('HTTP'):
                details.append("\n=== HTTP 层 ===")
                if packet.haslayer('HTTP Request'):
                    details.append("HTTP 请求:")
                    details.append(f"方法: {packet['HTTP Request'].Method.decode()}")
                    details.append(f"路径: {packet['HTTP Request'].Path.decode()}")
                    details.append(f"版本: {packet['HTTP Request'].Http_Version.decode()}")
                elif packet.haslayer('HTTP Response'):
                    details.append("HTTP 响应:")
                    details.append(f"状态码: {packet['HTTP Response'].Status_Code}")
                    details.append(f"原因: {packet['HTTP Response'].Reason_Phrase.decode()}")
            
            return "\n".join(details)
        except Exception as e:
            return f"解析数据包时出错: {str(e)}"

    def update(self, frame_no):
        """定期更新界面"""
        # 增加更新频率
        if frame_no - self._last_frame >= 1:  # 每帧更新
            self._last_frame = frame_no
            self._update_lists()
            
            # 强制重绘
            self._screen.force_update()
            
        super().update(frame_no)

def parse_args():
    parser = argparse.ArgumentParser(description='Terminal Wireshark')
    parser.add_argument('-f', '--filter', 
                       help='Initial filter expression (e.g. "ip.src == 192.168.1.1")',
                       default="")
    parser.add_argument('-i', '--interface',
                       help='Network interface to capture',
                       default=None)
    return parser.parse_args()

def main(screen):
    logger = logging.getLogger('wireshark_tui.main')
    logger.debug("程序启动")
    
    try:
        logger.debug("选择网络接口")
        interface = select_interface(screen)
        if not interface:
            logger.warning("未选择网络接口，程序退出")
            return

        logger.debug(f"选择的网络接口: {interface}")
        
        logger.debug("初始化数据包捕获")
        capture = PacketCapture()
        capture.start_capture(interface)
        
        logger.debug("创建主界面")
        scenes = []
        main_view = WiresharkTUI(screen, capture)
        scenes.append(Scene([main_view], -1))
        
        logger.debug("启动界面循环")
        screen.play(scenes, stop_on_resize=True)
        
    except Exception as e:
        logger.debug(f"程序运行错误: {e}", exc_info=True)
    finally:
        if 'capture' in locals():
            logger.info("正在停止数据包捕获...")
            capture.stop_capture()
        logger.debug("程序结束")

if __name__ == "__main__":
    
    # 设置 scapy 配置
    conf.verb = 0
    conf.use_pcap = False
    conf.use_dnet = False
    conf.save_packets = False
    conf.sniff_promisc = False  # 关闭混杂模式
    conf.promisc = False  # 关闭混杂模式
    conf.monitor = False  # 关闭监控模式
    
    # 设置日志记录
    logger = setup_logging()
    try:
        Screen.wrapper(main)
        logger.debug("程序正常退出")
    except KeyboardInterrupt:
        logger.info("程序被用户终止")
    except Exception as e:
        logger.debug(f"程序异常退出: {e}", exc_info=True)