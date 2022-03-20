#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sqlite3
import sys

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


# data dirs
if os.path.exists("/data"):
    SQLITE3_DB = "/data/rwalker.sqlite3"
else:
    SQLITE3_DB = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data/rwalker.sqlite3"
    )

# datasets
DATASETS = {
    "classic": {
        "discrete": {
            "line": {
                "table": "crw_line",
            },
            "ring": {
                "table": "crw_ring",
            },
        },
        "continuous": {
            "line": {
                "table": "crw_line_ct",
            },
            "ring": {
                "table": "crw_ring_ct",
            },
        },
    },
    "quantum": {
        "discrete": {
            "line": {
                "table": "qrw_line",
            },
            "ring": {
                "table": "qrw_ring",
            },
        },
        "continuous": {
            "line": {
                "table": "qrw_line_ct",
            },
            "ring": {
                "table": "qrw_ring_ct",
            },
        },
    },
}

# load data from sqlite3 db
colors = iter(
    [
        "#119DFF",  # classic dt line
        "#119DFF",  # classic dt ring
        "#0860C4",  # classic ct line
        "#0860C4",  # classic ct ring
        "#FFCE19",  # quantum dt line
        "#FFCE19",  # quantum dt ring
        "#FF7700",  # quantum ct line
        "#D50000",  # quantum ct ring
    ]
)
engine = sqlite3.connect(SQLITE3_DB)
for walker in DATASETS:
    for time in DATASETS[walker]:
        for graph in DATASETS[walker][time]:
            DATASETS[walker][time][graph]["color"] = next(colors)
            DATASETS[walker][time][graph]["dataframe"] = dict()
            for tab in ["pdf", "std"]:
                DATASETS[walker][time][graph]["dataframe"][tab] = pd.read_sql(
                    f"select * from {DATASETS[walker][time][graph]['table']}_{tab}",
                    engine,
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
                                            "In mathematics, a random walk is a random process that describes a path that consists of a succession of random steps on space."
                                        ),
                                        html.P(
                                            "What are the main differences between a classic and quantum walk? "
                                            "And evolving with continuous time? And what about random walk on a ring?"
                                        ),
                                        html.P(
                                            'In the "Plot" tab, you can play with the evolution of '
                                            "density function and its associated std deviation for all these cases."
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
                                                            "label": walker,
                                                            "value": walker,
                                                        }
                                                        for walker in DATASETS
                                                    ],
                                                    value="classic",
                                                ),
                                                html.Div(
                                                    className="app-controls-name",
                                                    children="Time",
                                                ),
                                                dcc.RadioItems(
                                                    id="vp-dataset-radio-time",
                                                    options=[
                                                        {
                                                            "label": time,
                                                            "value": time,
                                                        }
                                                        for time in DATASETS["classic"]
                                                    ],
                                                    value="discrete",
                                                ),
                                                html.Div(
                                                    className="app-controls-name",
                                                    children="Graph",
                                                ),
                                                dcc.RadioItems(
                                                    id="vp-dataset-radio-graph",
                                                    options=[
                                                        {
                                                            "label": graph,
                                                            "value": graph,
                                                        }
                                                        for graph in DATASETS[
                                                            "classic"
                                                        ]["discrete"]
                                                    ],
                                                    value="line",
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
        [
            Input("vp-dataset-radio", "value"),
            Input("vp-dataset-radio-time", "value"),
            Input("vp-dataset-radio-graph", "value"),
            Input("vp-dataset-slider", "value"),
        ],
    )
    def update_pdf(walker, time, graph, step):
        """Update density function plot"""
        col = DATASETS[walker][time][graph]["color"]
        df = DATASETS[walker][time][graph]["dataframe"]["pdf"]
        if graph == "line":
            limit = int((df.columns.size - 1) * 0.5)
            sites = np.arange(-limit, limit + 1, 1)
        elif graph == "ring":
            limit = df.columns.size
            sites = np.arange(0, limit, 1)
        else:
            sys.exit(1)
        return {
            "data": [
                dict(
                    type="scatter",
                    fill="tozeroy",
                    x=sites,
                    y=df.loc[step].to_numpy(),
                    marker={
                        "color": col,
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
    def update_std(step):
        """Update standard deviation plot"""
        data = list()
        for walker in DATASETS:
            for time in DATASETS[walker]:
                for graph in DATASETS[walker][time]:
                    col = DATASETS[walker][time][graph]["color"]
                    df = DATASETS[walker][time][graph]["dataframe"]["std"]
                    nm = DATASETS[walker][time][graph]["table"]
                    data.append(
                        dict(
                            type="scatter",
                            x=df.index.to_numpy()[:step],
                            y=df["0"][:step],
                            name=nm,
                            marker={
                                "color": col,
                            },
                        )
                    )
        return {
            "data": data,
            "layout": dict(
                xaxis={"title": "steps"},
                yaxis={"title": "std"},
            ),
        }


run_standalone_app(app, app_title, repo_url, layout, callbacks, header_colors, __file__)

if __name__ == "__main__":
    app.run_server()
