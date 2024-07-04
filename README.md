<p align="center">
  <img src="assets/logo.png" alt="Fungi Logo" width="200">
</p>

<h1 align="center">Fungi</h1>

<p align="center">
  Fungi is a simple P2P network library for connecting nodes in a decentralized manner. Nodes discover their public IP and port using STUN servers, facilitating direct connections.
</p>

<p align="center">
  <a href="#installation-%EF%B8%8F">Installation</a> •
  <a href="#usage-">Usage</a>
</p>

<br>


## Installation 🛠️

To install Fungi, run:

```bash
pip install https://github.com/VictorGoubet/fungi/archive/refs/tags/v1.tar.gz
```

Replace *v1* with the release you want to use.

## Usage 🚀

### Host your signaling server

A P2P connection needs a signaling server to keep track of who is on the network and to share this information to the nodes. A docker image is available for this server. You will need to host it either locally or on a server. 


```bash
docker run -p 8000:8000 victorgoubet/fungi:v1
```


### Launch

Launch the client inorder to connect to other nodes

```bash
launch-fungi
```

Note: be sure to have the good signaling server host and port in the tools/constants file, the default is

```python
SERVER_URL = "http://localhost:8000"
SERVER_PORT = 8000
```


## Customization

If you want to build your own docker image of the signaling server, some scripts are available in the *server/scripts* folder.

---
