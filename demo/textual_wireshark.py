from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Input, ListView, ListItem, Static, Label
from textual.reactive import reactive
from textual.widget import Widget
from rich.text import Text

import socket
import struct
import time
from datetime import datetime
import logging
import threading
import queue
from typing import Optional, List, Dict, Any
import os
import re
import sys
import select

# 创建logs目录（如果不存在）
if not os.path.exists('logs'):
    os.makedirs('logs')

# 设置日志文件名（使用当前时间）
log_filename = f"logs/capture_{datetime.now().strftime('%Y%m%d')}.log"

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 捕获所有级别的日志
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8')  # 只输出到文件
    ]
)

logger = logging.getLogger(__name__)

# 禁用终端输出
logger.propagate = False

# 确保捕获所有级别的日志
logger.setLevel(logging.DEBUG)

class Packet:
    """数据包对象"""
    def __init__(self, data: bytes, timestamp: float):
        self.data = data
        self.timestamp = timestamp
        self.src_ip = ""
        self.dst_ip = ""
        self.protocol = ""
        self.src_port = 0
        self.dst_port = 0
        self.length = len(data)
        self.info = ""
        self.http_info = {}  # 存储HTTP相关信息
        self.parse()
        
    def parse(self):
        """解析数据包"""
        try:
            # 直接解析 IP 头
            ip_header = self.data[:20]
            iph = struct.unpack('!BBHHHBBH4s4s', ip_header)
            
            version_ihl = iph[0]
            self.protocol = iph[6]
            self.src_ip = socket.inet_ntoa(iph[8])
            self.dst_ip = socket.inet_ntoa(iph[9])
            
            # 获取 IP 头长度
            ihl = version_ihl & 0xF
            iph_length = ihl * 4
            
            # TCP
            if self.protocol == 6:
                self.protocol = "TCP"
                tcp_header = self.data[iph_length:iph_length+20]
                tcph = struct.unpack('!HHLLBBHHH', tcp_header)
                self.src_port = tcph[0]
                self.dst_port = tcph[1]
                
                # 计算TCP数据偏移
                tcp_offset = (tcph[4] >> 4) * 4
                payload_offset = iph_length + tcp_offset
                payload = self.data[payload_offset:]
                
                # 检查是否是HTTP流量
                if self.src_port == 80 or self.dst_port == 80 or \
                   self.src_port == 8080 or self.dst_port == 8080:
                    self._parse_http(payload)
                else:
                    self.info = f"Seq={tcph[2]} Ack={tcph[3]}"
                
            # UDP
            elif self.protocol == 17:
                self.protocol = "UDP"
                udp_header = self.data[iph_length:iph_length+8]
                udph = struct.unpack('!HHHH', udp_header)
                self.src_port = udph[0]
                self.dst_port = udph[1]
                self.info = f"Len={udph[2]}"
                
            # ICMP
            elif self.protocol == 1:
                self.protocol = "ICMP"
                icmp_header = self.data[iph_length:iph_length+4]
                icmph = struct.unpack('!BBH', icmp_header)
                self.info = f"Type={icmph[0]} Code={icmph[1]}"
                
        except Exception as e:
            logger.error(f"数据包解析错误: {e}")

    def _parse_http(self, payload: bytes):
        """解析HTTP协议"""
        try:
            # 尝试解码HTTP内容
            http_data = payload.decode('utf-8', errors='ignore')
            
            # 检查是否为HTTP请求或响应
            if http_data.startswith(('GET ', 'POST ', 'PUT ', 'DELETE ', 'HEAD ', 'OPTIONS ')):
                # HTTP请求
                self.protocol = "HTTP"
                request_line = http_data.split('\r\n')[0]
                method, path, version = request_line.split(' ')
                self.http_info = {
                    'type': 'Request',
                    'method': method,
                    'path': path,
                    'version': version
                }
                self.info = f"{method} {path}"
                
            elif http_data.startswith('HTTP/'):
                # HTTP响应
                self.protocol = "HTTP"
                status_line = http_data.split('\r\n')[0]
                version, status_code, *status_text = status_line.split(' ')
                self.http_info = {
                    'type': 'Response',
                    'version': version,
                    'status_code': status_code,
                    'status_text': ' '.join(status_text)
                }
                self.info = f"{status_code} {' '.join(status_text)}"
                
                # 提取Content-Type (如果存在)
                content_type_match = re.search(r'Content-Type: (.+?)\r\n', http_data)
                if content_type_match:
                    self.http_info['content_type'] = content_type_match.group(1)
                
                # 提取Content-Length (如果存在)
                content_length_match = re.search(r'Content-Length: (\d+)\r\n', http_data)
                if content_length_match:
                    self.http_info['content_length'] = content_length_match.group(1)
                    
        except Exception as e:
            logger.debug(f"HTTP解析错误: {e}")

    def __str__(self) -> str:
        if self.protocol in ("TCP", "UDP"):
            return (f"{datetime.fromtimestamp(self.timestamp).strftime('%H:%M:%S.%f')} "
                   f"{self.src_ip}:{self.src_port} -> {self.dst_ip}:{self.dst_port} "
                   f"[{self.protocol}] {self.length}字节 {self.info}")
        else:
            return (f"{datetime.fromtimestamp(self.timestamp).strftime('%H:%M:%S.%f')} "
                   f"{self.src_ip} -> {self.dst_ip} "
                   f"[{self.protocol}] {self.length}字节 {self.info}")

    def get_details(self) -> str:
        """获取详细信息"""
        details = [
            "=== 数据包详情 ===",
            f"时间: {datetime.fromtimestamp(self.timestamp)}",
            f"长度: {self.length} 字节",
            "",
            "=== IP层 ===",
            f"源IP: {self.src_ip}",
            f"目标IP: {self.dst_ip}",
            f"协议: {self.protocol}",
        ]
        
        if self.protocol in ("TCP", "UDP"):
            details.extend([
                "",
                f"=== {self.protocol}层 ===",
                f"源端口: {self.src_port}",
                f"目标端口: {self.dst_port}",
                f"信息: {self.info}"
            ])
            
        # 添加HTTP信息
        if self.protocol == "HTTP" and self.http_info:
            details.extend([
                "",
                "=== HTTP层 ===",
                f"类型: {self.http_info.get('type', 'Unknown')}"
            ])
            
            if self.http_info.get('type') == 'Request':
                details.extend([
                    f"方法: {self.http_info.get('method', '')}",
                    f"路径: {self.http_info.get('path', '')}",
                    f"版本: {self.http_info.get('version', '')}"
                ])
            else:
                details.extend([
                    f"状态码: {self.http_info.get('status_code', '')}",
                    f"状态信息: {self.http_info.get('status_text', '')}",
                    f"内容类型: {self.http_info.get('content_type', 'N/A')}",
                    f"内容长度: {self.http_info.get('content_length', 'N/A')}"
                ])
            
        # 添加十六进制显示
        details.extend([
            "",
            "=== 原始数据(十六进制) ===",
            self._hex_dump(self.data)
        ])
            
        return "\n".join(details)
        
    def _hex_dump(self, data: bytes, bytes_per_line: int = 16) -> str:
        """生成十六进制显示"""
        hex_lines = []
        for i in range(0, len(data), bytes_per_line):
            chunk = data[i:i+bytes_per_line]
            # 十六进制部分
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            # ASCII部分
            ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
            # 补齐空格
            hex_part = f"{hex_part:<{bytes_per_line*3}}"
            # 组合行
            hex_lines.append(f"{i:04x}  {hex_part}  |{ascii_part}|")
        return "\n".join(hex_lines)

class PacketCapture:
    """数据包捕获类"""
    def __init__(self):
        self.sock = None
        self.running = False
        self.packets: queue.Queue = queue.Queue(maxsize=10000)  # 增大队列容量
        self.capture_thread: Optional[threading.Thread] = None
        self.packet_list: List[Packet] = []
        
    def start(self, interface: str):
        """启动捕获"""
        try:
            # 在 macOS 上直接使用 BPF 方式
            if sys.platform == 'darwin':
                return self._start_bpf(interface)
            
            # Linux 系统使用 AF_PACKET
            self.sock = socket.socket(
                socket.AF_PACKET,
                socket.SOCK_RAW,
                socket.ntohs(3)  # ETH_P_ALL
            )
            
            # 设置更大的接收缓冲区
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2**25)  # 32MB
            self.sock.settimeout(0.001)  # 降低超时时间，提高捕获频率
            
            # 绑定到指定接口
            self.sock.bind((interface, 0))
            
            self.running = True
            self.capture_thread = threading.Thread(target=self._capture_loop)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
        except Exception as e:
            logger.error(f"启动捕获失败: {e}")
            raise
    
    def _start_bpf(self, interface: str):
        """macOS 上使用 BPF 捕获"""
        try:
            logger.debug(f"开始在接口 {interface} 上启动捕获...")
            
            # 创建原始套接字
            self.sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_RAW,
                socket.IPPROTO_IP
            )
            logger.debug("套接字创建成功")
            
            # 绑定到指定接口和 IP
            import netifaces
            if netifaces.AF_INET in netifaces.ifaddresses(interface):
                ip = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
            else:
                ip = '0.0.0.0'
            
            self.sock.bind((ip, 0))
            logger.debug(f"绑定到 IP: {ip} 成功")
            
            # 设置基本选项
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            logger.debug("基本套接字选项设置完成")
            
            # 设置接收缓冲区
            try:
                current_buffer = self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
                new_buffer = min(4 * 1024 * 1024, current_buffer * 2)
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, new_buffer)
                logger.debug(f"接收缓冲区设置成功: {new_buffer} 字节")
            except Exception as e:
                logger.warning(f"设置接收缓冲区失败: {e}")
            
            # 设置超时
            self.sock.settimeout(0.001)
            logger.debug("超时设置完成")
            
            # 启用混杂模式
            try:
                os.system(f'sudo ifconfig {interface} promisc')
                os.system('sudo sysctl -w net.inet.ip.forwarding=1')
                logger.debug("系统混杂模式设置完成")
            except Exception as e:
                logger.warning(f"设置混杂模式失败: {e}")
                
            # 启动捕获线程
            self.interface = interface
            self.running = True
            self.capture_thread = threading.Thread(target=self._capture_loop)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            logger.debug("捕获线程已启动")
            
        except Exception as e:
            logger.error(f"BPF 捕获启动失败: {e}")
            raise
    
    def _capture_loop(self):
        """捕获循环"""
        buffer_size = 65535
        packet_count = 0
        last_print = time.time()
        
        logger.debug("进入捕获循环")
        while self.running:
            try:
                ready = select.select([self.sock], [], [], 0.001)
                if ready[0]:
                    logger.debug("select 检测到数据可读")
                    data = self.sock.recv(buffer_size)
                    logger.debug(f"接收到数据: {len(data)} 字节")
                    if data:
                        # 打印原始数据的前100个字节的十六进制
                        logger.debug(f"数据内容(前100字节): {data[:100].hex()}")
                        packet_count += 1
                        current_time = time.time()
                        
                        if current_time - last_print >= 1.0:
                            logger.debug(f"已捕获 {packet_count} 个数据包")
                            last_print = current_time
                        
                        try:
                            packet = Packet(data, time.time())
                            logger.debug(f"解析后的数据包: {packet}")
                            
                            try:
                                self.packets.put_nowait(packet)
                                self.packet_list.append(packet)
                                logger.debug("数据包已添加到队列和列表")
                            except queue.Full:
                                logger.debug("数据包队列已满")
                                continue
                                
                        except Exception as e:
                            logger.debug(f"数据包处理错误: {e}")
                            continue
                else:
                    logger.debug("select 未检测到数据")
                        
            except socket.timeout:
                logger.debug("套接字超时")
                continue
            except socket.error as e:
                if not self.running:
                    break
                logger.error(f"接收数据包错误: {e}")
                time.sleep(0.1)
                continue
            except Exception as e:
                logger.error(f"捕获循环错误: {e}")
                if not self.running:
                    break
                time.sleep(0.1)
        
        logger.debug("退出捕获循环")

    def stop(self):
        """停止捕获"""
        try:
            self.running = False
            if self.capture_thread and self.capture_thread.is_alive():
                self.capture_thread.join(timeout=1.0)
            if self.sock:
                self.sock.close()
                self.sock = None
                
            # 清理系统设置
            try:
                # 关闭混杂模式
                os.system(f'sudo ifconfig {self.interface} -promisc')
                # 停止 tcpdump
                os.system('sudo pkill tcpdump')
                # 删除临时文件
                os.system('rm -f /tmp/capture.pcap')
            except:
                pass
                
        except Exception as e:
            logger.error(f"停止捕获时出错: {e}")

class FilterInput(Input):
    """过滤输入框"""
    def __init__(self):
        super().__init__(placeholder="输入过滤条件 (例如: tcp/udp/http/ip=192.168.1.1/port=80)")
        
    def on_change(self, event):
        """当输入变化时触发过滤"""
        self.parent.apply_filter(self.value)

class FilteredPacketList(ListView):
    """过滤后的数据包列表"""
    def compose(self) -> ComposeResult:
        yield ListItem(Label("等待数据包..."))
        
    def add_packet(self, packet: Packet):
        """添加数据包到列表"""
        self.mount(ListItem(Label(str(packet))))
        # 保持最新的1000个数据包
        if len(self.children) > 1000:
            self.children[0].remove()

class TrafficMonitor(Static):
    """流量监控组件"""
    def __init__(self):
        super().__init__("等待流量数据...")
        self.last_bytes = 0
        self.last_time = time.time()
        self.current_speed = 0
        self.total_bytes = 0
        self.start_time = time.time()
        self.packet_count = 0
        
    def update_traffic(self, total_bytes: int, packet_count: int):
        """更新流量数据"""
        current_time = time.time()
        time_diff = current_time - self.last_time
        
        if time_diff > 0:
            bytes_diff = total_bytes - self.last_bytes
            self.current_speed = bytes_diff / time_diff
            self.last_bytes = total_bytes
            self.last_time = current_time
            self.total_bytes = total_bytes
            self.packet_count = packet_count
            
            # 计算平均速度
            avg_speed = self.total_bytes / (current_time - self.start_time)
            
            # 格式化显示
            current_speed_text = self._format_speed(self.current_speed)
            avg_speed_text = self._format_speed(avg_speed)
            total_bytes_text = self._format_bytes(self.total_bytes)
            
            print(f"流量更新 - 当前速度: {current_speed_text}, 平均速度: {avg_speed_text}, 总流量: {total_bytes_text}")
            
            # 更新显示
            self.update(
                f"当前流量: {current_speed_text}\n"
                f"平均流量: {avg_speed_text}\n"
                f"总流量: {total_bytes_text}\n"
                f"数据包数: {self.packet_count}"
            )
            
    def _format_speed(self, speed: float) -> str:
        """格式化速度显示"""
        if speed < 1024:
            return f"{speed:.1f} B/s"
        elif speed < 1024*1024:
            return f"{speed/1024:.1f} KB/s"
        else:
            return f"{speed/(1024*1024):.1f} MB/s"
            
    def _format_bytes(self, bytes: int) -> str:
        """格式化字节显示"""
        if bytes < 1024:
            return f"{bytes} B"
        elif bytes < 1024*1024:
            return f"{bytes/1024:.1f} KB"
        elif bytes < 1024*1024*1024:
            return f"{bytes/(1024*1024):.1f} MB"
        else:
            return f"{bytes/(1024*1024*1024):.1f} GB"

class MainContent(Container):
    """主内容区域"""
    def __init__(self):
        super().__init__()
        self.filter_input = FilterInput()
        self.filtered_list = FilteredPacketList()
        self.traffic_monitor = TrafficMonitor()
        self.filter_condition = ""
        
    def compose(self) -> ComposeResult:
        """构建界面"""
        with Horizontal():
            # 左侧部分
            with Vertical():
                yield self.filter_input
                yield self.filtered_list
            
            # 右侧部分
            with Vertical():
                yield self.traffic_monitor
                
    def apply_filter(self, filter_text: str):
        """应用过滤条件"""
        self.filter_condition = filter_text.lower()
        self.refresh_filtered_list()
        
    def refresh_filtered_list(self):
        """刷新过滤后的列表"""
        self.filtered_list.clear()
        
        if hasattr(self, 'capture'):
            for packet in self.capture.packet_list:
                if self._packet_matches_filter(packet):
                    self.filtered_list.add_packet(packet)
                    
    def _packet_matches_filter(self, packet: Packet) -> bool:
        """检查数据包是否匹配过滤条件"""
        if not self.filter_condition:
            return True
            
        filter_parts = self.filter_condition.split('/')
        for part in filter_parts:
            if not part:
                continue
                
            if '=' in part:
                key, value = part.split('=', 1)
                if key == 'ip':
                    if value not in (packet.src_ip, packet.dst_ip):
                        return False
                elif key == 'port':
                    port = int(value)
                    if port not in (packet.src_port, packet.dst_port):
                        return False
            else:
                if part == 'tcp' and packet.protocol != 'TCP':
                    return False
                elif part == 'udp' and packet.protocol != 'UDP':
                    return False
                elif part == 'http' and packet.protocol != 'HTTP':
                    return False
                    
        return True

class PacketDetails(Static):
    """数据包详情组件"""
    def __init__(self):
        super().__init__("选择数据包查看详情", markup=False)
        
    def show_packet(self, packet: Packet):
        """显示数据包详情"""
        self.update(packet.get_details())

class WiresharkApp(App):
    """主应用类"""
    CSS = """
    MainContent {
        height: 70%;
        border: solid green;
    }
    
    Horizontal {
        height: 100%;
    }
    
    Vertical {
        width: 50%;
        height: 100%;
    }
    
    FilterInput {
        dock: top;
        width: 100%;
        height: 3;
        border: solid blue;
    }
    
    FilteredPacketList {
        width: 100%;
        height: 1fr;
        border: solid red;
    }
    
    TrafficMonitor {
        width: 100%;
        height: 100%;
        border: solid yellow;
        content-align: center middle;
    }
    
    PacketDetails {
        height: 30%;
        border: solid blue;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "退出"),
        Binding("c", "clear", "清除"),
    ]
    
    def __init__(self, interface: str):
        super().__init__()
        self.interface = interface
        self.capture = PacketCapture()
        self.main_content = MainContent()
        self.packet_details = PacketDetails()
        
    def compose(self) -> ComposeResult:
        """构建界面"""
        yield Header()
        yield self.main_content
        yield self.packet_details
        yield Footer()
        
    def on_mount(self) -> None:
        """挂载启动捕获"""
        self.capture.start(self.interface)
        self.set_interval(0.1, self.update_display)
        
    def update_display(self):
        """更新显示"""
        try:
            packets_count = len(self.capture.packet_list)
            total_bytes = sum(packet.length for packet in self.capture.packet_list)
            
            logger.debug(f"更新显示 - 数据包数: {packets_count}, 总字节数: {total_bytes}")
            
            # 更新流量监控
            self.main_content.traffic_monitor.update_traffic(total_bytes, packets_count)
            
            # 批量处理数据包
            processed_count = 0
            while not self.capture.packets.empty():
                try:
                    packet = self.capture.packets.get_nowait()
                    if self.main_content._packet_matches_filter(packet):
                        self.main_content.filtered_list.add_packet(packet)
                    processed_count += 1
                except queue.Empty:
                    break
                    
            if processed_count > 0:
                logger.debug(f"本次更新处理了 {processed_count} 个数据包")
                
        except Exception as e:
            logger.error(f"更新显示时出错: {e}")

    def on_list_view_selected(self, message: ListView.Selected) -> None:
        """处理列表选择事件"""
        if isinstance(message.item, ListItem):
            try:
                # 获取选中的数据包并显示详情
                selected_index = len(self.main_content.filtered_list.children) - self.main_content.filtered_list.children.index(message.item) - 1
                if 0 <= selected_index < len(self.capture.packet_list):
                    packet = self.capture.packet_list[selected_index]
                    self.packet_details.show_packet(packet)
            except Exception as e:
                logger.error(f"显示数据包详情出错: {e}")
                self.packet_details.update(f"显示数据包详情时出错: {str(e)}")

    def action_quit(self):
        """退出动作"""
        try:
            if hasattr(self, 'capture'):
                self.capture.stop()
        except Exception as e:
            logger.error(f"退出时停止捕获出错: {e}")
        finally:
            self.exit()
        
    def action_clear(self):
        """清除动作"""
        self.main_content.filtered_list.clear()
        self.packet_details.update("选择数据包查看详情")
        # 同时清除捕获器中的数据包列表
        self.capture.packet_list.clear()
        while not self.capture.packets.empty():
            try:
                self.capture.packets.get_nowait()
            except queue.Empty:
                break

def get_interfaces() -> List[Dict[str, Any]]:
    """获取网络接口列表
    Returns:
        List[Dict[str, Any]]: 包含接口信息的字典列表，每个字典包含:
            - name: 接口名称
            - ip: IP地址
            - active: 是否激活
    """
    interfaces = []
    try:
        import netifaces
        # 获取所有网络接口
        for iface in netifaces.interfaces():
            try:
                # 获取接口地址信息
                addrs = netifaces.ifaddresses(iface)
                # 获取IPv4地址
                if netifaces.AF_INET in addrs:
                    ip = addrs[netifaces.AF_INET][0]['addr']
                    # 检查接口是否活跃
                    is_active = False
                    try:
                        # 检查接口状态
                        if os.name == 'nt':  # Windows
                            import subprocess
                            output = subprocess.check_output(['netsh', 'interface', 'show', 'interface', iface])
                            is_active = b'Connected' in output
                        else:  # Unix/Linux/MacOS
                            with open(f'/sys/class/net/{iface}/operstate', 'r') as f:
                                state = f.read().strip()
                                is_active = state == 'up'
                    except:
                        # 如果无法检查状态，但有IP地址，则认为活跃的
                        is_active = True
                    
                    # 过滤掉回环口和非活跃接口
                    if not iface.startswith('lo') and ip != '127.0.0.1' and is_active:
                        interfaces.append({
                            'name': iface,
                            'ip': ip,
                            'active': is_active
                        })
            except:
                continue
                
    except ImportError:
        logger.warning("netifaces 库未安装，使用备用方法")
        try:
            import socket
            import fcntl
            import struct
            
            def get_ip_address(ifname):
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    ip = socket.inet_ntoa(fcntl.ioctl(
                        s.fileno(),
                        0x8915,  # SIOCGIFADDR
                        struct.pack('256s', ifname[:15].encode())
                    )[20:24])
                    return ip
                except:
                    return None
                finally:
                    s.close()
            
            # 从 /sys/class/net 读取
            for iface in os.listdir('/sys/class/net/'):
                if not iface.startswith('lo'):
                    try:
                        # 检查接口是否活跃
                        with open(f'/sys/class/net/{iface}/operstate', 'r') as f:
                            state = f.read().strip()
                            is_active = state == 'up'
                            
                        if is_active:
                            ip = get_ip_address(iface)
                            if ip:
                                interfaces.append({
                                    'name': iface,
                                    'ip': ip,
                                    'active': True
                                })
                    except:
                        continue
                        
        except Exception as e:
            logger.error(f"获取网络接口失败: {e}")
            
    return interfaces

def main():
    # 检查是否有root权限
    if os.geteuid() != 0:
        print("错误: 需要root权限能捕获数据包")
        print("请使用 sudo 运行此程序")
        exit(1)
        
    try:
        # 获取网络接口
        interfaces = get_interfaces()
        if not interfaces:
            print("未找到可用的网络接口")
            exit(1)
            
        # 打印可用接口列表
        print("\n可用网络接口:")
        print("序号  接口名��     IP地址          状态")
        print("-" * 45)
        for i, iface in enumerate(interfaces, 1):
            status = "活跃" if iface['active'] else "非活跃"
            print(f"{i:<5} {iface['name']:<11} {iface['ip']:<15} {status}")
            
        # 让用户选择接口
        while True:
            try:
                choice = input("\n请选择网络接口 (输入编号): ")
                index = int(choice) - 1
                if 0 <= index < len(interfaces):
                    interface = interfaces[index]['name']
                    print(f"\n使用网络接口: {interface} ({interfaces[index]['ip']})")
                    break
                else:
                    print("无效的选择，请重试")
            except ValueError:
                print("请输入有效的数字")
                
        # 启动应用
        app = WiresharkApp(interface)
        app.run()
        
    except KeyboardInterrupt:
        print("\n程序被用户终止")
    except Exception as e:
        print(f"程序错误: {e}")
        logger.exception("程序异常退出")

if __name__ == "__main__":
    main()

