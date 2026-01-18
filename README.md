# 🔷 KRIX PROXY

A powerful proxy generation and verification tool with a colorful command-line interface.

## 📋 Description

KRIX PROXY is a multi-threaded proxy checker that allows you to:
- Generate random proxies (HTTP, HTTPS, SOCKS4, SOCKS5)
- Verify proxy validity
- Test proxies from a file
- Configure verification parameters

## ✨ Features

- **Proxy Generation**: Create realistic random IP addresses and ports
- **Multi-threaded Verification**: Fast testing of multiple proxies simultaneously
- **Multi-protocol Support**: HTTP, HTTPS, SOCKS4, SOCKS5
- **Flexible Configuration**: Customize timeouts, threads, and test URLs
- **Colorful Interface**: Elegant display with ASCII banner
- **Real-time Statistics**: Counters for valid/invalid/timeout proxies
- **Retry System**: Automatic retry attempts on temporary failures
- **Rate Limiting**: Control delay between requests

## 📦 Installation

### Prerequisites
- Python 3.7+
- pip

### Dependencies
```bash
pip install pystyle colorama requests urllib3 pyyaml
```

## 🗂️ Project Structure

```
proxy/
├── krix_proxy.py      # Main script
├── config.yaml        # Configuration file
├── input/             # Folder for proxies to verify
│   └── proxies.txt    # Proxy list (one per line)
└── output/            # Results folder
    ├── valid_proxies.txt    # Valid proxies
    ├── invalid_proxies.txt  # Invalid proxies
    └── timeout_proxies.txt  # Timeout proxies
```

## ⚙️ Configuration

The `config.yaml` file contains the following parameters:

```yaml
max_retries: 2                    # Number of retry attempts on failure
print_invalid: true               # Display invalid proxies
request_delay: 0                  # Delay between requests (seconds)
request_timeout: 1                # Request timeout (seconds)
test_url: http://httpbin.org/ip  # URL used to test proxies
threads: 10                       # Number of simultaneous threads
update_title: true                # Update console title
```

## 🚀 Usage

### Launch
```bash
python krix_proxy.py
```

### Main Menu

**Option 1: Generate and verify proxies**
- Choose the number of proxies to generate
- Select the type (HTTP, HTTPS, SOCKS4, SOCKS5, or all)
- Set the delay between generations
- Proxies are automatically verified

**Option 2: Verify proxies from a file**
- Place your proxies in `proxy/input/proxies.txt`
- Accepted format: `TYPE://IP:PORT` or `IP:PORT` (HTTP by default)
- Example: `HTTP://192.168.1.1:8080` or `192.168.1.1:8080`

**Option 3: Modify configuration**
- Adjust parameters without manually editing the YAML file
- Changes require program restart

**Option 4: Exit**

### Supported Proxy Formats

```
# Without authentication
HTTP://192.168.1.1:8080
HTTPS://192.168.1.1:443
SOCKS4://192.168.1.1:1080
SOCKS5://192.168.1.1:1080
192.168.1.1:8080  # HTTP by default

# With authentication
user:pass@192.168.1.1:8080
```

## 📊 Results

Results are automatically saved in `proxy/output/`:

- **valid_proxies.txt**: Functional proxies (HTTP 200 code)
- **invalid_proxies.txt**: Non-functional proxies or connection errors
- **timeout_proxies.txt**: Proxies that exceeded timeout

## 🎨 Usage Example

```
1. Launch the script
2. Select option 1 (Generate and verify)
3. Enter 100 proxies
4. Choose type 5 (all types mixed)
5. Set delay 0 (fast generation)
6. Use 10 threads (default)
7. Wait for results
```

Statistics display in real-time:
- ✅ Valid proxies in green
- ❌ Invalid proxies in red
- ⚠️ Timeouts in yellow

## 🛠️ Technical Details

### ProxyChecker Class
Handles proxy verification with:
- Automatic parsing of different formats
- Error handling (ProxyError, ConnectionError, Timeout)
- Configurable retry system
- SOCKS proxy support with `socks5://` and `socks4://`

### Generation Features
- **generate_random_ip()**: Generates realistic IPs (avoids private ranges)
- **generate_random_port()**: Uses common ports (80, 8080, 3128, etc.)
- **generate_proxy()**: Combines IP and port with authentication option

### Rate Limiting
- Semaphore to control concurrency
- Lock to synchronize requests
- Additional random delay (0.05-0.15s) to avoid detection

## 📝 Notes

- Generated proxies are **random** and may not be functional
- Verification uses `httpbin.org` by default (configurable)
- SSL warnings are disabled for HTTPS tests
- Compatible with Windows (console title) and Linux/Mac

## 🐛 Troubleshooting

**Issue: No valid proxies**
- Check your internet connection
- Try with another `test_url`
- Increase `request_timeout`

**Issue: Slow program**
- Reduce the number of threads
- Decrease `request_timeout`
- Reduce `max_retries`

**Issue: Too many errors**
- Increase `request_delay` to avoid rate limiting
- Check proxy format in input file

## ⚠️ Disclaimer

This tool is provided for educational purposes. Proxy usage must comply with local laws and service terms of use. The author is not responsible for misuse of this tool.

## 📄 License

Personal Project - KRIX

## 👤 Author

**KRIX** - Proxy Verification Tool

---

⭐ Feel free to star if this project is useful to you!
