import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.graph_objects as go
import pandas as pd
import requests

# Inicializar la app
app = dash.Dash(__name__)
app.title = "Dashboard Financiero Comparativo"

# Cargar datos desde la API local
try:
    response = requests.get("http://backend:8000/data")  # CAMBIA esto si tu backend usa otro host o puerto
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data)

    # Validación mínima
    if "ticker" not in df.columns or "date" not in df.columns:
        raise ValueError("Faltan columnas requeridas en los datos")
except Exception as e:
    print(f"Error al obtener datos: {e}")
    df = pd.DataFrame()

# Columnas financieras para comparación (excluye campos no numéricos o no útiles)
value_columns = [
    col for col in df.columns
    if col not in ["index", "date", "ticker", "close", "open", "high", "low", "vol"]
    and pd.api.types.is_numeric_dtype(df[col])
] if not df.empty else []

# Layout
app.layout = html.Div([
    html.H1("Dashboard Financiero Comparativo"),

    html.Div([
        html.Label("Seleccionar Ticker:"),
        dcc.Dropdown(
            id="ticker-selector",
            options=[{"label": t, "value": t} for t in df["ticker"].unique()] if not df.empty else [],
            value=df["ticker"].iloc[0] if not df.empty else None,
            multi=False,
            clearable=False
        )
    ], style={"width": "40%", "margin-bottom": "20px"}),

    html.Div([
        html.Label("Seleccionar Métrica a Comparar con el Precio:"),
        dcc.Dropdown(
            id="metric-selector",
            options=[{"label": m, "value": m} for m in value_columns],
            value=value_columns[0] if value_columns else None,
            multi=False,
            clearable=False
        )
    ], style={"width": "40%", "margin-bottom": "20px"}),

    dcc.Graph(id="comparison-graph"),

    html.H2("Datos Financieros del Ticker Seleccionado"),
    dash_table.DataTable(
        id="financial-table",
        columns=[{"name": col, "id": col} for col in df.columns] if not df.empty else [],
        data=[],
        page_size=10,
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left", "padding": "5px"},
        style_header={"backgroundColor": "lightgrey", "fontWeight": "bold"}
    )
])

# Callback para actualizar la gráfica y la tabla
@app.callback(
    Output("comparison-graph", "figure"),
    Output("financial-table", "data"),
    Input("ticker-selector", "value"),
    Input("metric-selector", "value")
)
def update_comparison(ticker, metric):
    if df.empty or not ticker or not metric:
        return go.Figure(), []

    filtered_df = df[df["ticker"] == ticker].copy()

    # Asegurar formato de fechas
    filtered_df["date"] = pd.to_datetime(filtered_df["date"])
    filtered_df.sort_values("date", inplace=True)

    # Crear figura con doble eje Y
    fig = go.Figure()

    # Línea del precio (eje Y1)
    fig.add_trace(go.Scatter(
        x=filtered_df["date"],
        y=filtered_df["close"],
        name="Precio (Close)",
        mode="lines",
        line=dict(color="blue"),
        yaxis="y1",
        hovertemplate="Fecha: %{x}<br>Precio: %{y:.2f}<extra></extra>"
    ))

    # Línea de la métrica seleccionada (eje Y2)
    fig.add_trace(go.Scatter(
        x=filtered_df["date"],
        y=filtered_df[metric],
        name=metric,
        mode="lines",
        line=dict(color="orange", dash="dot"),
        yaxis="y2",
        hovertemplate=f"Fecha: %{{x}}<br>{metric}: %{{y:.2f}}<extra></extra>"
    ))

    # Configurar layout con doble eje Y
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
