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

2. **Configure API Key**
   Edit the `.env` file and add your `GEMINI_API_KEY`:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
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

## 🔒 Security & Architecture

This demo uses the **Ephemeral Token** approach:

1.  **Backend**: Uses `GEMINI_API_KEY` to request a short-lived (ephemeral) token via the `google-genai` SDK.
2.  **Frontend**: Fetches this token from the backend `/api/token` endpoint.
3.  **Direct Connection**: The browser establishes a WebSocket connection directly to Gemini API using the token, ensuring maximum performance and privacy.

monaco editor - https://github.com/monaco-editor/monaco-editor   ----    https://microsoft.github.io/monaco-editor/     used here for code editor
