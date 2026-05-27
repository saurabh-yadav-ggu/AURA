# Gemini Live API - Premium Voice Assistant

A high-performance, premium WebSocket client for Google's Gemini Live API. This implementation features a modern, glassmorphic UI and supports real-time audio/video streaming using **Ephemeral Tokens**.

## ✨ Features

- **Premium UI**: Modern, responsive design with glassmorphism and smooth animations.
- **Direct Connection**: Low-latency WebSocket connection directly to Gemini API.
- **Multimodal Support**: Real-time audio, video, and screen sharing.
- **Secure Tokens**: Uses backend-generated ephemeral tokens for enhanced security.
- **Custom Tools**: Built-in examples for browser interaction and CSS injection.

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   uv venv
   # On Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```

2. **C
   ```

3. **Start Server**
   ```bash
   uv run server.py
   ```

4. **Experience Gemini**
   Open [http://localhost:8000](http://localhost:8000) and click **Connect Session**.

## 🛠️ Project Structure

```
/
├── server.py        # Token provisioning + HTTP server
├── .env             # API key configuration
├── requirements.txt # Python dependencies
└── frontend/
    ├── index.html    # UI
    ├── styles.css    # Premium Styling
    ├── geminilive.js # Gemini API client
    ├── mediaUtils.js # Audio/video streaming logic
    ├── tools.js      # Custom tool definitions
    └── script.js     # Application workflow
```

