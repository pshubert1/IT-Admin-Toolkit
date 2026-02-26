"""
Log Analysis Utilities
"""

import tarfile
import os
import re
import shutil
from datetime import datetime


class ESXiLogAnalyzer:
    """Analyzer for ESXi log archives."""
    
    def __init__(self, log_callback=None):
        self.log = log_callback or print
        self.results = {
            'total_files': 0,
            'total_lines': 0,
            'filtered_lines': 0,
            'errors': []
        }
    
    def analyze(self, archive_path, output_path, start_time=None, end_time=None):
        self.results = {
            'total_files': 0,
            'total_lines': 0,
            'filtered_lines': 0,
            'errors': []
        }
        
        extract_dir = os.path.join(os.path.dirname(archive_path), "extracted_logs_temp")
        
        try:
            self.log("📦 Extracting archive...")
            self._extract_archive(archive_path, extract_dir)
            
            log_files = self._find_logs(extract_dir)
            self.results['total_files'] = len(log_files)
            self.log(f"📄 Found {len(log_files)} log files")
            
            if not log_files:
                self.log("⚠️ No .log files found in archive")
                return self.results
            
            if os.path.exists(output_path):
                os.remove(output_path)
            
            for i, log_path in enumerate(log_files):
                log_name = os.path.basename(log_path)
                self.log(f"   Processing ({i+1}/{len(log_files)}): {log_name}")
                self._analyze_log(log_path, output_path, start_time, end_time)
            
            self.log(f"✅ Analysis complete!")
            self.log(f"   📊 Total lines scanned: {self.results['total_lines']}")
            self.log(f"   📋 Lines matching filter: {self.results['filtered_lines']}")
            self.log(f"📄 Output saved to: {output_path}")
            
        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            self.results['errors'].append(str(e))
        finally:
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir, ignore_errors=True)
        
        return self.results
    
    def _extract_archive(self, file_path, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        with tarfile.open(file_path, 'r:*') as tar:
            tar.extractall(output_dir)
    
    def _find_logs(self, directory):
        log_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.log'):
                    log_files.append(os.path.join(root, file))
        return log_files
    
    def _analyze_log(self, log_path, output_path, start_time=None, end_time=None):
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as log_file:
                with open(output_path, 'a', encoding='utf-8') as output:
                    for line in log_file:
                        self.results['total_lines'] += 1
                        
                        match = re.match(r"^(\d{4}-\d{2}-\d{2}T?\d{2}:\d{2}:\d{2})", line)
                        if match:
                            try:
                                fmt = "%Y-%m-%dT%H:%M:%S" if "T" in match.group(1) else "%Y-%m-%d %H:%M:%S"
                                log_time = datetime.strptime(match.group(1), fmt)
                                
                                if start_time and log_time < start_time:
                                    continue
                                if end_time and log_time > end_time:
                                    continue
                                
                                output.write(line)
                                self.results['filtered_lines'] += 1
                            except ValueError:
                                pass
        except Exception as e:
            self.results['errors'].append(f"{os.path.basename(log_path)}: {e}")


class GenericLogAnalyzer:
    """Analyzer for generic text log files."""
    
    def __init__(self, log_callback=None):
        self.log = log_callback or print
        self.results = {
            'total_lines': 0,
            'filtered_lines': 0,
            'matched_lines': []
        }
    
    TIMESTAMP_PATTERNS = [
        (r'^(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})', '%Y-%m-%dT%H:%M:%S'),
        (r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', '%Y-%m-%d %H:%M:%S'),
        (r'^(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})', '%m/%d/%Y %H:%M:%S'),
        (r'^(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})', '%m-%d-%Y %H:%M:%S'),
        (r'^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', '%Y-%m-%d %H:%M:%S'),
        (r'^(\w{3} \d{1,2} \d{2}:\d{2}:\d{2})', '%b %d %H:%M:%S'),
    ]
    
    def analyze(self, log_path, output_path=None, start_time=None, end_time=None, 
                keywords=None, regex_pattern=None, case_sensitive=False):
        self.results = {
            'total_lines': 0,
            'filtered_lines': 0,
            'matched_lines': []
        }
        
        self.log(f"📄 Analyzing: {os.path.basename(log_path)}")
        
        try:
            regex = None
            if regex_pattern:
                try:
                    flags = 0 if case_sensitive else re.IGNORECASE
                    regex = re.compile(regex_pattern, flags)
                except re.error as e:
                    self.log(f"⚠️ Invalid regex pattern: {e}")
                    return self.results
            
            if keywords and not case_sensitive:
                keywords = [k.lower() for k in keywords]
            
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    self.results['total_lines'] += 1
                    
                    if self._matches_filters(line, start_time, end_time, keywords, regex, case_sensitive):
                        self.results['filtered_lines'] += 1
                        self.results['matched_lines'].append(line)
            
            if output_path and self.results['matched_lines']:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.writelines(self.results['matched_lines'])
                self.log(f"💾 Saved {self.results['filtered_lines']} lines to: {output_path}")
            
            self.log(f"✅ Complete: {self.results['filtered_lines']}/{self.results['total_lines']} lines matched")
            
        except FileNotFoundError:
            self.log(f"❌ File not found: {log_path}")
        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
        
        return self.results
    
    def _matches_filters(self, line, start_time, end_time, keywords, regex, case_sensitive):
        if start_time or end_time:
            log_time = self._extract_timestamp(line)
            if log_time:
                if start_time and log_time < start_time:
                    return False
                if end_time and log_time > end_time:
                    return False
            elif start_time or end_time:
                return False
        
        if keywords:
            search_line = line if case_sensitive else line.lower()
            if not any(kw in search_line for kw in keywords):
                return False
        
        if regex:
            if not regex.search(line):
                return False
        
        return True
    
    def _extract_timestamp(self, line):
        for pattern, fmt in self.TIMESTAMP_PATTERNS:
            match = re.search(pattern, line)
            if match:
                try:
                    if '%b' in fmt:
                        ts_str = f"{datetime.now().year} {match.group(1)}"
                        return datetime.strptime(ts_str, f"%Y {fmt}")
                    return datetime.strptime(match.group(1), fmt)
                except ValueError:
                    continue
        return None
    
    def get_log_stats(self, log_path):
        stats = {
            'total_lines': 0,
            'file_size': 0,
            'first_timestamp': None,
            'last_timestamp': None,
            'sample_lines': []
        }
        
        try:
            stats['file_size'] = os.path.getsize(log_path)
            
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f):
                    stats['total_lines'] += 1
                    
                    if i < 10:
                        stats['sample_lines'].append(line.rstrip())
                    
                    ts = self._extract_timestamp(line)
                    if ts:
                        if stats['first_timestamp'] is None:
                            stats['first_timestamp'] = ts
                        stats['last_timestamp'] = ts
                        
        except Exception as e:
            self.log(f"❌ Error reading file: {e}")
        
        return stats


class WindowsEventLogAnalyzer:
    """Analyzer for Windows Event Logs."""
    
    def __init__(self, log_callback=None):
        self.log = log_callback or print
        self.results = {
            'total_events': 0,
            'events': []
        }
    
    def get_available_logs(self):
        import subprocess
        
        try:
            result = subprocess.run(
                ["powershell", "-Command", 
                 "Get-WinEvent -ListLog * -ErrorAction SilentlyContinue | Where-Object {$_.RecordCount -gt 0} | Select-Object -ExpandProperty LogName | Sort-Object"],
                capture_output=True, text=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                logs = [l.strip() for l in result.stdout.strip().split('\n') if l.strip()]
                return logs
            return ["System", "Application", "Security"]
        except:
            return ["System", "Application", "Security"]
    
    def analyze(self, log_name="System", hours=24, level=None, event_ids=None, keywords=None):
        import subprocess
        from datetime import timedelta
        
        self.results = {'total_events': 0, 'events': []}
        
        self.log(f"🔍 Querying {log_name} log (last {hours} hours)...")
        
        start_time = datetime.now() - timedelta(hours=hours)
        start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        
        filter_parts = [f"LogName='{log_name}'", f"StartTime='{start_str}'"]
        
        if level:
            filter_parts.append(f"Level={level}")
        
        if event_ids:
            ids_str = ','.join(str(id) for id in event_ids)
            filter_parts.append(f"Id={ids_str}")
        
        filter_hash = "@{" + ";".join(filter_parts) + "}"
        
        ps_cmd = f'''
        try {{
            $events = Get-WinEvent -FilterHashtable {filter_hash} -MaxEvents 1000 -ErrorAction Stop
            foreach ($event in $events) {{
                $msg = $event.Message -replace "`r`n", " " -replace "`n", " "
                if ($msg.Length -gt 200) {{ $msg = $msg.Substring(0, 200) + "..." }}
                Write-Output "$($event.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss'))|$($event.Id)|$($event.LevelDisplayName)|$msg"
            }}
        }} catch {{
            Write-Output "ERROR: $_"
        }}
        '''
        
        try:
            result = subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if line.startswith("ERROR:"):
                        self.log(f"⚠️ {line}")
                        continue
                    
                    parts = line.split('|', 3)
                    if len(parts) >= 4:
                        event = {
                            'time': parts[0],
                            'id': parts[1],
                            'level': parts[2],
                            'message': parts[3]
                        }
                        
                        if keywords:
                            if not any(kw.lower() in event['message'].lower() for kw in keywords):
                                continue
                        
                        self.results['events'].append(event)
                        self.results['total_events'] += 1
            
            self.log(f"✅ Found {self.results['total_events']} events")
            
        except subprocess.TimeoutExpired:
            self.log("⚠️ Query timed out")
        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
        
        return self.results
    
    def export(self, output_path):
        if not self.results['events']:
            self.log("⚠️ No events to export")
            return
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("Time\tEvent ID\tLevel\tMessage\n")
                f.write("=" * 100 + "\n")
                for event in self.results['events']:
                    f.write(f"{event['time']}\t{event['id']}\t{event['level']}\t{event['message']}\n")
            
            self.log(f"💾 Exported to: {output_path}")
        except Exception as e:
            self.log(f"❌ Export failed: {e}")