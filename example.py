# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "flask",
#     "gunicorn",
#     "more-click",
#     "asgiref",
#     "hypercorn",
#     "asyncio",
# ]
#
# [tool.uv.sources]
# more-click = { path = ".", editable = true }
# ///

"""An example app that can be served many different ways."""

import flask

app = flask.Flask(__name__)


@app.route("/")
def home() -> str:
    """Serve the homepage."""
    return "hello world"


if __name__ == "__main__":
    import more_click

    more_click.make_web_command(app)()
