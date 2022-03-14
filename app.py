# Import required libraries

import sqlite3

import dash
import numpy as np
import pandas as pd
from dash import dcc, html
from dash.dependencies import Input, Output
from flask import Flask

from layout import run_standalone_app

# configure dash app
server = Flask(__name__)
app = dash.Dash(__name__, server)
app.title = "rwalk"
app_title = "Random Walk"
repo_url = "https://github.com/andros21/rwalk"


SQLITE3_DB = "/data/rwalker.sqlite3"

DATASETS = {
    1: {
        "label": "classic",
        "table": "crw_pdf",
    },
    2: {
        "label": "quantum",
        "table": "qrw_pdf",
    },
    3: {
        "label": "classic-std",
        "table": "crw_std",
    },
    4: {
        "label": "quantum-std",
        "table": "qrw_std",
    },
}

engine = sqlite3.connect(SQLITE3_DB)
for dataset in DATASETS:
    DATASETS[dataset]["dataframe"] = pd.read_sql(
        f"select * from {DATASETS[dataset]['table']}", engine
    )
engine.close()


def description():
    return "Interactive random walk application"


def header_colors():
    return {"bg_color": "#990099", "font_color": "white", "light_logo": True}


def layout():
    return html.Div(
        id="vp-page-content",
        className="app-body",
        children=[
            dcc.Tabs(
                id="vp-plot-tabs",
                value="pdf",
                children=[
                    dcc.Tab(
                        label="Density Function",
                        value="pdf",
                        children=[
                            html.Div(
                                id="vp-graph-div",
                                children=dcc.Graph(
                                    id="vp-graph",
                                ),
                            ),
                        ],
                    ),
                    dcc.Tab(
                        label="Standard Deviation",
                        value="std",
                        children=[
                            html.Div(
                                id="vp-graph-std-div",
                                children=dcc.Graph(
                                    id="vp-graph-std",
                                ),
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                id="vp-control-tabs",
                className="control-tabs",
                children=[
                    dcc.Tabs(
                        id="vp-tabs",
                        value="what-is",
                        children=[
                            dcc.Tab(
                                label="About",
                                value="what-is",
                                children=html.Div(
                                    className="control-tab",
                                    children=[
                                        html.H4(
                                            className="what-is",
                                            children="What is RW?",
                                        ),
                                        html.P(
                                            "In mathematics, a random walk is a random process that describes a path that consists of a succession of random steps on space. An elementary example of a random walk is the random walk on the integer number line which starts at 0, and at each step moves +1 or −1 with equal probability."
                                        ),
                                        html.P(
                                            "Let's focus on it, and check out the main differences between a classic rw and quantum rw (coin is up or down)?"
                                        ),
                                        html.P(
                                            'In the "Plot" tab, you can play with the evolution of '
                                            "density function and its associated standard deviation."
                                        ),
                                        html.P("Quantum random walk is must faster!"),
                                    ],
                                ),
                            ),
                            dcc.Tab(
                                label="Plot",
                                value="data",
                                children=html.Div(
                                    className="control-tab",
                                    children=[
                                        html.Div(
                                            className="app-controls-block",
                                            children=[
                                                html.Div(
                                                    className="app-controls-name",
                                                    children="Walker",
                                                ),
                                                dcc.RadioItems(
                                                    id="vp-dataset-radio",
                                                    options=[
                                                        {
                                                            "label": DATASETS[dset][
                                                                "label"
                                                            ],
                                                            "value": dset,
                                                        }
                                                        for dset in [1, 2]
                                                    ],
                                                    value=1,
                                                    inline=True,
                                                ),
                                                html.Div(
                                                    className="app-controls-name",
                                                    children="Steps",
                                                ),
                                                dcc.Slider(
                                                    10,
                                                    100,
                                                    10,
                                                    value=50,
                                                    id="vp-dataset-slider",
                                                ),
                                            ],
                                        )
                                    ],
                                ),
                            ),
                        ],
                    )
                ],
            ),
        ],
    )


def callbacks(_app):
    @_app.callback(
        Output("vp-graph", "figure"),
        [Input("vp-dataset-radio", "value"), Input("vp-dataset-slider", "value")],
    )
    def update_graph(dataset_id, step):
        """Update density function plot"""
        color = "#119dff" if dataset_id == 1 else "#ffce19"
        sites = (
            np.arange(-50, 50 + 1, 1) if dataset_id == 1 else np.arange(-80, 80 + 1, 1)
        )
        return {
            "data": [
                dict(
                    type="scatter",
                    fill="tozeroy",
                    x=sites,
                    y=DATASETS[dataset_id]["dataframe"].loc[step].to_numpy(),
                    marker={
                        "color": color,
                    },
                )
            ],
            "layout": dict(
                xaxis={"title": "sites"},
                yaxis={"title": "pdf"},
            ),
        }

    @_app.callback(
        Output("vp-graph-std", "figure"),
        [Input("vp-dataset-slider", "value")],
    )
    def update_graph(step):
        """Update standard deviation plot"""
        return {
            "data": [
                dict(
                    type="scatter",
                    x=DATASETS[3]["dataframe"].index.to_numpy()[0:step],
                    y=DATASETS[3]["dataframe"]["0"][0:step],
                    name="classic",
                    marker={
                        "color": "#119dff",
                    },
                ),
                dict(
                    type="scatter",
                    x=DATASETS[4]["dataframe"].index.to_numpy()[0:step],
                    y=DATASETS[4]["dataframe"]["0"][0:step],
                    name="quantum",
                    marker={
                        "color": "#ffce19",
                    },
                ),
            ],
            "layout": dict(
                xaxis={"title": "steps"},
                yaxis={"title": "std"},
            ),
        }


run_standalone_app(app, app_title, repo_url, layout, callbacks, header_colors, __file__)

if __name__ == "__main__":
    app.run_server()
