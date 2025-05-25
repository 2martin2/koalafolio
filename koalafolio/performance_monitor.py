# -*- coding: utf-8 -*-
"""
Performance monitoring for koalafolio startup optimization

This module provides tools to measure and analyze startup performance.
"""

import time
import sys
import os
import psutil
import threading
from contextlib import contextmanager


class StartupProfiler:
    """Profile startup performance and resource usage"""
    
    def __init__(self):
        self.start_time = None
        self.checkpoints = []
        self.memory_usage = []
        self.monitoring = False
        self.monitor_thread = None
    
    def start(self):
        """Start profiling"""
        self.start_time = time.time()
        self.checkpoints = []
        self.memory_usage = []
        self.monitoring = True
        
        # Start memory monitoring in background
        self.monitor_thread = threading.Thread(target=self._monitor_memory)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.checkpoint("Profiling started")
    
    def checkpoint(self, description):
        """Add a checkpoint with description"""
        if self.start_time is None:
            return
        
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # Get current memory usage
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        checkpoint = {
            'time': elapsed,
            'description': description,
            'memory_mb': memory_mb,
            'timestamp': current_time
        }
        
        self.checkpoints.append(checkpoint)
        print(f"[{elapsed:.2f}s] {description} (Memory: {memory_mb:.1f} MB)")
    
    def stop(self):
        """Stop profiling and return results"""
        if self.start_time is None:
            return None
        
        self.monitoring = False
        self.checkpoint("Profiling stopped")
        
        total_time = time.time() - self.start_time
        
        results = {
            'total_time': total_time,
            'checkpoints': self.checkpoints,
            'memory_usage': self.memory_usage,
            'peak_memory': max(self.memory_usage) if self.memory_usage else 0
        }
        
        return results
    
    def _monitor_memory(self):
        """Monitor memory usage in background"""
        process = psutil.Process()
        
        while self.monitoring:
            try:
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.memory_usage.append(memory_mb)
                time.sleep(0.1)  # Sample every 100ms
            except:
                break
    
    def print_summary(self, results=None):
        """Print a summary of the profiling results"""
        if results is None:
            results = self.stop()
        
        if results is None:
            print("No profiling data available")
            return
        
        print("\n" + "="*60)
        print("STARTUP PERFORMANCE SUMMARY")
        print("="*60)
        print(f"Total startup time: {results['total_time']:.2f} seconds")
        print(f"Peak memory usage: {results['peak_memory']:.1f} MB")
        print()
        
        print("Checkpoints:")
        print("-" * 40)
        for i, checkpoint in enumerate(results['checkpoints']):
            if i > 0:
                prev_time = results['checkpoints'][i-1]['time']
                delta = checkpoint['time'] - prev_time
                print(f"  {checkpoint['time']:6.2f}s (+{delta:5.2f}s) - {checkpoint['description']}")
            else:
                print(f"  {checkpoint['time']:6.2f}s          - {checkpoint['description']}")
        
        print("\nSlowest operations:")
        print("-" * 40)
        # Calculate deltas and sort by slowest
        deltas = []
        for i in range(1, len(results['checkpoints'])):
            prev_time = results['checkpoints'][i-1]['time']
            curr_time = results['checkpoints'][i]['time']
            delta = curr_time - prev_time
            deltas.append((delta, results['checkpoints'][i]['description']))
        
        deltas.sort(reverse=True)
        for delta, description in deltas[:5]:  # Top 5 slowest
            print(f"  {delta:5.2f}s - {description}")


@contextmanager
def profile_startup():
    """Context manager for easy startup profiling"""
    profiler = StartupProfiler()
    profiler.start()
    try:
        yield profiler
    finally:
        results = profiler.stop()
        profiler.print_summary(results)


def profile_imports():
    """Profile import times for heavy modules"""
    print("Profiling import times...")
    
    imports_to_test = [
        ('PyQt5.QtWidgets', 'PyQt5 Widgets'),
        ('PyQt5.QtCore', 'PyQt5 Core'),
        ('PyQt5.QtGui', 'PyQt5 GUI'),
        ('pandas', 'Pandas'),
        ('requests', 'Requests'),
        ('web3', 'Web3'),
        ('koalafolio.PcpCore.core', 'Koalafolio Core'),
        ('koalafolio.gui.QThreads', 'Koalafolio Threads'),
    ]
    
    results = []
    
    for module_name, display_name in imports_to_test:
        start_time = time.time()
        try:
            __import__(module_name)
            import_time = time.time() - start_time
            results.append((import_time, display_name, 'Success'))
        except ImportError as e:
            import_time = time.time() - start_time
            results.append((import_time, display_name, f'Failed: {e}'))
    
    # Sort by import time
    results.sort(reverse=True)
    
    print("\nImport Performance:")
    print("-" * 50)
    for import_time, display_name, status in results:
        print(f"{import_time:6.3f}s - {display_name:25s} - {status}")


if __name__ == '__main__':
    # Run import profiling
    profile_imports()
    
    print("\nTo profile full application startup, run:")
    print("python -c \"from koalafolio.performance_monitor import profile_startup; from koalafolio.gui_root import main; import koalafolio.performance_monitor as pm; profiler = pm.StartupProfiler(); profiler.start(); main()\"")
