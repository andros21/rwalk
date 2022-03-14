import base64

from dash import dcc, html


def run_standalone_app(
    app, app_title, repo_url, layout, callbacks, header_colors, filename
):
    """Run app as standalone app"""
    app.layout = app_page_layout(
        repo_url,
        page_layout=layout(),
        app_title=app_title,
        standalone=True,
        **header_colors()
    )

    # Register all callbacks
    callbacks(app)


def app_page_layout(
    repo_url,
    page_layout,
    app_title,
    light_logo=True,
    standalone=False,
    bg_color="#006784",
    font_color="#F3F6FA",
):
    return html.Div(
        id="main_page",
        children=[
            dcc.Location(id="url", refresh=False),
            html.Div(
                id="app-page-header",
                children=[
                    html.A(
                        id="dashbio-logo",
                        children=[
                            html.Img(
                                src="data:image/png;base64,{}".format(
                                    base64.b64encode(
                                        open(
                                            "./assets/plotly-dash-bio-logo.png", "rb"
                                        ).read()
                                    ).decode()
                                )
                            )
                        ],
                        href="https://plotly.com/dash/",
                    ),
                    html.H2(app_title),
                    html.A(
                        id="gh-link",
                        children=["View on GitHub"],
                        href=repo_url,
                        style={
                            "color": "white" if light_logo else "black",
                            "border": "solid 1px white"
                            if light_logo
                            else "solid 1px black",
                        },
                    ),
                    html.Img(
                        src="data:image/png;base64,{}".format(
                            base64.b64encode(
                                open(
                                    "./assets/GitHub-Mark-{}64px.png".format(
                                        "Light-" if light_logo else ""
                                    ),
                                    "rb",
                                ).read()
                            ).decode()
                        )
                    ),
                ],
                style={
                    "background": bg_color,
                    "color": font_color,
                },
            ),
            html.Div(id="app-page-content", children=page_layout),
        ],
    )
