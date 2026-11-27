"""
DevOps Lab 4 - Sample Flask Application
Author: Arghyadipta Goswami
Roll: 2301010192
Section: C
Subject: DEV OPS AUTOMATION
Year: 2023-2027
"""

import os
from flask import Flask, jsonify

app = Flask(__name__)


def add(a, b):
    return a + b


@app.route("/")
def home():
    return jsonify(
        application="DevOps Lab 4",
        version=os.getenv("APP_VERSION", "v1"),
        status="running",
        author="Arghyadipta Goswami",
        roll="2301010192",
        section="C",
        subject="DEV OPS AUTOMATION",
        year="2023-2027",
    )


@app.route("/health")
def health():
    return jsonify(status="healthy"), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004)
