import json
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
import numpy as np
import pandas as pd
from dash.dependencies import Input, Output, State

from .constants import THRESHOLD_POSITION
from .html_functions import (
    put_tab_2_into_html,
    make_dash_table_from_dataframe,
    get_file_contents_and_analyze,
)

def init_dashboard(server):
    dash_app = dash.Dash(
        __name__,
        server=server,
        routes_pathname_prefix='/standardapp/',
        prevent_initial_callbacks=True,
        suppress_callback_exceptions=True
    )

    # Serving locally
    dash_app.css.config.serve_locally = True
    dash_app.scripts.config.serve_locally = True

    # contains the reference file
    tab1 = dbc.Tab(
        label="Reference File",
        id="tab-1",
        children=[
            html.Div(id="reference-row"),
            dcc.Store(id="reference-table"),
            dcc.Interval(
                id='interval-component1',
                interval=10*1000, # in milliseconds
                n_intervals=0
        ),
        dcc.Location(id='url', refresh=False),
        ],
    )

    # shows overall summary graphs of deviations from reference file
    tab2 = dbc.Tab(
        label="Sample Files",
        id="tab-2",
        children=[
            dbc.Row(
                children=[
                    dbc.Col(
                        [
                            html.H5("{} Threshold ".format(k[0].upper() + k[1::])),
                            dbc.Input(
                                id="{}-threshold".format(k),
                                type="number",
                                placeholder="{} threshold".format(k[0].upper() + k[1::]),
                                step=0.01,
                                disabled=True
                            ),
                        ],
                        width=4,
                        align="center",
                    )
                    for k in ["position", "fwhm", "height"]
                ],
                align="center",
                className="mt-3 mb-3",
                justify="center",
            ),
            dcc.Store(id="differences-table-storage"),
            html.Div(id="differences-table"),
            dcc.Interval(
                id='interval-component2',
                interval=10*1000, # in milliseconds
                n_intervals=0),
        ],
    )

    # shows details for each file uploaded including peaks picked and individual deviations
    tab3 = dbc.Tab(
        label="Details",
        id="tab-3",
        children=[
            html.Div(id="samples-uploaded"),
            dcc.Interval(
                id='interval-component3',
                interval=10*1000, # in milliseconds
                n_intervals=0)
        ],
    )
    dash_app.layout = dbc.Container(dbc.Tabs(children=[tab1, tab2, tab3], className="nav-fill"))
    init_callbacks(dash_app)

    return dash_app.server

def init_callbacks(dash_app):
    @dash_app.callback(
        Output("reference-row", "children"),
        Input('interval-component1', 'n_intervals'),
        Input('url', 'pathname'),
    )
    def update_output_tab_1(n, pathname):
        hostname = pathname.split("/")[-1].upper()
        data_table = pd.read_csv(".//reference_files//" + hostname + "//reference_std.csv")
        row1 = dbc.Row(children=html.Label("Reference Standard:"), align="center")
        row2 = make_dash_table_from_dataframe(table=data_table, with_slash=1)
        return [row1, row2]


    @dash_app.callback(
        Output("samples-uploaded", "children"),
        Output("differences-table-storage", "data"),
        Input('interval-component2', 'n_intervals'),
        [Input("{}-threshold".format(i), "value") for i in ["position", "fwhm", "height"]],
        Input('url', 'pathname'),
    )
    def update_output_tab_3(
        n, threshold_position, threshold_fwhm, threshold_height, pathname
    ):
        hostname = pathname.split("/")[-1].upper()
        most_recent_std_path = Path(".//reference_files//" + hostname + "//most_recent_standard.json")
        with open(most_recent_std_path.absolute(), 'r') as f:
            most_recent_std = json.load(f)
            if most_recent_std is not None:
                children = []
                positions = pd.DataFrame()
                fwhms = pd.DataFrame()
                heights = pd.DataFrame()

                ref_df = pd.read_csv(".//reference_files//" + hostname + "//reference_std.csv")

                data_table, diff, fig, info_card, ref_df_filtered = get_file_contents_and_analyze(
                    most_recent_std, ref_df
                )
                col1 = dbc.Col(info_card, width=3)
                col2 = dbc.Col(dcc.Graph(figure=fig), width=9)
                row1 = dbc.Row(children=[col1, col2], align="center")
                row2 = make_dash_table_from_dataframe(
                    table=data_table,
                    with_slash=3,
                    threshold_position=threshold_position,
                    threshold_fwhm=threshold_fwhm,
                    threshold_height=threshold_height,
                )

                children += [row1, row2]

                positions = positions.append(diff.iloc[[0]])
                fwhms = fwhms.append(diff.iloc[[2]])
                heights = heights.append(diff.iloc[[1]])

                peak_metadata = {
                    "positions": positions.to_json(orient="split"),
                    "fwhms": fwhms.to_json(orient="split"),
                    "heights": heights.to_json(orient="split"),
                }

                return children, json.dumps(peak_metadata)

            else:
                return [], {}


    @dash_app.callback(
        Output("differences-table", "children"),
        Input("differences-table-storage", "data"),
        [Input("{}-threshold".format(i), "value") for i in ["position", "fwhm", "height"]],
    )
    def get_peak_metadata_from_storage(
        metadata, threshold_position, threshold_fwhm, threshold_height
    ):
        if metadata == {}:
            return []
        else:
            metadata = json.loads(metadata)
            positions = pd.read_json(
                metadata["positions"],
                orient="split",
            )
            fwhms = pd.read_json(metadata["fwhms"], orient="split")
            heights = pd.read_json(metadata["heights"], orient="split")

            positions = positions.round(2)
            fwhms = fwhms.round(2)
            heights = heights.round(2)

            return put_tab_2_into_html(
                positions,
                threshold_position,
                fwhms,
                threshold_fwhm,
                heights,
                threshold_height,
            )


    @dash_app.callback(
        [Output("{}-threshold".format(i), "value") for i in ["position", "fwhm", "height"]],
        Input('interval-component3', 'n_intervals'),
        Input('url', 'pathname') # TODO: Put this everywhere there is a url that gets got.
    )
    def calculate_thresholds(n, pathname):
        # ref_df = pd.read_csv('.//reference_files//reference_std.csv')
        # _, threshold_fwhm, threshold_height = np.round(
        #     (ref_df.max(axis=1).values / 10.0), 2
        # )
        hostname = pathname.split("/")[-1].upper()
        config_path = Path(".//reference_files//" + hostname + "//config.json")
        with open(config_path.absolute(), 'r') as f:
            config_json = json.load(f)
            threshold_position = config_json["STDPositionThreshold"]
            threshold_fwhm = config_json["STDFWHMThreshold"]
            threshold_height = config_json["STDHeightThreshold"]
            f.close()
            

        threshold_position = threshold_position

        return threshold_position, threshold_fwhm, threshold_height