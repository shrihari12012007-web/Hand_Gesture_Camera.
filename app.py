import os
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    """Serves the interactive Hand Gesture Camera web interface."""
    return render_template("index.html")

@app.route("/health")
def health():
    """Health check endpoint for cloud and local deployments."""
    return jsonify({"status": "ok", "service": "hand-gesture-camera"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Hand Gesture Camera server on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
