import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.graph_objects as go
import pandas as pd
import requests
import time

# Función para obtener datos con reintentos
def get_data_with_retries(url, retries=5, delay=3):
    for i in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Intento {i+1} fallido para obtener datos de {url}: {e}")
            time.sleep(delay)
    raise Exception(f"No se pudo conectar a {url} después de {retries} intentos")

# Inicializar la app
app = dash.Dash(__name__)
app.title = "Dashboard Financiero Comparativo"

# Layout inicial con dropdowns vacíos
app.layout = html.Div([
    html.H1("Dashboard Financiero Comparativo"),

    html.Div([
        html.Label("Seleccionar Ticker:"),
        dcc.Dropdown(id="ticker-selector", multi=False, clearable=False)
    ], style={"width": "40%", "margin-bottom": "20px"}),

    html.Div([
        html.Label("Seleccionar Métrica a Comparar con el Precio:"),
        dcc.Dropdown(id="metric-selector", multi=False, clearable=False)
    ], style={"width": "40%", "margin-bottom": "20px"}),

    dcc.Graph(id="comparison-graph"),

    html.H2("Datos Financieros del Ticker Seleccionado"),
    dash_table.DataTable(
        id="financial-table",
        page_size=10,
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left", "padding": "5px"},
        style_header={"backgroundColor": "lightgrey", "fontWeight": "bold"}
    ),

    # Componente oculto para disparar la carga inicial de dropdowns
    dcc.Store(id='data-store')
])

# Callback para cargar opciones de dropdown la primera vez
@app.callback(
    Output("ticker-selector", "options"),
    Output("ticker-selector", "value"),
    Output("metric-selector", "options"),
    Output("metric-selector", "value"),
    Output("data-store", "data"),
    Input("ticker-selector", "value")  # input dummy para disparar al cargar
)
def load_dropdowns(_):
    try:
        data = get_data_with_retries("http://backend:8000/data")
        df = pd.DataFrame(data)

        tickers = [{"label": t, "value": t} for t in sorted(df["ticker"].unique())]

        value_cols = [
            col for col in df.columns
            if col not in ["index", "date", "ticker", "close", "open", "high", "low", "vol"]
            and pd.api.types.is_numeric_dtype(df[col])
        ]
        metrics = [{"label": m, "value": m} for m in value_cols]

        # Guardamos los datos en Store para reutilizar
        return tickers, tickers[0]["value"] if tickers else None, metrics, metrics[0]["value"] if metrics else None, data
    except Exception as e:
        print(f"Error cargando opciones dropdown: {e}")
        # Si falla, devuelve vacíos para que no falle la app
        return [], None, [], None, None

# Callback para actualizar gráfica y tabla con datos almacenados en Store
@app.callback(
    Output("comparison-graph", "figure"),
    Output("financial-table", "data"),
    Input("ticker-selector", "value"),
    Input("metric-selector", "value"),
    Input("data-store", "data")
)
def update_comparison(ticker, metric, data):
    if not ticker or not metric or data is None:
        return go.Figure(), []

    df = pd.DataFrame(data)
    filtered_df = df[df["ticker"] == ticker].copy()
    filtered_df["date"] = pd.to_datetime(filtered_df["date"])
    filtered_df.sort_values("date", inplace=True)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=filtered_df["date"],
        y=filtered_df["close"],
        name="Precio (Close)",
        mode="lines",
        line=dict(color="blue"),
        yaxis="y1",
        hovertemplate="Fecha: %{x}<br>Precio: %{y:.2f}<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=filtered_df["date"],
        y=filtered_df[metric],
        name=metric,
        mode="lines",
        line=dict(color="orange", dash="dot"),
        yaxis="y2",
        hovertemplate=f"Fecha: %{{x}}<br>{metric}: %{{y:.2f}}<extra></extra>"
    ))

    fig.update_layout(
        title=f"{ticker}: Precio vs {metric}",
        xaxis=dict(title="Fecha"),
        yaxis=dict(
            title="Precio (Close)",
            titlefont=dict(color="blue"),
            tickfont=dict(color="blue")
        ),
        yaxis2=dict(
            title=metric,
            titlefont=dict(color="orange"),
            tickfont=dict(color="orange"),
            overlaying="y",
            side="right"
        ),
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=60, r=60, t=50, b=50),
        hovermode="x unified"
    )

    return fig, filtered_df.to_dict("records")

# Ejecutar la app
if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)
