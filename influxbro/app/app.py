from flask import Flask, render_template, request, jsonify
import os

APP_VERSION = "1.0.0"

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html", version=APP_VERSION)

@app.route("/config")
def config():
    return render_template("config.html", version=APP_VERSION)

@app.post("/api/autodetect")
def autodetect():
    path = request.json.get("path", "/homeassistant/influx.yaml")
    if not os.path.exists(path):
        return jsonify({"ok": False, "error": f"Datei nicht gefunden unter: {path}"})
    return jsonify({"ok": True, "message": f"Gefunden: {path}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8099)