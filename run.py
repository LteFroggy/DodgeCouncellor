from flask import Flask
from flask.templating import render_template
from app import app

app.run(host="0.0.0.0", port=80, debug = True)