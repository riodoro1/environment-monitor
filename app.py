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

PARAMETER_AXIS_WIDTH={"temperature":0.028,
                      "humidity":0.028,
                      "pressure":0.042}
Y_AXIS_TICKS=5
PLOT_GRID_COLOR="#333"

def generate_plot(archive, start, end, parameters):
  print(f"Generating plot from {start} to {end}")
  entries=archive.entries_in_span(start, end)
  combined_df=pd.DataFrame()

  print("Obtained these entries:")
  for e in entries:
    print(f"\t{e} from {e.path}")
    e.open()
    combined_df=combined_df.append(e.dataframe)
    e.close()

  fig = go.Figure()
  if len(parameters)==0:
    return fig

  # Set general plot layout
  fig.update_layout(
    showlegend=False,
    margin=dict(t=30, b=0, l=10, r=10), 
    autosize=True,
    #height=500,
    plot_bgcolor="#fff",
    dragmode=False,
    modebar=dict(
      remove=["pan", "zoom", "zoomin", "zoomout", "autoscale", "resetscale"]
    )
  )

  y_position=0
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

    # Calculate position of Y axis (right edge)
    y_position=y_position+PARAMETER_AXIS_WIDTH[parameter]

    # Set Y axis layout
    yaxis_layout=dict(
      title=dict(
        text=f"<b>{PARAMETER_NAMES[parameter]}</b>",
        standoff=0,
        font=dict(
          size=11
        )
      ),

      tickfont=dict(
        size=10
      ),

      color=PARAMETER_COLORS[parameter],

      tick0=y_axis_min,
      dtick=y_axis_step,
      tickformat=PARAMETER_FORMATS[parameter]["format"],
      ticksuffix=PARAMETER_FORMATS[parameter]["suffix"],

      showgrid=True,
      gridcolor=PLOT_GRID_COLOR,

      automargin=True,
      anchor="free",
      position=y_position,
      linewidth=2
    )

    # Set binding of additional Y axes to Y1
    if i>0:
      yaxis_layout.update(overlaying="y1")

    # Apply layout
    fig.update_layout(**{f"yaxis{i+1}":yaxis_layout})

  # Set X axis layout
  fig.update_layout(xaxis=dict(
      title=dict(
        text="<b>Time</b>",
        font=dict(
          size=11
        )
      ),
      domain=[y_position, 1],
      showgrid=True,
      gridcolor=PLOT_GRID_COLOR
    ),
  )

  return fig

app = dash.Dash(__name__)
app.layout = html.Div(children=[
  dcc.Graph(
    id='graph',
    responsive=True
  ),

  dcc.Interval(
    id='interval-component',
    interval=20*1000
  )
])

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
