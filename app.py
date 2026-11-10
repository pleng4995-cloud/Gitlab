from flask import Flask, render_template

app = Flask(__name__)

DEFAULTS = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "4700",
    "re": "1000",
    "beta": "150",
    "vbe": "0.7",
}


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html", values=DEFAULTS, errors={})


if __name__ == "__main__":
    app.run(debug=False)
