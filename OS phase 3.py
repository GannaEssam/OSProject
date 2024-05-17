import tkinter as tk
from tkinter import ttk

class CombinedMonitor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Combined Monitor")
        self.geometry("800x600")

        self.tabControl = ttk.Notebook(self)
        self.processMonitorTab = ttk.Frame(self.tabControl)
        self.systemMonitorTab = ttk.Frame(self.tabControl)
        self.filesystemMonitorTab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.processMonitorTab, text="Process Monitor")
        self.tabControl.add(self.systemMonitorTab, text="System Monitor")
        self.tabControl.add(self.filesystemMonitorTab, text="File Systems")
        self.tabControl.pack(expand=1, fill="both")

        self.create_process_monitor()
        self.create_system_monitor()
        self.create_file_system_monitor()

    def create_process_monitor(self):
        self.process_text = tk.Text(self.processMonitorTab)
        self.process_text.pack(fill="both", expand=True)
        self.update_process_info()

    def create_system_monitor(self):
        self.system_text = tk.Text(self.systemMonitorTab)
        self.system_text.pack(fill="both", expand=True)
        self.update_system_info()

    def create_file_system_monitor(self):
        self.filesystem_text = tk.Text(self.filesystemMonitorTab)
        self.filesystem_text.pack(fill="both", expand=True)
        self.update_file_system_info()


    def read_process_info(self): 
        process_info = ""
        try:
            for pid in range(1, 32768):
                try:
                    with open(f'/proc/{pid}/stat', 'r') as pid_stat_file:
                        stat_parts = pid_stat_file.readline().split()
                        command = stat_parts[1][1:-1]
                        cpu_time = float(stat_parts[13]) + float(stat_parts[14])
                        process_info += f"PID: {pid}, Command: {command}, CPU Time: {cpu_time:.2f}\n"
                except FileNotFoundError:
                    continue
        except Exception as e:
            process_info += f"Error: {e}\n"
        return process_info
    
    def update_process_info(self): 
        try:
            process_info = self.read_process_info()
            self.process_text.config(state="normal")
            self.process_text.delete("1.0", "end")
            self.process_text.insert("1.0", process_info)
            self.process_text.config(state="disabled")
        except Exception as e:
            print("Error:", e)
        self.after(1000, self.update_process_info)
        
    def get_disk_usage(self, path): 
        total_blocks = 0
        used_blocks = 0
        
        with open('/proc/partitions', 'r') as file:
            for line in file:
                if 'sd' in line or 'hd' in line or 'vd' in line:
                    fields = line.split()
                    total_blocks += int(fields[2])
        
        with open('/proc/diskstats', 'r') as file:
            for line in file:
                fields = line.split()
                if 'sd' in fields[2] or 'hd' in fields[2] or 'vd' in fields[2]:
                    major_minor = f"{fields[0]}:{fields[1]}"
                    with open(f'/sys/class/block/{fields[2]}/stat', 'r') as stat_file:
                        stats = stat_file.readline().split()
                        used_blocks += int(stats[2]) + int(stats[10])
        
        total_size = total_blocks * 1024  
        used_size = used_blocks * 1024
        return total_size / (1024**2), used_size / (1024**2)  
    
    def update_system_info(self): 
        try:
            cpu_usage = self.get_cpu_usage()
            memory_usage = self.get_memory_usage()
            swap_usage = self.get_swap_usage()
            disk_usage = self.get_fulldisk_usage()
        
            system_info = (
                f"CPU Usage: {cpu_usage}%\n"
                f"Memory Usage: {memory_usage}%\n"
                f"Swap Usage: {swap_usage}%\n"
                f"Disk Usage: {disk_usage}%\n"
            )

            self.system_text.config(state="normal")
            self.system_text.delete("1.0", "end")
            self.system_text.insert("1.0", system_info)
            self.system_text.config(state="disabled")
        except Exception as e:
            print("Error:", e)
        self.after(1000, self.update_system_info)

    def get_file_system_info(self): 
        try:
            filesystem_info = ""
            with open('/proc/mounts', 'r') as file:
                for line in file:
                    if line.startswith('/dev/'):
                        fields = line.split()
                        device, mountpoint, fstype, options = fields[:4]
                        if 'rw' in options:  
                            try:
                                total_size, used_size = self.get_disk_usage(mountpoint)
                                total_gb_str = f"{total_size:.2f} GB"
                                used_gb_str = f"{used_size:.2f} GB"
                                usage_percent = (used_size / total_size) * 100
                                filesystem_info += f"Device: {device}, Mountpoint: {mountpoint}, Type: {fstype}, Total: {total_gb_str}, Used: {used_gb_str} ({usage_percent:.2f}%)\n"
                            except Exception as e:
                                print(f"Error reading {mountpoint}: {e}")
            return filesystem_info
        except Exception as e:
            print(f"Error reading file systems: {e}")
            return "Unknown"

    def update_file_system_info(self): 
        try:
            filesystem_info = self.get_file_system_info()

            self.filesystem_text.config(state="normal")
            self.filesystem_text.delete("1.0", "end")
            self.filesystem_text.insert("1.0", filesystem_info)
            self.filesystem_text.config(state="disabled")
        except Exception as e:
            print("Error:", e)
        self.after(1000, self.update_file_system_info)

    def get_cpu_usage(self): 
        try:
            with open('/proc/stat', 'r') as file:
                lines = file.readlines()
                cpu_info = lines[0].split()[1:]
                total_cpu_time = sum(map(int, cpu_info))
                idle_cpu_time = int(cpu_info[3])
                cpu_usage = 100 * (1 - idle_cpu_time / total_cpu_time)
                return f"{cpu_usage:.2f}"
        except Exception as e:
            print(f"Error getting CPU usage: {e}")
            return "Unknown"

    def get_memory_usage(self): 
        try:
            with open('/proc/meminfo', 'r') as file:
                lines = file.readlines()
                total_mem = int(lines[0].split()[1])
                free_mem = int(lines[1].split()[1])
                used_mem = total_mem - free_mem
                mem_percent = (used_mem / total_mem) * 100
                return f"{mem_percent:.2f}"
        except Exception as e:
            print(f"Error getting memory usage: {e}")
            return "Unknown"

    def get_swap_usage(self): 
        try:
            with open('/proc/meminfo', 'r') as file:
                lines = file.readlines()
                total_swap = int(lines[14].split()[1])
                free_swap = int(lines[15].split()[1])
                used_swap = total_swap - free_swap
                swap_percent = (used_swap / total_swap) * 100
                return f"{swap_percent:.2f}"
        except Exception as e:
            print(f"Error getting swap usage: {e}")
            return "Unknown"

    def get_fulldisk_usage(self): 
        try:
            total_blocks = 0
            used_blocks = 0
            
            with open('/proc/partitions', 'r') as file:
                for line in file:
                    if 'sd' in line or 'hd' in line or 'vd' in line:
                        fields = line.split()
                        total_blocks += int(fields[2])
            
            with open('/proc/diskstats', 'r') as file:
                for line in file:
                    fields = line.split()
                    if 'sd' in fields[2] or 'hd' in fields[2] or 'vd' in fields[2]:
                        major_minor = f"{fields[0]}:{fields[1]}"
                        with open(f'/sys/class/block/{fields[2]}/stat', 'r') as stat_file:
                            stats = stat_file.readline().split()
                            used_blocks += int(stats[2]) + int(stats[10])
            
            disk_percent = (used_blocks / total_blocks) * 100
            return f"{disk_percent:.2f}"
        
        except Exception as e:
            print(f"Error getting disk usage: {e}")
            return "Unknown"



if __name__ == "__main__":
    app = CombinedMonitor()
    app.mainloop()

