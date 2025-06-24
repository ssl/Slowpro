#!/usr/bin/env python3
"""
Slowpro Report Generator - Interactive Performance Dashboard Generator

Generates comprehensive HTML dashboards from Slowpro performance data,
providing detailed analysis of network requests, response times, and 
resource utilization across domains and sessions.

Author: github.com/ssl (Elyesa)
Version: 1.0.0
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import statistics


class ReportError(Exception):
    """Base exception for report generation errors."""
    pass


class DataLoadError(ReportError):
    """Data loading errors."""
    pass


class DashboardGenerator:
    """
    Generates interactive HTML dashboard from Slowpro performance data.
    
    This class provides comprehensive performance analysis by:
    - Loading and filtering performance data by domain/session
    - Analyzing response times, sizes, and resource types
    - Generating interactive HTML dashboards with filtering capabilities
    - Providing detailed statistics and insights
    """
    
    def __init__(self, data_dir: str = "performance_data"):
        """
        Initialize DashboardGenerator.
        
        Args:
            data_dir: Directory containing performance data files
        """
        self.data_dir = Path(data_dir)
        self.all_data: List[Dict] = []
        self.domains: Dict[str, List[Dict]] = {}
        self.session_info: Dict[str, Dict] = {}
        self.available_domains: List[str] = []
        self.available_sessions: List[str] = []
        
    def discover_data(self) -> bool:
        """
        Discover available domains and sessions from data directory.
        
        Returns:
            True if data found, False otherwise
        """
        print("🔍 Discovering available data...")
        
        # Find all JSON files
        json_files = list(self.data_dir.glob("**/session_*.json"))
        
        if not json_files:
            print("❌ No session JSON files found in the data directory")
            return False
            
        domains = set()
        sessions = set()
        
        for json_file in json_files:
            domain = json_file.parent.name
            session_id = json_file.stem.replace('session_', '')
            domains.add(domain)
            sessions.add(session_id)
            
        self.available_domains = sorted(list(domains))
        self.available_sessions = sorted(list(sessions))
        
        print(f"📊 Found data for {len(self.available_domains)} domains and {len(self.available_sessions)} sessions")
        print(f"🌐 Domains: {', '.join(self.available_domains[:5])}{' and more...' if len(self.available_domains) > 5 else ''}")
        print(f"📅 Sessions: {', '.join(self.available_sessions[:3])}{' and more...' if len(self.available_sessions) > 3 else ''}")
        
        return True
    
    def load_data(self, selected_domains: Optional[List[str]] = None, selected_sessions: Optional[List[str]] = None) -> bool:
        """
        Load JSON data with optional domain/session filtering.
        
        Args:
            selected_domains: List of domains to include (None for all)
            selected_sessions: List of sessions to include (None for all)
            
        Returns:
            True if data loaded successfully, False otherwise
        """
        print("📂 Loading performance data...")
        
        # Find all JSON files
        json_files = list(self.data_dir.glob("**/session_*.json"))
        
        if not json_files:
            print("❌ No session JSON files found in the data directory")
            return False
            
        # Filter files based on selection
        filtered_files = []
        for json_file in json_files:
            domain = json_file.parent.name
            session_id = json_file.stem.replace('session_', '')
            
            if selected_domains and domain not in selected_domains:
                continue
            if selected_sessions and session_id not in selected_sessions:
                continue
                
            filtered_files.append(json_file)
        
        if not filtered_files:
            print("❌ No files match the selected filters")
            return False
            
        print(f"📊 Loading {len(filtered_files)} session files")
        
        # Reset data
        self.all_data = []
        self.domains = {}
        self.session_info = {}
        
        # Load data from filtered files
        for json_file in filtered_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                domain = json_file.parent.name
                session_id = json_file.stem.replace('session_', '')
                
                # Store domain data
                if domain not in self.domains:
                    self.domains[domain] = []
                    
                self.domains[domain].extend(data)
                self.all_data.extend(data)
                
                # Track session info
                if session_id not in self.session_info:
                    self.session_info[session_id] = {
                        'domains': set(),
                        'request_count': 0,
                        'files': []
                    }
                    
                self.session_info[session_id]['domains'].add(domain)
                self.session_info[session_id]['request_count'] += len(data)
                self.session_info[session_id]['files'].append(str(json_file))
                
            except Exception as e:
                print(f"⚠️ Error loading {json_file}: {e}")
                
        print(f"✅ Loaded {len(self.all_data)} total requests from {len(self.domains)} domains")
        return True
    
    def analyze_data(self) -> Dict[str, Any]:
        """
        Analyze the loaded data and generate insights.
        
        Returns:
            Dictionary containing comprehensive performance insights
        """
        if not self.all_data:
            return {}
            
        print("🔍 Analyzing performance data...")
        
        # Basic stats
        total_requests = len(self.all_data)
        response_times = [r.get('response_time_ms', 0) for r in self.all_data if r.get('response_time_ms', 0) > 0]
        response_sizes = [r.get('response_size', 0) for r in self.all_data if r.get('response_size', 0) > 0]
        
        # Resource type distribution
        resource_types = {}
        status_codes = {}
        domains_stats = {}
        
        for request in self.all_data:
            # Resource types
            rtype = request.get('resource_type', 'unknown')
            resource_types[rtype] = resource_types.get(rtype, 0) + 1
            
            # Status codes
            status = request.get('status', 0)
            status_codes[status] = status_codes.get(status, 0) + 1
            
            # Domain stats
            domain = request.get('domain', 'unknown')
            if domain not in domains_stats:
                domains_stats[domain] = {
                    'requests': 0,
                    'total_time': 0,
                    'total_size': 0,
                    'avg_time': 0,
                    'avg_size': 0,
                    'min_time': float('inf'),
                    'max_time': 0,
                    'response_times': []
                }
            
            domains_stats[domain]['requests'] += 1
            response_time = request.get('response_time_ms', 0)
            domains_stats[domain]['total_time'] += response_time
            domains_stats[domain]['total_size'] += request.get('response_size', 0)
            
            # Track min/max response times
            if response_time > 0:
                domains_stats[domain]['response_times'].append(response_time)
                domains_stats[domain]['min_time'] = min(domains_stats[domain]['min_time'], response_time)
                domains_stats[domain]['max_time'] = max(domains_stats[domain]['max_time'], response_time)
        
        # Calculate averages for domains
        for domain, stats in domains_stats.items():
            if stats['requests'] > 0:
                stats['avg_time'] = round(stats['total_time'] / stats['requests'], 2)
                stats['avg_size'] = round(stats['total_size'] / stats['requests'], 2)
                
                # Handle cases where no valid response times were recorded
                if stats['min_time'] == float('inf'):
                    stats['min_time'] = 0
                stats['min_time'] = round(stats['min_time'], 2)
                stats['max_time'] = round(stats['max_time'], 2)
        
        # Performance insights
        insights = {
            'total_requests': total_requests,
            'total_domains': len(self.domains),
            'total_sessions': len(self.session_info),
            'avg_response_time': round(statistics.mean(response_times), 2) if response_times else 0,
            'median_response_time': round(statistics.median(response_times), 2) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'avg_response_size': round(statistics.mean(response_sizes), 2) if response_sizes else 0,
            'total_data_transferred': sum(response_sizes),
            'resource_types': resource_types,
            'status_codes': status_codes,
            'domains_stats': domains_stats,
            'slowest_requests': sorted(self.all_data, key=lambda x: x.get('response_time_ms', 0), reverse=True)[:10],
            'largest_requests': sorted(self.all_data, key=lambda x: x.get('response_size', 0), reverse=True)[:10],
            'failed_requests': [r for r in self.all_data if r.get('status', 200) >= 400]
        }
        
        return insights
    
    def _clean_url_display(self, url: str, domain: str) -> Dict[str, str]:
        """Clean URL for display - remove redundant domain info and separate parameters"""
        if not url:
            return {"path": "", "params": "", "has_params": False}
            
        # Remove protocol
        clean_url = url.replace('https://', '').replace('http://', '')
        
        # If URL starts with domain, show path only
        if clean_url.startswith(domain):
            full_path = clean_url[len(domain):]
            if full_path.startswith('/'):
                path_part = full_path if full_path != '/' else '/ (root)'
            else:
                path_part = '/ (root)'
        else:
            # For cross-domain requests, show the different domain
            path_part = clean_url
        
        # Split path and parameters
        if '?' in path_part:
            path, params = path_part.split('?', 1)
            return {
                "path": path,
                "params": params,
                "has_params": True
            }
        else:
            return {
                "path": path_part,
                "params": "",
                "has_params": False
            }
    
    def generate_html_dashboard(self, insights: Dict[str, Any]) -> str:
        """Generate the complete HTML dashboard"""
        print("🎨 Generating HTML report...")
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slowpro Performance Report</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <style>
        :root {{
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            --border-radius: 20px;
        }}
        
        body {{ 
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        
        .metric-card {{
            background: var(--primary-gradient);
            color: white;
            border-radius: var(--border-radius);
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow);
            text-align: center;
            transition: transform 0.3s ease;
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px);
        }}
        
        .metric-card h3 {{
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        
        .metric-card p {{
            font-size: 1.1rem;
            margin: 0;
            opacity: 0.95;
        }}
        
        .metric-card i {{
            font-size: 1.5rem;
            margin-right: 0.5rem;
        }}
        
        .chart-container {{
            background: white;
            border-radius: var(--border-radius);
            padding: 2.5rem;
            margin-bottom: 2.5rem;
            box-shadow: var(--shadow);
            border: 1px solid rgba(0,0,0,0.05);
            height: 520px;
            display: flex;
            flex-direction: column;
        }}
        
        .chart-container h4 {{
            color: #2c3e50;
            font-weight: 600;
            margin-bottom: 1.5rem;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 1rem;
            flex-shrink: 0;
        }}
        
        .chart-wrapper {{
            flex: 1;
            position: relative;
            min-height: 0;
        }}
        
        .table-container {{
            background: white;
            border-radius: var(--border-radius);
            padding: 2.5rem;
            margin-bottom: 2.5rem;
            box-shadow: var(--shadow);
            border: 1px solid rgba(0,0,0,0.05);
        }}
        
        .table-container h4 {{
            color: #2c3e50;
            font-weight: 600;
            margin-bottom: 1.5rem;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 1rem;
        }}
        
        .table-responsive {{
            max-height: 500px;
            overflow-y: auto;
            border-radius: 10px;
            border: 1px solid #e9ecef;
        }}
        
        .status-success {{ color: #28a745; font-weight: 600; }}
        .status-error {{ color: #dc3545; font-weight: 600; }}
        .status-warning {{ color: #ffc107; font-weight: 600; }}
        
        .navbar {{ 
            background: var(--primary-gradient) !important;
            box-shadow: var(--shadow);
            padding: 1rem 0;
        }}
        
        .navbar-brand {{
            font-size: 1.5rem;
            font-weight: 600;
        }}
        
        .filter-section {{
            background: white;
            border-radius: var(--border-radius);
            padding: 2.5rem;
            margin-bottom: 2.5rem;
            box-shadow: var(--shadow);
            border: 1px solid rgba(0,0,0,0.05);
        }}
        
        .filter-section h4 {{
            color: #2c3e50;
            font-weight: 600;
            margin-bottom: 1.5rem;
        }}
        
        .btn-primary {{
            background: var(--primary-gradient);
            border: none;
            border-radius: 10px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }}
        
        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }}
        
        .form-select, .form-control {{
            border-radius: 10px;
            border: 2px solid #e9ecef;
            padding: 0.75rem 1rem;
            transition: all 0.3s ease;
        }}
        
        .form-select:focus, .form-control:focus {{
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }}
        
        .table thead th {{
            background: var(--primary-gradient);
            color: white;
            border: none;
            padding: 1rem;
            font-weight: 600;
            cursor: pointer;
            user-select: none;
            white-space: nowrap;
        }}
        
        .table thead th:hover {{
            background: var(--secondary-gradient);
        }}
        
        .table tbody td {{
            padding: 1rem;
            vertical-align: middle;
            border-bottom: 1px solid #f8f9fa;
            word-wrap: break-word;
        }}
        
        .table tbody tr:hover {{
            background: #f8f9fa;
        }}
        
        .badge {{
            font-size: 0.75rem;
            padding: 0.5rem 0.75rem;
            border-radius: 8px;
            margin-top: -15px;
        }}
        
        .container-fluid {{
            padding: 0 2rem;
        }}
        
        .url-path {{
            max-width: 400px;
            overflow: visible;
            white-space: normal;
            word-break: break-word;
            display: inline-block;
            vertical-align: middle;
            line-height: 1.4;
        }}
        
        .url-path-full {{
            max-width: 500px;
            overflow: visible;
            white-space: normal;
            word-break: break-word;
            display: inline;
            vertical-align: middle;
            line-height: 1.4;
        }}
        
        .url-path-summary {{
            max-width: 250px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            display: inline;
            vertical-align: middle;
        }}
        
        .params-toggle {{
            background: none;
            border: none;
            color: #667eea;
            font-size: 0.8rem;
            cursor: pointer;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            margin-left: 0.5rem;
            display: inline;
            vertical-align: middle;
        }}
        
        .params-toggle:hover {{
            background: #f8f9fa;
        }}
        
        .url-params {{
            background: #f8f9fa;
            padding: 0.5rem;
            border-radius: 6px;
            margin-top: 0.5rem;
            font-size: 0.85rem;
            color: #666;
            max-width: 100%;
            word-break: break-all;
        }}
        
        .url-cell {{
            position: relative;
            min-width: 300px;
        }}
        
        .url-cell-summary {{
            position: relative;
            min-width: 200px;
        }}
        
        @media (max-width: 768px) {{
            .container-fluid {{
                padding: 0 1rem;
            }}
            
            .metric-card {{
                padding: 1.5rem;
                margin-bottom: 1.5rem;
            }}
            
            .metric-card h3 {{
                font-size: 2rem;
            }}
            
            .chart-container, .table-container, .filter-section {{
                padding: 1.5rem;
                margin-bottom: 1.5rem;
            }}
            
            .chart-container {{
                height: auto;
            }}
        }}
        
        /* Footer Styles */
        .footer-section {{
            background: var(--primary-gradient);
            color: white;
            padding: 2rem 0;
            margin-top: 3rem;
            border-top: 1px solid rgba(0,0,0,0.1);
        }}
        
        .footer-text {{
            margin: 0;
            font-size: 1rem;
            color: rgba(255, 255, 255, 0.9);
        }}
        
        .footer-text i {{
            margin-right: 0.5rem;
            color: rgba(255, 255, 255, 0.8);
        }}
        
        .footer-link {{
            color: white;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
            border-bottom: 1px solid transparent;
        }}
        
        .footer-link:hover {{
            color: #f8f9fa;
            border-bottom-color: #f8f9fa;
            text-decoration: none;
        }}
        
        /* Static Chart Styles */
        .static-chart {{
            width: 100%;
            padding: 1rem 0;
            max-height: 400px;
            overflow-y: auto;
            overflow-x: hidden;
        }}
        
        .chart-bar {{
            margin-bottom: 1rem;
            padding: 0.5rem 0;
            flex-shrink: 0;
        }}
        
        .chart-bar-label {{
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #2c3e50;
            font-size: 0.9rem;
        }}
        
        .chart-bar-wrapper {{
            position: relative;
            background: #f8f9fa;
            border-radius: 8px;
            height: 35px;
            display: flex;
            align-items: center;
            overflow: hidden;
        }}
        
        .chart-bar-fill {{
            height: 100%;
            border-radius: 8px;
            transition: width 0.8s ease;
            min-width: 2px;
        }}
        
        .chart-bar-value {{
            position: absolute;
            right: 10px;
            font-size: 0.85rem;
            font-weight: 600;
            color: #2c3e50;
            z-index: 2;
        }}
        
        /* Custom scrollbar for static charts */
        .static-chart::-webkit-scrollbar {{
            width: 6px;
        }}
        
        .static-chart::-webkit-scrollbar-track {{
            background: #f1f1f1;
            border-radius: 3px;
        }}
        
        .static-chart::-webkit-scrollbar-thumb {{
            background: #c1c1c1;
            border-radius: 3px;
        }}
        
        .static-chart::-webkit-scrollbar-thumb:hover {{
            background: #a8a8a8;
        }}
        
        /* Hide static charts when JS charts are loaded */
        .js-loaded .static-chart {{
            display: none;
        }}
        
        /* Hide JS charts initially */
        .chart-canvas {{
            display: none;
        }}
        
        .js-loaded .chart-canvas {{
            display: block;
        }}
        
        /* Hide search container by default, show only when JS is loaded */
        .search-container {{
            display: none;
        }}
        
        .js-loaded .search-container {{
            display: flex;
        }}
        
        /* Summary tables optimization */
        .summary-table {{
            font-size: 0.875rem;
            table-layout: fixed;
            width: 100%;
        }}
        
        .summary-table th,
        .summary-table td {{
            padding: 0.6rem 0.4rem;
            white-space: nowrap;
        }}
        
        .summary-table .path-col {{
            width: 55%;
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        
        .summary-table .domain-col {{
            width: 30%;
            max-width: 120px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        
        .summary-table .time-col {{
            width: 15%;
            text-align: right;
            min-width: 80px;
        }}
        
        .summary-table .size-col {{
            width: 15%;
            text-align: right;
            min-width: 80px;
        }}
        
        .summary-table .type-col {{
            min-width: 70px;
        }}
        
        .summary-table .badge {{
            font-size: 0.7rem;
            padding: 0.25rem 0.4rem;
        }}
    </style>
</head>
<body>
    <nav class="navbar navbar-dark">
        <div class="container-fluid">
            <span class="navbar-brand mb-0 h1">
                <i class="fas fa-chart-line"></i> Slowpro Performance Report
            </span>
            <span class="navbar-text">
                <i class="fas fa-calendar"></i> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </span>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <!-- Key Metrics -->
        <div class="row g-4">
            <div class="col-lg-3 col-md-6">
                <div class="metric-card">
                    <h3>{insights['total_requests']:,}</h3>
                    <p><i class="fas fa-globe"></i> Total Requests</p>
                </div>
            </div>
            <div class="col-lg-3 col-md-6">
                <div class="metric-card">
                    <h3>{insights['total_domains']}</h3>
                    <p><i class="fas fa-server"></i> Domains</p>
                </div>
            </div>
            <div class="col-lg-3 col-md-6">
                <div class="metric-card">
                    <h3>{insights['avg_response_time']}ms</h3>
                    <p><i class="fas fa-clock"></i> Avg Response Time</p>
                </div>
            </div>
            <div class="col-lg-3 col-md-6">
                <div class="metric-card">
                    <h3>{self._format_bytes(insights['total_data_transferred'])}</h3>
                    <p><i class="fas fa-download"></i> Data Transferred</p>
                </div>
            </div>
        </div>

        <!-- Charts Row -->
        <div class="row g-4">
            <div class="col-lg-6">
                <div class="chart-container">
                    <h4><i class="fas fa-chart-pie"></i> Resource Types Distribution</h4>
                    <div class="chart-wrapper">
                        <!-- Static fallback chart (works without JS) -->
                        {self._generate_static_resource_chart(insights['resource_types'])}
                        <!-- JavaScript chart (enhanced version) -->
                        <canvas id="resourceTypesChart" class="chart-canvas"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-lg-6">
                <div class="chart-container">
                    <h4><i class="fas fa-chart-bar"></i> Average Response Times by Domain</h4>
                    <div class="chart-wrapper">
                        <!-- Static fallback chart (works without JS) -->
                        {self._generate_static_response_times_chart(insights['domains_stats'])}
                        <!-- JavaScript chart (enhanced version) -->
                        <canvas id="responseTimesChart" class="chart-canvas"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- Filters -->
        <div class="filter-section">
            <h4><i class="fas fa-filter"></i> Filters & Search</h4>
            <div class="row g-3">
                <div class="col-lg-3 col-md-6">
                    <label for="domainFilter" class="form-label fw-semibold">Domain</label>
                    <select id="domainFilter" class="form-select">
                        <option value="">All Domains</option>
                        {self._generate_domain_options()}
                    </select>
                </div>
                <div class="col-lg-3 col-md-6">
                    <label for="resourceTypeFilter" class="form-label fw-semibold">Resource Type</label>
                    <select id="resourceTypeFilter" class="form-select">
                        <option value="">All Resource Types</option>
                        {self._generate_resource_type_options(insights['resource_types'])}
                    </select>
                </div>
                <div class="col-lg-3 col-md-6">
                    <label for="minResponseTime" class="form-label fw-semibold">Min Response Time (ms)</label>
                    <input type="number" id="minResponseTime" class="form-control" placeholder="e.g. 100">
                </div>
                <div class="col-lg-3 col-md-6">
                    <label class="form-label">&nbsp;</label>
                    <button class="btn btn-primary w-100" onclick="applyFilters()">
                        <i class="fas fa-search"></i> Apply Filters
                    </button>
                </div>
            </div>
        </div>

        <!-- All Requests Table -->
        <div class="row">
            <div class="col-12">
                <div class="table-container">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <div class="d-flex align-items-center">
                            <h4 class="mb-0 me-3"><i class="fas fa-list"></i> All Requests</h4>
                            <span class="badge bg-primary fs-6" id="requestCount">{len(self.all_data)}</span>
                        </div>
                        
                        <!-- Search Bar (JS only) -->
                        <div class="d-flex align-items-center search-container">
                            <small class="text-muted me-3">
                                <span id="visibleCount">{len(self.all_data)}</span> of 
                                <span id="totalCount">{len(self.all_data)}</span> requests shown
                            </small>
                            <div class="input-group" style="width: 300px;">
                                <span class="input-group-text"><i class="fas fa-search"></i></span>
                                <input type="text" id="searchInput" class="form-control" 
                                       placeholder="Search requests..." 
                                       onkeyup="searchTable()">
                                <button class="btn btn-outline-secondary" type="button" onclick="clearSearch()">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="table-responsive">
                        <table class="table table-hover mb-0" id="allRequestsTable">
                            <thead>
                                <tr>
                                    <th onclick="sortTable(0)">Path <i class="fas fa-sort"></i></th>
                                    <th onclick="sortTable(1)">Domain <i class="fas fa-sort"></i></th>
                                    <th onclick="sortTable(2)">Method <i class="fas fa-sort"></i></th>
                                    <th onclick="sortTable(3)">Status <i class="fas fa-sort"></i></th>
                                    <th onclick="sortTable(4)">Response Time (ms) <i class="fas fa-sort"></i></th>
                                    <th onclick="sortTable(5)">Size <i class="fas fa-sort"></i></th>
                                    <th onclick="sortTable(6)">Type <i class="fas fa-sort"></i></th>
                                    <th onclick="sortTable(7)">Timestamp <i class="fas fa-sort"></i></th>
                                </tr>
                            </thead>
                            <tbody id="requestsTableBody">
                                {self._generate_all_requests_table()}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- Summary Tables Row -->
        <div class="row g-4">
            <div class="col-lg-6">
                <div class="table-container">
                    <h4><i class="fas fa-snowflake"></i> Slowest Requests</h4>
                    <div class="table-responsive">
                        <table class="table table-hover mb-0 summary-table">
                            <thead>
                                <tr>
                                    <th class="path-col">Path</th>
                                    <th class="domain-col">Domain</th>
                                    <th class="time-col">Time (ms)</th>
                                </tr>
                            </thead>
                            <tbody>
                                {self._generate_slowest_requests_table(insights['slowest_requests'])}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            <div class="col-lg-6">
                <div class="table-container">
                    <h4><i class="fas fa-weight-hanging"></i> Largest Requests</h4>
                    <div class="table-responsive">
                        <table class="table table-hover mb-0 summary-table">
                            <thead>
                                <tr>
                                    <th class="path-col">Path</th>
                                    <th class="domain-col">Domain</th>
                                    <th class="size-col">Size</th>
                                </tr>
                            </thead>
                            <tbody>
                                {self._generate_largest_requests_table(insights['largest_requests'])}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- Domain Statistics -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="table-container">
                    <h4><i class="fas fa-chart-line"></i> Domain Performance Summary</h4>
                    <div class="table-responsive">
                        <table class="table table-hover mb-0">
                            <thead>
                                <tr>
                                    <th>Domain</th>
                                    <th>Requests</th>
                                    <th>Avg Response Time (ms)</th>
                                    <th>Min Response Time (ms)</th>
                                    <th>Max Response Time (ms)</th>
                                    <th>Avg Size</th>
                                    <th>Total Data</th>
                                </tr>
                            </thead>
                            <tbody>
                                {self._generate_domain_stats_table(insights['domains_stats'])}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Mark document as having JavaScript loaded for progressive enhancement
        document.body.classList.add('js-loaded');
        
        // Store all data for filtering
        const allRequests = {json.dumps(self.all_data, default=str)};
        let filteredRequests = [...allRequests];

        // Helper function to clean URL display
        function cleanUrlDisplay(url, domain) {{
            if (!url) return {{ path: '', params: '', has_params: false }};
            let cleanUrl = url.replace(/^https?:\\/\\//, '');
            let pathPart = '';
            
            if (cleanUrl.startsWith(domain)) {{
                let fullPath = cleanUrl.substring(domain.length);
                pathPart = fullPath.startsWith('/') ? (fullPath === '/' ? '/ (root)' : fullPath) : '/ (root)';
            }} else {{
                pathPart = cleanUrl;
            }}
            
            if (pathPart.includes('?')) {{
                const [path, params] = pathPart.split('?', 2);
                return {{ path, params, has_params: true }};
            }} else {{
                return {{ path: pathPart, params: '', has_params: false }};
            }}
        }}

        // Toggle parameters display
        function toggleParams(button) {{
            const paramsDiv = button.nextElementSibling;
            if (paramsDiv && paramsDiv.classList.contains('url-params')) {{
                if (paramsDiv.style.display === 'none') {{
                    paramsDiv.style.display = 'block';
                    button.innerHTML = '<i class="fas fa-eye-slash"></i>';
                }} else {{
                    paramsDiv.style.display = 'none';
                    button.innerHTML = '<i class="fas fa-cog"></i>';
                }}
            }}
        }}

        // Resource Types Chart (JavaScript enhanced version)
        const resourceTypesCtx = document.getElementById('resourceTypesChart').getContext('2d');
        new Chart(resourceTypesCtx, {{
            type: 'doughnut',
            data: {{
                labels: {list(insights['resource_types'].keys())},
                datasets: [{{
                    data: {list(insights['resource_types'].values())},
                    backgroundColor: [
                        '#667eea', '#764ba2', '#f093fb', '#f5576c',
                        '#4facfe', '#00f2fe', '#fa709a', '#fee140'
                    ],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{
                            padding: 20,
                            usePointStyle: true
                        }}
                    }}
                }}
            }}
        }});

        // Response Times Chart (JavaScript enhanced version)
        const responseTimesCtx = document.getElementById('responseTimesChart').getContext('2d');
        const domainStats = {json.dumps(insights['domains_stats'])};
        const domainNames = Object.keys(domainStats);
        const avgTimes = domainNames.map(domain => domainStats[domain].avg_time);
        
        new Chart(responseTimesCtx, {{
            type: 'bar',
            data: {{
                labels: domainNames,
                datasets: [{{
                    label: 'Avg Response Time (ms)',
                    data: avgTimes,
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2,
                    borderRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{
                            color: 'rgba(0,0,0,0.1)'
                        }}
                    }},
                    x: {{
                        grid: {{
                            display: false
                        }}
                    }}
                }}
            }}
        }});

        // Table sorting (enhanced functionality)
        let sortDirection = [];
        
        function sortTable(columnIndex) {{
            const table = document.getElementById('allRequestsTable');
            const tbody = table.getElementsByTagName('tbody')[0];
            const rows = Array.from(tbody.getElementsByTagName('tr'));
            
            // Toggle sort direction
            sortDirection[columnIndex] = !sortDirection[columnIndex];
            const isAsc = sortDirection[columnIndex];
            
            rows.sort((a, b) => {{
                const aCell = a.getElementsByTagName('td')[columnIndex];
                const bCell = b.getElementsByTagName('td')[columnIndex];
                
                // Special handling for size column (index 5) - use raw byte values
                if (columnIndex === 5) {{
                    const aBytes = parseInt(aCell.getAttribute('data-bytes')) || 0;
                    const bBytes = parseInt(bCell.getAttribute('data-bytes')) || 0;
                    return isAsc ? aBytes - bBytes : bBytes - aBytes;
                }}
                
                // Handle response time column (index 4)
                if (columnIndex === 4) {{
                    const aNum = parseFloat(aCell.textContent.trim()) || 0;
                    const bNum = parseFloat(bCell.textContent.trim()) || 0;
                    return isAsc ? aNum - bNum : bNum - aNum;
                }}
                
                // Handle other columns as text
                const aText = aCell.textContent.trim();
                const bText = bCell.textContent.trim();
                return isAsc ? aText.localeCompare(bText) : bText.localeCompare(aText);
            }});
            
            // Clear tbody and append sorted rows
            tbody.innerHTML = '';
            rows.forEach(row => tbody.appendChild(row));
        }}

        // Filtering (enhanced functionality)
        function applyFilters() {{
            const domainFilter = document.getElementById('domainFilter').value;
            const resourceTypeFilter = document.getElementById('resourceTypeFilter').value;
            const minResponseTime = parseFloat(document.getElementById('minResponseTime').value) || 0;
            
            filteredRequests = allRequests.filter(request => {{
                if (domainFilter && request.domain !== domainFilter) return false;
                if (resourceTypeFilter && request.resource_type !== resourceTypeFilter) return false;
                if (minResponseTime && (request.response_time_ms || 0) < minResponseTime) return false;
                return true;
            }});
            
            updateTable();
            searchTable(); // Apply search after filtering
        }}

        // Search functionality
        function searchTable() {{
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const table = document.getElementById('allRequestsTable');
            const tbody = table.getElementsByTagName('tbody')[0];
            const rows = tbody.getElementsByTagName('tr');
            let visibleCount = 0;
            
            for (let i = 0; i < rows.length; i++) {{
                const row = rows[i];
                const cells = row.getElementsByTagName('td');
                let shouldShow = false;
                
                if (searchTerm === '') {{
                    shouldShow = true;
                }} else {{
                    // Search through URL, domain, method, status, and resource type
                    const searchableText = [
                        cells[0]?.textContent || '', // URL/Path
                        cells[1]?.textContent || '', // Domain
                        cells[2]?.textContent || '', // Method
                        cells[3]?.textContent || '', // Status
                        cells[6]?.textContent || ''  // Resource Type
                    ].join(' ').toLowerCase();
                    
                    shouldShow = searchableText.includes(searchTerm);
                }}
                
                if (shouldShow) {{
                    row.style.display = '';
                    visibleCount++;
                }} else {{
                    row.style.display = 'none';
                }}
            }}
            
            // Update visible count
            document.getElementById('visibleCount').textContent = visibleCount;
        }}

        // Clear search
        function clearSearch() {{
            document.getElementById('searchInput').value = '';
            searchTable();
        }}

        function updateTable() {{
            const tbody = document.getElementById('requestsTableBody');
            const requestCount = document.getElementById('requestCount');
            const totalCount = document.getElementById('totalCount');
            
            tbody.innerHTML = filteredRequests.map(request => {{
                const statusClass = request.status >= 400 ? 'status-error' : 
                                  request.status >= 300 ? 'status-warning' : 'status-success';
                                  
                const urlInfo = cleanUrlDisplay(request.url, request.domain);
                const pathDisplay = urlInfo.path;
                const responseSize = request.response_size || 0;
                                  
                return `
                    <tr>
                        <td class="url-cell">
                            <span class="url-path-full" title="${{request.url}}">${{pathDisplay}}</span>
                            ${{urlInfo.has_params ? `<button class="params-toggle" onclick="toggleParams(this)"><i class="fas fa-cog"></i></button>` : ''}}
                            ${{urlInfo.has_params ? `<div class="url-params" style="display: none;">${{urlInfo.params}}</div>` : ''}}
                        </td>
                        <td>${{request.domain}}</td>
                        <td>${{request.method}}</td>
                        <td><span class="${{statusClass}}">${{request.status}}</span></td>
                        <td>${{(request.response_time_ms || 0).toFixed(2)}}</td>
                        <td data-bytes="${{responseSize}}">${{formatBytes(responseSize)}}</td>
                        <td><span class="badge bg-secondary">${{request.resource_type}}</span></td>
                        <td>${{new Date(request.timestamp).toLocaleString()}}</td>
                    </tr>
                `;
            }}).join('');
            
            requestCount.textContent = filteredRequests.length;
            totalCount.textContent = allRequests.length;
            
            // Reset visible count to match filtered results
            document.getElementById('visibleCount').textContent = filteredRequests.length;
        }}

        function formatBytes(bytes) {{
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }}
    </script>
    
    <!-- Footer -->
    <footer class="footer-section">
        <div class="container-fluid">
            <div class="text-center">
                <p class="footer-text">
                    <i class="fas fa-code"></i>
                    Generated using <a href="https://github.com/ssl/Slowpro" target="_blank" class="footer-link">Slowpro</a>
                </p>
            </div>
        </div>
    </footer>
</body>
</html>"""
        
        return html
    
    def _format_bytes(self, bytes_size: int) -> str:
        """Format bytes to human readable format"""
        if bytes_size == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(bytes_size, 1024)))
        p = math.pow(1024, i)
        s = round(bytes_size / p, 2)
        return f"{s} {size_names[i]}"
    
    def _generate_domain_options(self) -> str:
        """Generate domain filter options"""
        options = []
        for domain in sorted(self.domains.keys()):
            options.append(f'<option value="{domain}">{domain}</option>')
        return '\n'.join(options)
    
    def _generate_resource_type_options(self, resource_types: Dict[str, int]) -> str:
        """Generate resource type filter options"""
        options = []
        for rtype in sorted(resource_types.keys()):
            options.append(f'<option value="{rtype}">{rtype}</option>')
        return '\n'.join(options)
    
    def _generate_slowest_requests_table(self, requests: List[Dict]) -> str:
        """Generate slowest requests table rows"""
        rows = []
        for request in requests[:10]:
            url_info = self._clean_url_display(request.get('url', ''), request.get('domain', ''))
            # Let CSS handle truncation with ellipsis
            path_display = url_info['path']
            domain_display = request.get('domain', '')
            
            rows.append(f"""
                <tr>
                    <td class="path-col" title="{request.get('url', '')}">{path_display}</td>
                    <td class="domain-col" title="{request.get('domain', '')}">{domain_display}</td>
                    <td class="time-col">{request.get('response_time_ms', 0):.1f}</td>
                </tr>
            """)
        return '\n'.join(rows)
    
    def _generate_largest_requests_table(self, requests: List[Dict]) -> str:
        """Generate largest requests table rows"""
        rows = []
        for request in requests[:10]:
            url_info = self._clean_url_display(request.get('url', ''), request.get('domain', ''))
            # Let CSS handle truncation with ellipsis
            path_display = url_info['path']
            domain_display = request.get('domain', '')
            
            rows.append(f"""
                <tr>
                    <td class="path-col" title="{request.get('url', '')}">{path_display}</td>
                    <td class="domain-col" title="{request.get('domain', '')}">{domain_display}</td>
                    <td class="size-col">{self._format_bytes(request.get('response_size', 0))}</td>
                </tr>
            """)
        return '\n'.join(rows)
    
    def _generate_domain_stats_table(self, domain_stats: Dict[str, Dict]) -> str:
        """Generate domain statistics table rows"""
        rows = []
        sorted_domains = sorted(domain_stats.items(), key=lambda x: x[1]['requests'], reverse=True)
        
        for domain, stats in sorted_domains:
            rows.append(f"""
                <tr>
                    <td>{domain}</td>
                    <td>{stats['requests']:,}</td>
                    <td>{stats['avg_time']:.2f}</td>
                    <td>{stats['min_time']:.2f}</td>
                    <td>{stats['max_time']:.2f}</td>
                    <td>{self._format_bytes(stats['avg_size'])}</td>
                    <td>{self._format_bytes(stats['total_size'])}</td>
                </tr>
            """)
        return '\n'.join(rows)
    
    def _generate_static_resource_chart(self, resource_types: Dict[str, int]) -> str:
        """Generate static CSS-based resource types chart"""
        if not resource_types:
            return "<p>No data available</p>"
            
        total = sum(resource_types.values())
        colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe', '#fa709a', '#fee140']
        
        chart_html = '<div class="static-chart">'
        
        # Generate bars
        for i, (resource_type, count) in enumerate(sorted(resource_types.items(), key=lambda x: x[1], reverse=True)):
            percentage = (count / total) * 100
            color = colors[i % len(colors)]
            
            chart_html += f'''
                <div class="chart-bar">
                    <div class="chart-bar-label">{resource_type}</div>
                    <div class="chart-bar-wrapper">
                        <div class="chart-bar-fill" style="width: {percentage:.1f}%; background-color: {color};"></div>
                        <span class="chart-bar-value">{count} ({percentage:.1f}%)</span>
                    </div>
                </div>
            '''
        
        chart_html += '</div>'
        return chart_html
    
    def _generate_static_response_times_chart(self, domain_stats: Dict[str, Dict]) -> str:
        """Generate static CSS-based response times chart"""
        if not domain_stats:
            return "<p>No data available</p>"
            
        # Sort domains by average response time
        sorted_domains = sorted(domain_stats.items(), key=lambda x: x[1]['avg_time'], reverse=True)
        max_time = max(stats['avg_time'] for stats in domain_stats.values()) if domain_stats else 1
        
        chart_html = '<div class="static-chart">'
        
        for domain, stats in sorted_domains:
            percentage = (stats['avg_time'] / max_time) * 100 if max_time > 0 else 0
            
            chart_html += f'''
                <div class="chart-bar">
                    <div class="chart-bar-label">{domain}</div>
                    <div class="chart-bar-wrapper">
                        <div class="chart-bar-fill" style="width: {percentage:.1f}%; background-color: rgba(102, 126, 234, 0.8);"></div>
                        <span class="chart-bar-value">{stats['avg_time']:.2f}ms</span>
                    </div>
                </div>
            '''
        
        chart_html += '</div>'
        return chart_html
    
    def _generate_all_requests_table(self) -> str:
        """Generate all requests table rows server-side"""
        if not self.all_data:
            return "<tr><td colspan='8' class='text-center'>No data available</td></tr>"
            
        rows = []
        for request in self.all_data:
            status_class = 'status-error' if request.get('status', 200) >= 400 else \
                          'status-warning' if request.get('status', 200) >= 300 else 'status-success'
            
            url_info = self._clean_url_display(request.get('url', ''), request.get('domain', ''))
            path_display = url_info['path']
            response_size = request.get('response_size', 0)
            
            # Format timestamp
            timestamp = request.get('timestamp', '')
            if timestamp:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    formatted_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    formatted_timestamp = timestamp
            else:
                formatted_timestamp = 'N/A'
            
            row = f'''
                <tr>
                    <td class="url-cell">
                        <span class="url-path-full" title="{request.get('url', '')}">{path_display}</span>
                        {f'<button class="params-toggle" onclick="toggleParams(this)"><i class="fas fa-cog"></i></button>' if url_info['has_params'] else ''}
                        {f'<div class="url-params" style="display: none;">{url_info["params"]}</div>' if url_info['has_params'] else ''}
                    </td>
                    <td>{request.get('domain', '')}</td>
                    <td>{request.get('method', '')}</td>
                    <td><span class="{status_class}">{request.get('status', '')}</span></td>
                    <td>{request.get('response_time_ms', 0):.2f}</td>
                    <td data-bytes="{response_size}">{self._format_bytes(response_size)}</td>
                    <td><span class="badge bg-secondary">{request.get('resource_type', '')}</span></td>
                    <td>{formatted_timestamp}</td>
                </tr>
            '''
            rows.append(row)
        
        return '\n'.join(rows)
    
    def show_selection_menu(self) -> tuple[Optional[List[str]], Optional[List[str]]]:
        """
        Show interactive selection menu for domains and sessions.
        
        Returns:
            Tuple of (selected_domains, selected_sessions)
        """
        if not self.discover_data():
            return None, None
            
        print("\n" + "="*60)
        print("🎯 SLOWPRO DATA SELECTION MENU")
        print("="*60)
        
        # Domain selection
        print("\n📊 AVAILABLE DOMAINS:")
        print("0. All domains")
        for i, domain in enumerate(self.available_domains, 1):
            print(f"{i}. {domain}")
        
        domain_input = input(f"\nSelect domains (comma-separated numbers, or 0 for all): ").strip()
        selected_domains = None
        
        if domain_input and domain_input != "0":
            try:
                domain_indices = [int(x.strip()) - 1 for x in domain_input.split(',')]
                selected_domains = [self.available_domains[i] for i in domain_indices if 0 <= i < len(self.available_domains)]
                print(f"✅ Selected domains: {', '.join(selected_domains)}")
            except (ValueError, IndexError):
                print("⚠️ Invalid selection, using all domains")
        else:
            print("✅ Using all domains")
        
        # Session selection
        print(f"\n📅 AVAILABLE SESSIONS:")
        print("0. All sessions")
        for i, session in enumerate(self.available_sessions, 1):
            print(f"{i}. {session}")
        
        session_input = input(f"\nSelect sessions (comma-separated numbers, or 0 for all): ").strip()
        selected_sessions = None
        
        if session_input and session_input != "0":
            try:
                session_indices = [int(x.strip()) - 1 for x in session_input.split(',')]
                selected_sessions = [self.available_sessions[i] for i in session_indices if 0 <= i < len(self.available_sessions)]
                print(f"✅ Selected sessions: {', '.join(selected_sessions)}")
            except (ValueError, IndexError):
                print("⚠️ Invalid selection, using all sessions")
        else:
            print("✅ Using all sessions")
        
        return selected_domains, selected_sessions
    
    def generate_dashboard(self, output_file: Optional[str] = None, interactive: bool = True) -> bool:
        """
        Generate the complete dashboard.
        
        Args:
            output_file: Output HTML filename (None for timestamped filename)
            interactive: Whether to show interactive selection menu
            
        Returns:
            True if dashboard generated successfully, False otherwise
        """
        print("🚀 Starting Slowpro report generation...")
        
        # Generate timestamped filename if none provided
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"slowpro_report_{timestamp}.html"
        
        # Check if performance_data folder exists and save report there if it does
        perf_data_path = Path("performance_data")
        if perf_data_path.exists() and perf_data_path.is_dir():
            output_path = perf_data_path / output_file
            print(f"📁 Found performance_data/ folder - saving report there")
        else:
            output_path = Path(output_file)
            print(f"📁 Saving report in current directory")
        
        selected_domains, selected_sessions = None, None
        
        if interactive:
            selected_domains, selected_sessions = self.show_selection_menu()
        
        if not self.load_data(selected_domains, selected_sessions):
            return False
            
        insights = self.analyze_data()
        html_content = self.generate_html_dashboard(insights)
        
        # Write HTML file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        except Exception as e:
            print(f"❌ Error writing dashboard file: {e}")
            raise ReportError(f"Failed to write dashboard: {e}")
            
        print(f"\n✅ Slowpro Performance Report generated successfully!")
        print(f"📁 File: {output_path.absolute()}")
        print(f"🌐 Open in browser: file://{output_path.absolute()}")
        
        return True


def main() -> None:
    """Main function for Slowpro report generator."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate Slowpro performance report from JSON data",
        prog="slowpro-report"
    )
    parser.add_argument(
        '--data-dir', 
        default='performance_data', 
        help='Directory containing JSON data files (default: performance_data)'
    )
    parser.add_argument(
        '--output', 
        help='Output HTML file name (default: timestamped filename)'
    )
    parser.add_argument(
        '--all', 
        action='store_true', 
        help='Process all data without interactive selection'
    )
    parser.add_argument(
        '--domains', 
        nargs='+', 
        help='Specific domains to include'
    )
    parser.add_argument(
        '--sessions', 
        nargs='+', 
        help='Specific sessions to include'
    )
    
    args = parser.parse_args()
    
    try:
        generator = DashboardGenerator(args.data_dir)
        
        if args.all:
            # Process all data without interaction
            success = generator.generate_dashboard(args.output, interactive=False)
            if not success:
                exit(1)
                
        elif args.domains or args.sessions:
            # Use command line specified domains/sessions
            if not generator.load_data(args.domains, args.sessions):
                print("❌ Failed to load data with specified filters")
                exit(1)
                
            insights = generator.analyze_data()
            html_content = generator.generate_html_dashboard(insights)
            
            # Generate timestamped filename if none provided
            output_file = args.output
            if output_file is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"slowpro_report_{timestamp}.html"
            
            # Check if performance_data folder exists and save report there if it does
            perf_data_path = Path("performance_data")
            if perf_data_path.exists() and perf_data_path.is_dir():
                output_path = perf_data_path / output_file
                print(f"📁 Found performance_data/ folder - saving report there")
            else:
                output_path = Path(output_file)
                print(f"📁 Saving report in current directory")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ Slowpro Performance Report generated: {output_path.absolute()}")
            
        else:
            # Interactive mode
            success = generator.generate_dashboard(args.output, interactive=True)
            if not success:
                exit(1)
                
    except KeyboardInterrupt:
        print("\n👋 Report generation cancelled by user")
        exit(1)
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        exit(1)


if __name__ == "__main__":
    main() 