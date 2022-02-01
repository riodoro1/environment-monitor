#!/home/rafal/climate-monitor/climate-monitor-venv/bin/python

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
import math

import time,threading
import datetime

from smbus import SMBus
from bme280 import BME280


from measurer import MeasurementsArchive

PARAMETERS=["temperature", "humidity", "pressure"]
PARAMETER_NAMES={"temperature":"Temperature",
                 "humidity":"Humidity",
                 "pressure":"Pressure"}
PARAMETER_COLORS={"temperature":"#EF553B",
                  "humidity":"#636EFA",
                  "pressure":"#00CC96"}
PARAMETER_FORMATS={"temperature":{"format":"0.1f", "suffix":"°C"},
                   "humidity":{"format":"0.0f", "suffix":"%"},
                   "pressure":{"format":"0.0f", "suffix":"hPa"}}

Y_AXIS_TICKS=5
Y_DOMAIN_GAP=0.02
PLOT_GRID_COLOR="#ccc"

def generate_plot(archive, start, end, parameters):
  print(f"Generating plot from {start} to {end}")
  entries=archive.entries_in_span(start, end)
  combined_df=pd.DataFrame()

  print("Obtained these entries:")
  for e in entries:
    print(f"\t{e} from {e.path}")
    e.open()
    combined_df=combined_df.append(e.dataframe[start : end])
    e.close()

  fig = go.Figure()
  if len(parameters)==0:
    return fig

  # Set general plot layout
  fig.update_layout(
    showlegend=False,
    autosize=True,
    plot_bgcolor="#fff",
    hovermode="x"
  )

  # Set X axis layout
  fig.update_layout(xaxis=dict(
      title=dict(
        text="<b>Time</b>",
        font=dict(
          size=12
        )
      ),
      side="top",
      showgrid=True,
      showspikes=True,
      spikemode="across",
      spikethickness=2,
      gridcolor=PLOT_GRID_COLOR,
      ticks="outside",
      tickcolor=PLOT_GRID_COLOR,
      tickwidth=1,
      ticklen=10,
      mirror="ticks",
      fixedrange=True,
      rangeslider=dict(
        visible=True,
        borderwidth=1,
      )
    ),
  )

  n_subplots=((len(parameters) + 1) // 2)
  n_gaps=n_subplots-1
  subplot_height=(1.0-n_gaps*Y_DOMAIN_GAP)/n_subplots

  for i in range(len(parameters)):
    parameter=parameters[i]

    # Add trace
    fig.add_trace(go.Scatter(
      x=combined_df.index,
      y=combined_df[parameter],
      yaxis=f"y{i+1}",
      name=PARAMETER_NAMES[parameter],
      line=dict(
        color=PARAMETER_COLORS[parameter]
      )
    ))

    # Y axis calculated properties
    y_axis_min=combined_df[parameter].min()
    y_axis_step=(combined_df[parameter].max()-y_axis_min)/(Y_AXIS_TICKS-1)
    y_axis_side="left" if i%2==0 else "right"
    y_axis_overlaying="free" if i%2==0 else f"y{i}" if i!=0 else "y"
    y_axis_domain_upper=round(1-i//2*(subplot_height+Y_DOMAIN_GAP),3)
    y_axis_domain_lower=round(y_axis_domain_upper-subplot_height,3)

    print(f"i:{i} ({PARAMETER_NAMES[parameter]})")
    print(f"\tmin: {y_axis_min}")
    print(f"\tstep: {y_axis_step}")
    print(f"\tside: {y_axis_side}")
    print(f"\toverlying: {y_axis_overlaying}")
    print(f"\td_upper: {y_axis_domain_upper}")
    print(f"\td_lower: {y_axis_domain_lower}")

    # Set Y axis layout
    yaxis_layout=dict(
      title=dict(
        text=f"<b>{PARAMETER_NAMES[parameter]}</b>",
        font=dict(
          size=12
      ),
        standoff=4
      ),
      tickfont=dict(
        size=11
      ),

      color=PARAMETER_COLORS[parameter],
      gridcolor=PLOT_GRID_COLOR,
      showgrid=True,
      showspikes=True,
      spikemode="toaxis",
      spikethickness=2,
      fixedrange=True,

      tick0=y_axis_min,
      dtick=y_axis_step,
      tickformat=PARAMETER_FORMATS[parameter]["format"],
      ticksuffix=PARAMETER_FORMATS[parameter]["suffix"],

      side=y_axis_side,
      overlaying=y_axis_overlaying,
      domain=[y_axis_domain_lower, y_axis_domain_upper],
      automargin=True,
      anchor="x",
    )

    # Apply layout
    fig.update_layout(**{f"yaxis{i+1}":yaxis_layout})

  return fig

app = dash.Dash(__name__)

app.layout = html.Div(
  [
    html.Div(
      [
        html.Div(
          [
            html.Label("Plot:"),
            dcc.Checklist(
              id="parameters-checklist",
              options=[
                  {"label": label, "value": value} for value, label in PARAMETER_NAMES.items()
              ],
              value=list(PARAMETER_NAMES.keys()),
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
              id="period-radioitems",
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
              display_format="DD.MM.YYYY"
              #disabled=True
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
      id='interval-component',
      interval=20*1000
    )
  ],
  className="container"
)

@app.callback(Output('graph', 'figure'),
        Input('interval-component', 'n_intervals'))
def update_metrics(n):
  a = MeasurementsArchive("/home/rafal/climate-monitor/measurements")
  a.open()

  end = datetime.datetime.now()
  start = end - datetime.timedelta(hours=24)

  return generate_plot(a, start, end, ["temperature", "humidity", "pressure"])


if __name__ == '__main__':
  app.run_server(host='0.0.0.0', debug=False)
