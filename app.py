#!/home/rafal/environment-monitor/venv/bin/python

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

import datetime

from measurer import MeasurementsArchive
from plotter import Plotter

def app_layout():
  return html.Div(
    [
      html.Div(
        [
          html.Div(
            [
              html.Label("Plot:"),
              dcc.Checklist(
                id="parameters-inputlist",
                options=[
                    {"label":dict["name"], "value":label} for label, dict in Plotter.PARAMETERS.items()
                ],
                value=list(Plotter.PARAMETERS.keys()),
                className="form-inputlist",
                labelClassName="form-inputlist-label",
                inputClassName="form-inputlist-input"
              )
            ],
            className="menu-form menu-form-left"
          ),
          html.Div(
            [
              html.Label("Period:"),
              dcc.RadioItems(
                id="period-inputlist",
                options=[
                  {"label": "Last 24 hours", "value": "last24"},
                  {"label": "Custom:", "value": "custom"}
                ],
                value="last24",
                className="form-inputlist",
                labelClassName="form-inputlist-label",
                inputClassName="form-inputlist-input"
              ),
              dcc.DatePickerRange(
                id="custom-period-picker",
                display_format="DD.MM.YYYY",
                disabled=True
              )
            ],
            className="menu-form"
          )
        ],
        className="menu"
      ),
      dcc.Graph(
        id='graph',
        responsive=True,
        className="graph"
      ),
      dcc.Interval(
        id="refresher",
        interval=20*1000
      )
    ],
    className="container"
  )

ARCHIVE = MeasurementsArchive("/home/rafal/environment-monitor/measurements")
ARCHIVE.open()
PLOTTER = Plotter(ARCHIVE)

app = dash.Dash(__name__)
app.layout = app_layout()

@app.callback(
  Output("refresher", "disabled"),
  Output("custom-period-picker", "disabled"),
  Input("period-inputlist", "value")
)
def change_refresh_method(period_selection):
  return [True, False] if period_selection == "custom" else [False, True]

@app.callback(
  Output("custom-period-picker", "min_date_allowed"),
  Output("custom-period-picker", "max_date_allowed"),
  Output("custom-period-picker", "start_date"),
  Output("custom-period-picker", "end_date"),
  Input("refresher", "n_intervals")
)
def update_custom_period_picker(_):
  return [
    ARCHIVE.archive_start(),
    ARCHIVE.archive_end(),
    datetime.datetime.now() - datetime.timedelta(hours=24),
    datetime.datetime.now()
  ]

@app.callback(
  Output("graph", "figure"),
  Input("refresher", "n_intervals"),
  Input("period-inputlist", "value"),
  Input("parameters-inputlist", "value"),
  Input("custom-period-picker", "start_date"),
  Input("custom-period-picker", "end_date"),
)
def update_plot(_, period_selection, parameter_selection, custom_start, custom_end):
  print("update_plot")
  ARCHIVE.refresh()
  if period_selection == "last24":  
    end = datetime.datetime.now()
    start = end - datetime.timedelta(hours=24)
  else:
    print(f"Custom start:{custom_start}, end:{custom_end}")
    end=datetime.datetime.fromisoformat(custom_end)
    start=datetime.datetime.fromisoformat(custom_start)
  
  return PLOTTER.get_plot(start, end, parameter_selection)

if __name__ == '__main__':
  app.run_server(host='0.0.0.0', debug=False)
