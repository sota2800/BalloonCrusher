from flask import Flask, render_template, send_file
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

IMAGE_PATH = os.path.join(BASE_DIR, "latest.jpg")
STATUS_PATH = os.path.join(BASE_DIR, "status.txt")
START_PATH = os.path.join(BASE_DIR, "start.flag")
RESET_PATH = os.path.join(BASE_DIR, "reset.flag")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/image")
def image():
    if os.path.exists(IMAGE_PATH):
        return send_file(
            IMAGE_PATH,
            mimetype="image/jpeg"
        )

    return "", 404


@app.route("/status")
def status():
    try:
        with open(
            STATUS_PATH,
            "r",
            encoding="utf-8"
        ) as f:
            return f.read().strip()
    except:
        return "NONE"

@app.route("/reset", methods=["POST"])
def reset():

    with open(
        RESET_PATH,
        "w",
        encoding="utf-8"
    ) as f:
        f.write("true")

    print("[WEB] RESET")

    return "OK"


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )