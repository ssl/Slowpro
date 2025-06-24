#!/usr/bin/env python3
"""
Slowpro - Web Performance Testing Tool

A browser-based performance monitoring tool that captures and analyzes 
network requests to identify performance bottlenecks in web applications.

Author: github.com/ssl (Elyesa)
Version: 1.0.0
"""

import json
import csv
import time
import urllib.parse
import threading
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from seleniumbase import Driver
from selenium.common.exceptions import WebDriverException, NoSuchWindowException

# Banner
BANNER = """                                                                                                                                    
 ▗▄▄▖█  ▄▄▄  ▄   ▄ ▄▄▄▄   ▄▄▄ ▄▄▄  
▐▌   █ █   █ █ ▄ █ █   █ █   █   █    v1.0.0
 ▝▀▚▖█ ▀▄▄▄▀ █▄█▄█ █▄▄▄▀ █   ▀▄▄▄▀    github.com/ssl
▗▄▄▞▘█             █                           
"""


class SlowproError(Exception):
    """Base exception for Slowpro errors."""
    pass


class BrowserError(SlowproError):
    """Browser-related errors."""
    pass


class DataError(SlowproError):
    """Data processing errors."""
    pass


class Slowpro:
    """
    Performance tester that captures all network requests.
    
    This class provides comprehensive web performance monitoring by:
    - Capturing network requests via browser performance API
    - Analyzing response times and sizes
    - Organizing data by domain and session
    - Providing real-time monitoring feedback
    """
    
    # Define consistent CSV fieldnames for all record types
    CSV_FIELDNAMES = [
        'url', 'domain', 'timestamp', 'type', 'method', 'status', 
        'response_time_ms', 'response_size', 'content_type', 
        'request_id', 'initiator', 'resource_type'
    ]
    
    def __init__(self, output_dir: str = "performance_data"):
        """
        Initialize Slowpro performance tester.
        
        Args:
            output_dir: Directory to store performance data files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.performance_data: Dict[str, List[Dict]] = {}
        self.driver: Optional[Driver] = None
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.network_events: List[Dict] = []
        self.session_start = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def setup_browser(self, headless: bool = False) -> bool:
        """
        Setup Chrome browser with network monitoring capabilities.
        
        Args:
            headless: Whether to run browser in headless mode
            
        Returns:
            True if browser setup successful, False otherwise
        """
        try:
            self.driver = Driver(
                browser="chrome", 
                headless=headless,
                incognito=False,
                guest_mode=False,
                undetectable=True,
                page_load_strategy="normal"
            )
            
            # Enable Network and Runtime domains via CDP
            try:
                self.driver.execute_cdp_cmd('Network.enable', {})
                self.driver.execute_cdp_cmd('Runtime.enable', {})
                print("✅ Browser initialized with CDP network monitoring")
            except Exception as e:
                print(f"⚠️ CDP not available ({e}), using alternative monitoring")
            
            print("✅ Browser initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize browser: {e}")
            raise BrowserError(f"Browser initialization failed: {e}")
    
    def get_domain(self, url: str) -> str:
        """
        Extract domain from URL safely.
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain name or 'unknown' if extraction fails
        """
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            parsed = urllib.parse.urlparse(url)
            return parsed.netloc or "unknown"
        except Exception:
            return "unknown"
    
    def get_network_requests_from_browser(self) -> List[Dict]:
        """
        Get network requests from browser's performance API.
        
        Returns:
            List of network request dictionaries, or None if browser is closed
        """
        network_requests = []
        
        try:
            # Check if browser is still available
            if not self.driver:
                return None
                
            # Get all performance entries from browser
            network_data = self.driver.execute_script("""
                // Get all performance entries
                const entries = performance.getEntriesByType('navigation').concat(
                    performance.getEntriesByType('resource')
                );
                
                return entries.map(entry => ({
                    name: entry.name,
                    initiatorType: entry.initiatorType || 'unknown',
                    duration: entry.duration,
                    responseStart: entry.responseStart,
                    responseEnd: entry.responseEnd,
                    transferSize: entry.transferSize || 0,
                    entryType: entry.entryType,
                    startTime: entry.startTime,
                    // Create a stable identifier for deduplication
                    entryId: entry.name + '_' + entry.startTime + '_' + entry.duration
                }));
            """)
            
            # Handle case where network_data might be None or empty
            if not network_data:
                return network_requests
            
            # Process the performance entries
            for entry in network_data:
                if entry['name'] and entry['name'].startswith('http'):
                    network_request = {
                        'url': entry['name'],
                        'domain': self.get_domain(entry['name']),
                        'timestamp': datetime.now().isoformat(),
                        'type': 'network_request',
                        'method': 'GET',  # Default, as we can't get actual method from performance API
                        'status': 200,  # Assume success if it loaded
                        'response_time_ms': round(entry.get('duration', 0), 2),
                        'response_size': entry.get('transferSize', 0),
                        'content_type': self._guess_content_type(entry['name']),
                        'request_id': entry['entryId'],  # Use stable ID for deduplication
                        'initiator': entry.get('initiatorType', 'unknown'),
                        'resource_type': self._map_initiator_to_type(entry.get('initiatorType', 'unknown')),
                        'start_time': entry.get('startTime', 0)
                    }
                    network_requests.append(network_request)
                    
        except (WebDriverException, NoSuchWindowException):
            # Browser window closed
            return None
        except Exception as e:
            if "no such window" in str(e).lower() or "target window already closed" in str(e).lower():
                return None
            print(f"⚠️ Error collecting network data: {e}")
        
        return network_requests
    
    def _guess_content_type(self, url: str) -> str:
        """
        Guess content type from URL.
        
        Args:
            url: URL to analyze
            
        Returns:
            Guessed content type string
        """
        url_lower = url.lower()
        
        content_type_mapping = {
            ('.js', 'javascript'): 'application/javascript',
            ('.css', 'stylesheet'): 'text/css',
            ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'): 'image/*',
            ('.json', 'api/', '/api'): 'application/json',
            ('.html',): 'text/html'
        }
        
        for extensions, content_type in content_type_mapping.items():
            if any(ext in url_lower for ext in extensions):
                return content_type
                
        return 'unknown'
    
    def _map_initiator_to_type(self, initiator: str) -> str:
        """
        Map performance API initiator to resource type.
        
        Args:
            initiator: Initiator type from performance API
            
        Returns:
            Mapped resource type
        """
        mapping = {
            'navigation': 'Document',
            'script': 'Script',
            'link': 'Stylesheet',
            'img': 'Image',
            'xmlhttprequest': 'XHR',
            'fetch': 'Fetch',
            'other': 'Other'
        }
        return mapping.get(initiator.lower(), 'Other')
    
    def monitor_network_activity(self) -> None:
        """Continuously monitor network activity in a separate thread."""
        processed_request_ids = set()
        
        while self.monitoring:
            try:
                if not self.driver:
                    print("🔒 Browser session ended")
                    self.monitoring = False
                    break
                
                # Check if browser window still exists
                try:
                    self.driver.current_url  # This will fail if window is closed
                except (WebDriverException, NoSuchWindowException):
                    print("👋 Browser window closed - ending session")
                    self.monitoring = False
                    break
                
                # Get current network requests
                current_requests = self.get_network_requests_from_browser()
                
                # Handle case where network_data might be None
                if current_requests is None:
                    print("👋 Browser session ended - stopping monitoring")
                    self.monitoring = False
                    break
                
                # Process only new requests using stable IDs
                new_requests = []
                for request in current_requests:
                    request_id = request['request_id']
                    if request_id not in processed_request_ids:
                        new_requests.append(request)
                        processed_request_ids.add(request_id)
                
                # Store new requests
                for request in new_requests:
                    domain = request['domain']
                    if domain not in self.performance_data:
                        self.performance_data[domain] = []
                    
                    self.performance_data[domain].append(request)
                    
                    # Show real-time feedback for interesting requests
                    resource_type = request.get('resource_type', '')
                    if resource_type in ['XHR', 'Fetch', 'Document', 'Script'] and request['response_time_ms'] > 0:
                        url_display = request['url'][:60] + "..." if len(request['url']) > 60 else request['url']
                        print(f"📡 {resource_type}: {url_display} ({request['response_time_ms']}ms)")
                
                # Save data if we have new requests
                if new_requests:
                    self.save_data()
                
                time.sleep(3)  # Check every 3 seconds
                
            except (WebDriverException, NoSuchWindowException):
                print("👋 Browser window closed - ending session")
                self.monitoring = False
                break
            except Exception as e:
                # Check if it's a browser-related error
                if "no such window" in str(e).lower() or "target window already closed" in str(e).lower():
                    print("👋 Browser window closed - ending session")
                    self.monitoring = False
                    break
                else:
                    print(f"⚠️ Error in network monitoring: {e}")
                    time.sleep(5)
    
    def start_monitoring(self) -> None:
        """Start automatic network monitoring in background thread."""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self.monitor_network_activity, daemon=True)
            self.monitor_thread.start()
            print("🔍 Network monitoring started - capturing all requests")
    
    def stop_monitoring(self) -> None:
        """Stop automatic network monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=3)
        print("⏹️  Network monitoring stopped")
    
    def navigate_to(self, url: str) -> bool:
        """
        Navigate to specified URL.
        
        Args:
            url: URL to navigate to
            
        Returns:
            True if navigation successful, False otherwise
        """
        if not self.driver:
            print("❌ Browser not initialized. Call setup_browser() first.")
            return False
            
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            print(f"🌐 Navigating to: {url}")
            
            # Navigate to page
            self.driver.get(url)
            
            # Give time for page and resources to load
            time.sleep(4)
            
            print(f"✅ Navigation to {url} completed")
            return True
            
        except Exception as e:
            print(f"❌ Error navigating to {url}: {e}")
            return False
    
    def save_data(self) -> None:
        """Save performance data to JSON and CSV files organized by domain."""
        try:
            for domain, data in self.performance_data.items():
                if not data:
                    continue
                    
                domain_dir = self.output_dir / domain
                domain_dir.mkdir(exist_ok=True)
                
                # Use session timestamp for consistent filenames
                json_file = domain_dir / f"session_{self.session_start}.json"
                csv_file = domain_dir / f"session_{self.session_start}.csv"
                
                # Save as JSON (overwrite with latest data)
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
                
                # Save as CSV with consistent fieldnames
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.CSV_FIELDNAMES, extrasaction='ignore')
                    writer.writeheader()
                    for row in data:
                        # Fill missing fields with default values
                        complete_row = {field: row.get(field, '') for field in self.CSV_FIELDNAMES}
                        writer.writerow(complete_row)
            
            total_requests = sum(len(data) for data in self.performance_data.values())
            if total_requests > 0:
                print(f"💾 Saved {total_requests} network requests to {self.output_dir}")
            
        except Exception as e:
            print(f"❌ Error saving data: {e}")
            raise DataError(f"Failed to save data: {e}")
    
    def start_interactive_session(self) -> None:
        """Start performance testing session with automatic monitoring."""
        print(BANNER)
        
        if not self.setup_browser():
            return
            
        # Start automatic monitoring
        self.start_monitoring()
            
        print(f"\n🚀 Slowpro Performance Testing Session Started! (ID: {self.session_start})")
        print("📍 Browser opened - browse any websites normally!")
        print("\n🔍 Automatic network monitoring active:")
        print("   • All page loads are captured")
        print("   • Resource downloads (CSS, JS, images) are tracked")
        print("   • API calls and AJAX requests are monitored")
        print("   • Real-time performance feedback is shown")
        
        print(f"\n💡 Just browse normally! Close the browser window or press Ctrl+C to end the session.")
        print(f"📊 Data will be saved to: {self.output_dir}")
        print("\n" + "="*60)
        
        try:
            # Keep the main thread alive while monitoring
            while self.monitoring:
                try:
                    time.sleep(1)
                    # Check if browser is still open
                    if self.driver:
                        try:
                            self.driver.current_url
                        except (WebDriverException, NoSuchWindowException):
                            print("\n👋 Browser window closed - ending session")
                            break
                    else:
                        break
                except KeyboardInterrupt:
                    print("\n👋 Session ended by user (Ctrl+C)")
                    break
                    
        except KeyboardInterrupt:
            print("\n👋 Session ended by user (Ctrl+C)")
        finally:
            self.stop_monitoring()
            # Final save
            self.save_data()
            
            total_requests = sum(len(data) for data in self.performance_data.values())
            if total_requests > 0:
                print(f"\n📊 Session Summary:")
                print(f"   • Captured {total_requests} network requests")
                print(f"   • Monitored {len(self.performance_data)} domains")
                print(f"   • Data saved to {self.output_dir}")
                print(f"\n🎯 Generate report with: python report_generator.py")
            
            if self.driver:
                try:
                    self.driver.quit()
                    print("🔒 Browser closed")
                except Exception:
                    pass


def main() -> None:
    """Main function to run the Slowpro performance tester."""
    try:
        tester = Slowpro()
        tester.start_interactive_session()
    except KeyboardInterrupt:
        print("\n👋 Slowpro session terminated")
    except Exception as e:
        print(f"❌ Slowpro error: {e}")


if __name__ == "__main__":
    main()
