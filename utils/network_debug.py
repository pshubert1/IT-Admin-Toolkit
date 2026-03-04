"""
Network Debugging Utilities
"""

import subprocess
import socket


class NetworkDebugger:
    """Network debugging tools."""
    
    def __init__(self, app=None, log_callback=None):
        self.app = app
        self._log = log_callback or (app.log if app else print)
    
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
    
    def _run_command(self, cmd, timeout=30):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.stdout + result.stderr, result.returncode == 0
        except subprocess.TimeoutExpired:
            return "Command timed out", False
        except Exception as e:
            return str(e), False
    
    def ping(self, target, count=4):
        self.log(f"🏓 Pinging {target} ({count} packets)...")
        output, success = self._run_command(["ping", "-n", str(count), target])
        
        if success:
            if "Average" in output:
                for line in output.split('\n'):
                    if "Minimum" in line or "Average" in line:
                        self.log(f"   {line.strip()}")
                self.log_success("Ping successful")
            elif "Request timed out" in output:
                self.log_warning("Request timed out")
            elif "could not find host" in output.lower():
                self.log_error("Could not resolve hostname",
                    hint="Check the hostname spelling or DNS settings")
        else:
            self.log_error("Ping failed",
                hint="Check network connection and target address")
        
        return output, success
    
    def traceroute(self, target, max_hops=30):
        self.log(f"🔍 Tracing route to {target} (max {max_hops} hops)...")
        self.log("   This may take a moment...")
        
        output, success = self._run_command(
            ["tracert", "-h", str(max_hops), target], timeout=120
        )
        
        if success:
            self.log_success("Traceroute complete")
        else:
            self.log_error("Traceroute failed",
                hint="Target may be unreachable or blocking ICMP")
        
        return output, success
    
    def nslookup(self, target, dns_server=None):
        self.log(f"🔎 Looking up {target}...")
        cmd = ["nslookup", target]
        if dns_server:
            cmd.append(dns_server)
        
        output, success = self._run_command(cmd)
        
        if success:
            self.log_success("DNS lookup complete")
        else:
            self.log_error("DNS lookup failed",
                hint="Check DNS settings or try a different DNS server")
        
        return output, success
    
    def port_check(self, target, port, timeout=5):
        self.log(f"🔌 Checking {target}:{port}...")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((target, int(port)))
            sock.close()
            
            if result == 0:
                self.log_success(f"Port {port} is OPEN")
                return f"Port {port} is OPEN on {target}", True
            else:
                self.log_error(f"Port {port} is CLOSED/FILTERED",
                    hint="A firewall may be blocking this port")
                return f"Port {port} is CLOSED/FILTERED on {target}", False
        except socket.gaierror:
            self.log_error(f"Could not resolve {target}",
                hint="Check the hostname spelling")
            return f"Could not resolve hostname: {target}", False
        except Exception as e:
            self.log_error(f"Port check error: {e}")
            return str(e), False
    
    def port_scan(self, target, ports=None):
        if ports is None:
            ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 993, 995, 3389, 8080]
        
        self.log(f"🔍 Scanning {target} ({len(ports)} ports)...")
        
        results = []
        open_ports = []
        
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((target, port))
                sock.close()
                
                status = "OPEN" if result == 0 else "CLOSED"
                results.append(f"Port {port}: {status}")
                
                if result == 0:
                    open_ports.append(port)
                    self.log(f"   ✅ Port {port}: OPEN")
            except:
                results.append(f"Port {port}: ERROR")
        
        self.log_success(f"Scan complete: {len(open_ports)} open ports found")
        return "\n".join(results), True
    
    def get_ip_config(self):
        self.log("📋 Getting IP configuration...")
        output, success = self._run_command(["ipconfig", "/all"])
        return output, success
    
    def flush_dns(self):
        self.log("🧹 Flushing DNS cache...")
        output, success = self._run_command(["ipconfig", "/flushdns"])
        
        if success:
            self.log_success("DNS cache flushed")
        else:
            self.log_error("Failed to flush DNS",
                hint="Run the app as Administrator")
        
        return output, success
    
    def release_renew_ip(self):
        self.log("🔄 Releasing IP address...")
        output1, _ = self._run_command(["ipconfig", "/release"])
        
        self.log("🔄 Renewing IP address...")
        output2, success = self._run_command(["ipconfig", "/renew"], timeout=60)
        
        if success:
            self.log_success("IP renewed successfully")
        else:
            self.log_warning("IP renewal may have issues",
                hint="Check if DHCP server is reachable")
        
        return output1 + "\n" + output2, success
    
    def get_arp_table(self):
        self.log("📋 Getting ARP table...")
        return self._run_command(["arp", "-a"])
    
    def get_netstat(self, show_all=False):
        self.log("📋 Getting network connections...")
        cmd = ["netstat", "-ano"]
        if show_all:
            cmd = ["netstat", "-ano", "-p", "tcp"]
        return self._run_command(cmd)
    
    def get_route_table(self):
        self.log("📋 Getting routing table...")
        return self._run_command(["route", "print"])
    
    def whois(self, target):
        self.log(f"🔎 Getting info for {target}...")
        results = []
        
        try:
            ip = socket.gethostbyname(target)
            results.append(f"IP Address: {ip}")
            self.log(f"   IP: {ip}")
        except:
            results.append(f"Could not resolve: {target}")
            self.log_error(f"Could not resolve: {target}")
        
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            results.append(f"Hostname: {hostname}")
            self.log(f"   Hostname: {hostname}")
        except:
            results.append("Reverse DNS: Not available")
        
        output, _ = self._run_command(["nslookup", "-type=any", target])
        results.append("\nDNS Records:\n" + output)
        
        return "\n".join(results), True
    
    def test_internet(self):
        self.log("🌐 Testing internet connectivity...")
        
        tests = [
            ("DNS Resolution", lambda: socket.gethostbyname("google.com")),
            ("Google Ping", lambda: self._run_command(["ping", "-n", "1", "8.8.8.8"], timeout=5)),
            ("HTTPS (443)", lambda: self.port_check("google.com", 443, timeout=3)),
        ]
        
        results = []
        all_passed = True
        
        for name, test in tests:
            try:
                result = test()
                success = result[1] if isinstance(result, tuple) else True
                status = "✅ PASS" if success else "❌ FAIL"
                results.append(f"{name}: {status}")
                
                if success:
                    self.log(f"   ✅ {name}: PASS")
                else:
                    self.log(f"   ❌ {name}: FAIL")
                    all_passed = False
            except Exception as e:
                results.append(f"{name}: ❌ FAIL ({e})")
                self.log(f"   ❌ {name}: FAIL")
                all_passed = False
        
        if all_passed:
            self.log_success("Internet connectivity: OK")
        else:
            self.log_warning("Internet connectivity: Issues detected",
                hint="Check network adapter and router")
        
        return "\n".join(results), all_passed
    
    def get_wifi_info(self):
        self.log("📶 Getting WiFi information...")
        return self._run_command(["netsh", "wlan", "show", "interfaces"])
    
    def get_wifi_networks(self):
        self.log("📶 Scanning WiFi networks...")
        return self._run_command(["netsh", "wlan", "show", "networks", "mode=bssid"])