from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hand Gesture Camera</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 60px 20px;
            }
        </style>
    </head>
    <body>
        <h1>✋ Hand Gesture Camera</h1>
        <p>Hand Gesture Computer Controller</p>
        <p>Web deployment is running successfully.</p>
    </body>
    </html>
    """

@app.route("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
