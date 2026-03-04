"""
Network Diagnostics Utility
"""

import subprocess
import socket
import os
from datetime import datetime


class NetworkDiagnostics:
    def __init__(self, app=None, log_callback=None):
        self.app = app
        self._log = log_callback or (app.log if app else print)
        self.results = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'tests': [],
            'internet_access': False
        }
    
    def log(self, msg):
        self._log(msg)
    
    def log_error(self, msg, hint=None):
        if self.app and hasattr(self.app, 'log_error'):
            self.app.log_error(msg, hint)
        else:
            self._log(f"❌ {msg}")
    
    def log_warning(self, msg, hint=None):
        if self.app and hasattr(self.app, 'log_warning'):
            self.app.log_warning(msg, hint)
        else:
            self._log(f"⚠️ {msg}")
    
    def log_success(self, msg):
        if self.app and hasattr(self.app, 'log_success'):
            self.app.log_success(msg)
        else:
            self._log(f"✅ {msg}")
    
    def run_all(self, save_report=True):
        """Run all network diagnostics."""
        self.log("═══════════════════════════════════════════════════")
        self.log("🌐 NETWORK DIAGNOSTICS")
        self.log("═══════════════════════════════════════════════════")
        
        self._test_adapters()
        self._test_gateway()
        self._test_dns_config()
        self._test_dns_resolution()
        self._test_website_ping()
        self._test_public_dns()
        self._test_ports()
        self._show_summary()
        
        if save_report:
            self._save_report()
        
        return self.results
    
    def _run_command(self, cmd, timeout=10):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.stdout, result.returncode == 0
        except:
            return "", False
    
    def _test_adapters(self):
        self.log("")
        self.log("📡 1. NETWORK ADAPTERS")
        
        output, success = self._run_command(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command", 
             "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | "
             "Select-Object Name, Status, LinkSpeed | Format-Table -AutoSize"]
        )
        
        if success and output.strip():
            for line in output.strip().split('\n'):
                if line.strip() and '---' not in line and 'Name' not in line:
                    self.log(f"   ✅ {line.strip()}")
            self.results['tests'].append(('Adapters', True, 'Active adapters found'))
        else:
            self.log_error("No active network adapters",
                hint="Check if WiFi or Ethernet is enabled")
            self.results['tests'].append(('Adapters', False, 'No active adapters'))
    
    def _test_gateway(self):
        self.log("")
        self.log("🚪 2. DEFAULT GATEWAY")
        
        output, _ = self._run_command(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command",
             "(Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Select-Object -First 1).NextHop"]
        )
        
        gateway = output.strip()
        if gateway:
            self.log(f"   Gateway: {gateway}")
            ping_result = self._ping(gateway)
            if ping_result:
                self.log_success(f"Gateway reachable ({ping_result}ms)")
                self.results['tests'].append(('Gateway', True, f'{gateway} - {ping_result}ms'))
            else:
                self.log_error("Gateway unreachable",
                    hint="Check physical network connection")
                self.results['tests'].append(('Gateway', False, 'Unreachable'))
        else:
            self.log_error("No gateway configured",
                hint="Check network adapter settings or DHCP")
            self.results['tests'].append(('Gateway', False, 'Not configured'))
    
    def _test_dns_config(self):
        self.log("")
        self.log("📋 3. DNS SERVERS")
        
        output, _ = self._run_command(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command",
             "Get-DnsClientServerAddress -AddressFamily IPv4 | "
             "Where-Object {$_.ServerAddresses} | "
             "Select-Object -ExpandProperty ServerAddresses -Unique"]
        )
        
        if output.strip():
            for dns in output.strip().split('\n'):
                if dns.strip():
                    self.log(f"   📍 {dns.strip()}")
        else:
            self.log_warning("No DNS servers configured")
    
    def _test_dns_resolution(self):
        self.log("")
        self.log("🔍 4. DNS RESOLUTION")
        
        sites = ["google.com", "microsoft.com"]
        
        for site in sites:
            try:
                ip = socket.gethostbyname(site)
                self.log_success(f"{site} → {ip}")
                self.results['tests'].append((f'DNS:{site}', True, ip))
            except:
                self.log_error(f"{site} → FAILED",
                    hint="DNS resolution failed. Try flushing DNS: ipconfig /flushdns")
                self.results['tests'].append((f'DNS:{site}', False, 'Resolution failed'))
    
    def _test_website_ping(self):
        self.log("")
        self.log("🌐 5. WEBSITE PING")
        
        sites = ["google.com", "microsoft.com"]
        
        for site in sites:
            latency = self._ping(site)
            if latency:
                self.log_success(f"{site} - {latency}ms")
                self.results['tests'].append((f'Ping:{site}', True, f'{latency}ms'))
                self.results['internet_access'] = True
            else:
                self.log_error(f"{site} - FAILED")
                self.results['tests'].append((f'Ping:{site}', False, 'Timeout'))
    
    def _test_public_dns(self):
        self.log("")
        self.log("📡 6. PUBLIC DNS PING")
        
        dns_servers = [
            ("Google", "8.8.8.8"),
            ("Cloudflare", "1.1.1.1"),
            ("Quad9", "9.9.9.9")
        ]
        
        for name, ip in dns_servers:
            latency = self._ping(ip)
            if latency:
                self.log_success(f"{name} ({ip}) - {latency}ms")
                self.results['tests'].append((f'DNS-Ping:{name}', True, f'{latency}ms'))
            else:
                self.log_error(f"{name} ({ip}) - FAILED")
                self.results['tests'].append((f'DNS-Ping:{name}', False, 'Timeout'))
    
    def _test_ports(self):
        self.log("")
        self.log("🔌 7. PORT CONNECTIVITY")
        
        ports = [
            ("google.com", 80, "HTTP"),
            ("google.com", 443, "HTTPS"),
        ]
        
        for host, port, service in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    self.log_success(f"{service} (port {port}) - Open")
                    self.results['tests'].append((f'Port:{service}', True, 'Open'))
                else:
                    self.log_error(f"{service} (port {port}) - Blocked",
                        hint="A firewall may be blocking this port")
                    self.results['tests'].append((f'Port:{service}', False, 'Blocked'))
            except:
                self.log_error(f"{service} (port {port}) - Error")
                self.results['tests'].append((f'Port:{service}', False, 'Error'))
    
    def _ping(self, host, count=2):
        try:
            output, success = self._run_command(
                ["ping", "-n", str(count), "-w", "2000", host], timeout=10
            )
            if success and "Average" in output:
                for line in output.split('\n'):
                    if "Average" in line:
                        avg = line.split('=')[-1].strip().replace('ms', '')
                        return int(avg)
            return None
        except:
            return None
    
    def _show_summary(self):
        self.log("")
        self.log("═══════════════════════════════════════════════════")
        self.log("📋 SUMMARY")
        self.log("═══════════════════════════════════════════════════")
        
        passed = sum(1 for _, success, _ in self.results['tests'] if success)
        total = len(self.results['tests'])
        
        if self.results['internet_access']:
            self.log_success("Internet: Connected")
        else:
            self.log_error("Internet: Not Connected")
        
        self.log(f"   📊 Tests: {passed}/{total} passed")
        
        failures = [(name, detail) for name, success, detail in self.results['tests'] if not success]
        if failures:
            self.log("")
            self.log_warning("Issues detected:")
            for name, detail in failures:
                self.log(f"      • {name}: {detail}")
            self.log("")
            self.log("   🔧 Quick fixes to try:")
            self.log("      • ipconfig /flushdns")
            self.log("      • ipconfig /release && ipconfig /renew")
            self.log("      • netsh winsock reset")
        else:
            self.log_success("All tests passed!")
    
    def _save_report(self):
        try:
            output_folder = os.path.join(os.environ['USERPROFILE'], 'Desktop', 'Network-Diagnostics')
            os.makedirs(output_folder, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            filepath = os.path.join(output_folder, f"NetworkDiag_{timestamp}.txt")
            
            with open(filepath, 'w') as f:
                f.write(f"Network Diagnostics Report\n")
                f.write(f"Generated: {self.results['timestamp']}\n")
                f.write(f"Computer: {os.environ.get('COMPUTERNAME', 'Unknown')}\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Internet Access: {'Yes' if self.results['internet_access'] else 'No'}\n\n")
                f.write("Test Results:\n")
                for name, success, detail in self.results['tests']:
                    status = "PASS" if success else "FAIL"
                    f.write(f"  [{status}] {name}: {detail}\n")
            
            self.log("")
            self.log_success(f"Report saved: {filepath}")
            os.startfile(output_folder)
            
        except Exception as e:
            self.log_warning(f"Could not save report: {e}")