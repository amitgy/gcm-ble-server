# Contributing to GCM BLE Server

Thank you for your interest in contributing to this project! This document provides guidelines for contributing.

## Areas for Contribution

### 🔬 Research & Development
- **Phase 2**: BLE packet interception tools
- **Phase 3**: Replay attack implementation
- **Phase 4**: Security hardening (encryption, authentication)
- **Phase 5**: Real-world CGM device testing

### 🐛 Bug Reports
If you find issues:
1. Check existing issues first
2. Provide detailed reproduction steps
3. Include your OS and BlueZ version
4. Share relevant error messages

### ✨ Feature Requests
We welcome suggestions for:
- Additional GATT characteristics
- Enhanced security features
- Better mobile app integration
- Expanded documentation

### 📚 Documentation
Help improve:
- Installation guides
- Protocol explanations
- Code comments
- Example usage

## How to Contribute

1. **Fork** the repository
2. **Create a branch** for your feature
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** with clear commit messages
4. **Test thoroughly** before submitting
5. **Submit a Pull Request** with description

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/gcm-ble-server.git

# Install dependencies
sudo apt-get install -y python3 python3-pip bluez bluez-tools libglib2.0-dev libdbus-1-dev
pip3 install dbus-python PyGObject

# Create a branch
git checkout -b develop
```

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable names
- Add comments for complex logic
- Keep functions focused and small

## Testing

Before submitting a PR:
```bash
# Run the server
sudo python3 gcm_ble_server.py

# Test with nRF Connect or CGM app
# Verify glucose readings are transmitted correctly
```

## Reporting Security Issues

⚠️ **For security vulnerabilities:**
- Do NOT open public issues
- Email security details to the maintainer
- Allow time for a fix before disclosure
- Follow responsible disclosure practices

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Support the learning of others
- Report inappropriate behavior

## Questions?

- Check existing issues/discussions
- Review GATT_PROTOCOL.md for technical details
- Refer to README.md for setup help

Thank you for contributing! 🙏
