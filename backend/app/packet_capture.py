import asyncio
from scapy.all import sniff, IP, TCP, UDP, ICMP
from datetime import datetime
from typing import Callable, Optional
import logging

logger = logging.getLogger(__name__)


class PacketCapture:
    """Captura de paquetes de red usando Scapy"""

    def __init__(self, interface: str = None, ports: list[int] = None):
        self.interface = interface
        self.ports = ports or []
        self.running = False
        self.packet_callback: Optional[Callable] = None
        self.capture_thread = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def set_callback(self, callback: Callable):
        """Establece el callback para procesar paquetes"""
        self.packet_callback = callback

    def _build_filter(self) -> str:
        """Construye el filtro BPF para la captura"""
        if not self.ports:
            return "ip"

        port_filters = " or ".join([f"port {port}" for port in self.ports])
        return f"ip and ({port_filters})"

    def _process_packet(self, packet):
        """Procesa un paquete capturado"""
        try:
            if not packet.haslayer(IP):
                return

            ip_layer = packet[IP]

            # Determinar protocolo y puertos
            protocol = "OTHER"
            src_port = 0
            dst_port = 0
            flags = None

            if packet.haslayer(TCP):
                protocol = "TCP"
                tcp_layer = packet[TCP]
                src_port = tcp_layer.sport
                dst_port = tcp_layer.dport
                flags = str(tcp_layer.flags)
            elif packet.haslayer(UDP):
                protocol = "UDP"
                udp_layer = packet[UDP]
                src_port = udp_layer.sport
                dst_port = udp_layer.dport
            elif packet.haslayer(ICMP):
                protocol = "ICMP"

            # Extraer preview del payload
            payload_preview = None
            if packet.haslayer(TCP) or packet.haslayer(UDP):
                try:
                    payload = bytes(packet[TCP].payload if packet.haslayer(TCP) else packet[UDP].payload)
                    if payload:
                        payload_preview = payload[:100].hex()
                except Exception:
                    pass

            packet_data = {
                "source_ip": ip_layer.src,
                "destination_ip": ip_layer.dst,
                "source_port": src_port,
                "destination_port": dst_port,
                "protocol": protocol,
                "packet_size": len(packet),
                "flags": flags,
                "payload_preview": payload_preview,
                "timestamp": datetime.utcnow()
            }

            if self.packet_callback and self.loop:
                # Ejecutar callback en el loop de asyncio desde otro thread
                asyncio.run_coroutine_threadsafe(
                    self.packet_callback(packet_data),
                    self.loop
                )

        except Exception as e:
            logger.error(f"Error processing packet: {e}")

    def start(self):
        """Inicia la captura de paquetes"""
        if self.running:
            logger.warning("Packet capture already running")
            return

        self.running = True
        filter_str = self._build_filter()

        logger.info(f"Starting packet capture on interface {self.interface or 'all'} with filter: {filter_str}")

        try:
            # Sniff en modo promiscuo
            sniff(
                iface=self.interface,
                filter=filter_str,
                prn=self._process_packet,
                store=False,
                stop_filter=lambda x: not self.running
            )
        except PermissionError:
            logger.error("Permission denied. Need root/admin privileges for packet capture")
            self.running = False
        except Exception as e:
            logger.error(f"Error in packet capture: {e}")
            self.running = False

    def stop(self):
        """Detiene la captura de paquetes"""
        logger.info("Stopping packet capture")
        self.running = False

    async def start_async(self):
        """Inicia la captura en un thread separado"""
        self.loop = asyncio.get_event_loop()
        await self.loop.run_in_executor(None, self.start)
