<p align="center">
  <img src="assets/logo.png" alt="Fungi Logo" width="200">
</p>

<h1 align="center">🍄 Fungi</h1>

<p align="center">
  <strong>A simple P2P network library for decentralized node connections</strong>
</p>

<p align="center">
  <em>Discover public IP and port using STUN servers for direct connections</em>
</p>

<p align="center">
  <a href="#-signaling-server-setup">Signaling Server Setup</a> •
  <a href="#-client-installation">Client Installation</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-customization">Customization</a>
</p>

<br>

## 🖥️ Signaling Server Setup

Before using Fungi, set up a signaling server to track and share node information:

```bash
docker run -p 8000:8000 victorgoubet/fungi_server:v1
```

> 💡 Replace `v1` with your desired release version.

## 🛠️ Server Management

The server can now be built, deployed, and run using the Makefile at the project root. Example commands:

```bash
# Build the server Docker image
make build-server

# Deploy (push) the server image to Docker Hub
make deploy-server IMAGE_VERSION=your_version DOCKER_USERNAME=your_docker_username

# Run the server from Docker Hub
make run-server IMAGE_VERSION=your_version DOCKER_USERNAME=your_docker_username
```

- Edit the `.env_example` at the project root and copy it to `.env` to configure environment variables.

## 🛠️ Client Installation

Choose between pip or Docker for client installation:

### 🐍 Option 1: pip Installation

1. Install Fungi:

```bash
pip install https://github.com/VictorGoubet/fungi/archive/refs/tags/v1.tar.gz
```

2. Configure the signaling server URL in `utils/constants.py`:

```python
SERVER_URL = "http://localhost:8000"
```

3. Launch the client:

```bash
launch-fungi
```

### 🐳 Option 2: Docker Installation

Run the Fungi client container:

```bash
docker run -p 8080:8080 victorgoubet/fungi_client:v1
```

> 💡 Replace `v1` with your desired release version.

## 🚀 Usage

After launching the client, navigate to `http://localhost:8080` in your web browser.
## 🔧 Customization

To build your own signaling server Docker image, utilize the scripts in the `server/scripts` folder:

- 🐧 Linux: `fungi/server/scripts/linux/`
- 🍎 macOS: `fungi/server/scripts/macos/`
- 🪟 Windows: `fungi/server/scripts/windows/`

