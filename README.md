# 🚀 Slowpro

> **Web Performance Testing Tool**
```
 ▗▄▄▖█  ▄▄▄  ▄   ▄ ▄▄▄▄   ▄▄▄ ▄▄▄  
▐▌   █ █   █ █ ▄ █ █   █ █   █   █ 
 ▝▀▚▖█ ▀▄▄▄▀ █▄█▄█ █▄▄▄▀ █   ▀▄▄▄▀    
▗▄▄▞▘█             █            
```

Identify performance bottlenecks in web applications by capturing and analyzing all network requests with real-time browser monitoring.

[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ Features

- 🔍 **Real-time Network Monitoring** - Captures all HTTP requests, responses, and timings
- 📊 **Interactive Performance Dashboard** - Beautiful HTML reports with filtering and analysis
- 🌐 **Multi-Domain Support** - Organizes data by domain and session for easy analysis
- ⚡ **Live Feedback** - See performance metrics as you browse
- 📈 **Analytics** - Response times, sizes, resource types, and bottleneck identification

## 🛠️ Installation

### Quick Install
```bash
git clone https://github.com/ssl/Slowpro
cd Slowpro
pip install -r requirements.txt
```

## 🚀 Quick Start

### 1. Start Performance Testing
```bash
python slowpro.py
```

This opens a browser and starts automatic monitoring. Simply browse any websites normally - Slowpro captures all network activity automatically. Close the browser window or press `Ctrl+C` to end the session.

### 2. Generate Performance Report
```bash
python report_generator.py
```

This creates an interactive HTML dashboard from your captured data.

## 📊 Understanding Your Results

### Performance Dashboard
The generated HTML report includes:

- **📈 Response Time Analysis** - Identify slow requests
- **📦 Data Transfer Metrics** - Find large resources
- **🔗 Domain Statistics** - Compare performance across domains
- **🎯 Resource Type Breakdown** - Analyze JS, CSS, images, APIs
- **⚠️ Failed Requests** - Spot errors and timeouts

### Key Metrics to Watch
- **Average Response Time** - Lower is better
- **Largest Requests** - Opportunities for optimization  
- **Failed Requests** - Fix these first
- **Slowest Domains** - External dependencies to optimize

> View the example report that browsed on GitHub: [example_report.html](https://raw.githubusercontent.com/ssl/Slowpro/main/example_report.html)

## 💡 Tips

### For Best Results
- Browse normally - Slowpro automatically captures everything
- Visit different pages to capture varied performance data
- Test different user flows to find bottlenecks
- Use the report filters to focus on specific issues

### Common Use Cases
- **API Performance Testing** - Monitor XHR/Fetch requests automatically
- **Page Load Analysis** - Identify slow resources across all visited pages
- **Third-party Impact** - Measure external service performance
- **User Journey Testing** - Analyze performance across complete workflows

## 📁 Data Organization

```
performance_data/
├── domain1.com/
│   └── session_20240101_120000.json
│   └── session_20240101_120000.csv
├── domain2.com/
│   └── session_20240101_120000.json
│   └── session_20240101_120000.csv
└── slowpro_report_20240101_120500.html
```

Each session creates organized data files that can be analyzed individually or combined in reports.

## 🔧 Advanced Usage

### Command Line Options

**Report Generator:**
```bash
python report_generator.py --help
python report_generator.py --all                    # Process all data
python report_generator.py --domains domain1.com    # Specific domains
python report_generator.py --output my_report.html  # Custom filename
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
