"""
Network Debugging Utilities
"""

import subprocess
import socket
import re
from datetime import datetime


class NetworkDebugger:
    """Network debugging tools."""
    
    def __init__(self, log_callback=None):
        self.log = log_callback or print
    
    def _run_command(self, cmd, timeout=30):
        """Run a command and return output."""
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
        """Ping a target."""
        self.log(f"🏓 Pinging {target} ({count} packets)...")
        
        output, success = self._run_command(["ping", "-n", str(count), target])
        
        # Parse results
        if success:
            # Extract statistics
            if "Average" in output:
                for line in output.split('\n'):
                    if "Minimum" in line or "Average" in line:
                        self.log(f"   {line.strip()}")
                self.log("✅ Ping successful")
            elif "Request timed out" in output:
                self.log("⚠️ Request timed out")
            elif "could not find host" in output.lower():
                self.log("❌ Could not resolve hostname")
        else:
            self.log("❌ Ping failed")
        
        return output, success
    
    def traceroute(self, target, max_hops=30):
        """Traceroute to target."""
        self.log(f"🔍 Tracing route to {target} (max {max_hops} hops)...")
        self.log("   This may take a moment...")
        
        output, success = self._run_command(
            ["tracert", "-h", str(max_hops), target], 
            timeout=120
        )
        
        if success:
            self.log("✅ Traceroute complete")
        else:
            self.log("❌ Traceroute failed")
        
        return output, success
    
    def nslookup(self, target, dns_server=None):
        """DNS lookup."""
        self.log(f"🔎 Looking up {target}...")
        
        cmd = ["nslookup", target]
        if dns_server:
            cmd.append(dns_server)
        
        output, success = self._run_command(cmd)
        
        if success:
            self.log("✅ DNS lookup complete")
        else:
            self.log("❌ DNS lookup failed")
        
        return output, success
    
    def port_check(self, target, port, timeout=5):
        """Check if a port is open."""
        self.log(f"🔌 Checking {target}:{port}...")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((target, int(port)))
            sock.close()
            
            if result == 0:
                self.log(f"✅ Port {port} is OPEN")
                return f"Port {port} is OPEN on {target}", True
            else:
                self.log(f"❌ Port {port} is CLOSED/FILTERED")
                return f"Port {port} is CLOSED/FILTERED on {target}", False
        except socket.gaierror:
            self.log(f"❌ Could not resolve {target}")
            return f"Could not resolve hostname: {target}", False
        except Exception as e:
            self.log(f"❌ Error: {e}")
            return str(e), False
    
    def port_scan(self, target, ports=None):
        """Scan common ports."""
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
        
        self.log(f"✅ Scan complete: {len(open_ports)} open ports found")
        return "\n".join(results), True
    
    def get_ip_config(self):
        """Get IP configuration."""
        self.log("📋 Getting IP configuration...")
        output, success = self._run_command(["ipconfig", "/all"])
        return output, success
    
    def flush_dns(self):
        """Flush DNS cache."""
        self.log("🧹 Flushing DNS cache...")
        output, success = self._run_command(["ipconfig", "/flushdns"])
        
        if success:
            self.log("✅ DNS cache flushed")
        else:
            self.log("❌ Failed to flush DNS (need admin?)")
        
        return output, success
    
    def release_renew_ip(self):
        """Release and renew IP address."""
        self.log("🔄 Releasing IP address...")
        output1, _ = self._run_command(["ipconfig", "/release"])
        
        self.log("🔄 Renewing IP address...")
        output2, success = self._run_command(["ipconfig", "/renew"], timeout=60)
        
        if success:
            self.log("✅ IP renewed successfully")
        else:
            self.log("⚠️ IP renewal may have issues")
        
        return output1 + "\n" + output2, success
    
    def get_arp_table(self):
        """Get ARP table."""
        self.log("📋 Getting ARP table...")
        output, success = self._run_command(["arp", "-a"])
        return output, success
    
    def get_netstat(self, show_all=False):
        """Get network connections."""
        self.log("📋 Getting network connections...")
        
        cmd = ["netstat", "-ano"]
        if show_all:
            cmd = ["netstat", "-ano", "-p", "tcp"]
        
        output, success = self._run_command(cmd)
        return output, success
    
    def get_route_table(self):
        """Get routing table."""
        self.log("📋 Getting routing table...")
        output, success = self._run_command(["route", "print"])
        return output, success
    
    def whois(self, target):
        """Basic whois-like info using nslookup."""
        self.log(f"🔎 Getting info for {target}...")
        
        results = []
        
        # Get IP
        try:
            ip = socket.gethostbyname(target)
            results.append(f"IP Address: {ip}")
            self.log(f"   IP: {ip}")
        except:
            results.append(f"Could not resolve: {target}")
        
        # Get reverse DNS
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            results.append(f"Hostname: {hostname}")
            self.log(f"   Hostname: {hostname}")
        except:
            results.append("Reverse DNS: Not available")
        
        # Get DNS records
        output, _ = self._run_command(["nslookup", "-type=any", target])
        results.append("\nDNS Records:\n" + output)
        
        return "\n".join(results), True
    
    def test_internet(self):
        """Quick internet connectivity test."""
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
                if isinstance(result, tuple):
                    success = result[1]
                else:
                    success = True
                
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
            self.log("✅ Internet connectivity: OK")
        else:
            self.log("⚠️ Internet connectivity: Issues detected")
        
        return "\n".join(results), all_passed
    
    def get_wifi_info(self):
        """Get WiFi information."""
        self.log("📶 Getting WiFi information...")
        output, success = self._run_command(
            ["netsh", "wlan", "show", "interfaces"]
        )
        return output, success
    
    def get_wifi_networks(self):
        """Get available WiFi networks."""
        self.log("📶 Scanning WiFi networks...")
        output, success = self._run_command(
            ["netsh", "wlan", "show", "networks", "mode=bssid"]
        )
        return output, success