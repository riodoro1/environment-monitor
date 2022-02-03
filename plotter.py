import pandas as pd
import plotly.graph_objects as go

#TODO: remove
import time

class Plotter:
  PARAMETERS={
  "temperature":{
    "name":"Temperature",
    "color":"#EF553B",
    "format":"0.1f",
    "suffix":"°C"
  },
  "humidity":{
    "name":"Humidity",
    "color":"#636EFA",
    "format":"0.0f",
    "suffix":"%"
  },
  "pressure":{
    "name":"Pressure",
    "color":"#00CC96",
    "format":"0.0f",
    "suffix":"hPa"
  },
}

  def __init__(self, archive):
    self.archive = archive
    self.previous_result = {"arguments":None, "plot":None}

  def dataframe_in_span(self, start, end):
    entries=self.archive.entries_in_span(start, end)
    combined_df=pd.DataFrame()

    for e in entries:
      was_open = e.is_open()
      if not was_open: e.open()
      combined_df=combined_df.append(e.dataframe[start : end])
      if not was_open: e.close()

    return combined_df

  def generate_plot(self, dataframe, parameters):
    Y_AXIS_TICKS=5
    SUBPLOTS_DOMAIN_GAP=0.02
    PLOT_GRID_COLOR="#ccc"

    fig = go.Figure()
    if len(parameters)==0 or dataframe.empty:
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
    subplot_height=(1.0-n_gaps*SUBPLOTS_DOMAIN_GAP)/n_subplots

    for i in range(len(parameters)):
      parameter=parameters[i]

      # Add trace
      fig.add_trace(go.Scatter(
        x=dataframe.index,
        y=dataframe[parameter],
        yaxis=f"y{i+1}",
        name=self.PARAMETERS[parameter]["name"],
        line=dict(
          color=self.PARAMETERS[parameter]["color"]
        )
      ))

      # Y axis calculated properties
      y_axis_min=dataframe[parameter].min()
      y_axis_step=(dataframe[parameter].max()-y_axis_min)/(Y_AXIS_TICKS-1)
      y_axis_side="left" if i%2==0 else "right"
      y_axis_overlaying="free" if i%2==0 else f"y{i}" if i!=0 else "y"
      y_axis_domain_upper=round(1-i//2*(subplot_height+SUBPLOTS_DOMAIN_GAP),3)
      y_axis_domain_lower=round(y_axis_domain_upper-subplot_height,3)

      # Set Y axis layout
      yaxis_layout=dict(
        title=dict(
          text=f"<b>{self.PARAMETERS[parameter]['name']}</b>",
          font=dict(
            size=12
        ),
          standoff=4
        ),
        tickfont=dict(
          size=11
        ),

        color=self.PARAMETERS[parameter]["color"],
        gridcolor=PLOT_GRID_COLOR,
        showgrid=True,
        showspikes=True,
        spikemode="toaxis",
        spikethickness=2,
        fixedrange=True,

        tick0=y_axis_min,
        dtick=y_axis_step,
        tickformat=self.PARAMETERS[parameter]["format"],
        ticksuffix=self.PARAMETERS[parameter]["suffix"],

        side=y_axis_side,
        overlaying=y_axis_overlaying,
        domain=[y_axis_domain_lower, y_axis_domain_upper],
        automargin=True,
        anchor="x",
      )

      # Apply layout
      fig.update_layout(**{f"yaxis{i+1}":yaxis_layout})

    return fig

  def get_plot(self, start, end, parameters):
    print(f"There are {len(self.archive.archive_entries)} entries in the archive.")
    function_start = time.time()

    dataframe = self.dataframe_in_span(start, end)

    arguments_dict = {
      "start":dataframe.first_valid_index(),
      "end":dataframe.last_valid_index(),
      "parameters":parameters
    }

    cached = True
    if self.previous_result["arguments"] != arguments_dict:
      self.previous_result = {"arguments":arguments_dict, "plot":self.generate_plot(dataframe, parameters)}
      cached = False

    print(f"get_plot took:{(time.time()-function_start):.2f}s. The plot was: {'recalled' if cached else 'redrawn'}")
    
    return self.previous_result["plot"]