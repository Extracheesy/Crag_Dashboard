import dash
from dash import html
import plotly.graph_objects as go
from dash import dcc
from dash import dash_table
import plotly.express as px
from dash.dependencies import Input, Output
from datetime import datetime
import data_preparation
import config
import utils
import ftx_api

app = dash.Dash()

df_account_usd_value, account_usd_cash, account_usd_portfolio = ftx_api.fetch_df_balance()
df_trades = ftx_api.fetch_df_mytrades()
df_trades = data_preparation.process_trades(df_trades)

df_positions = ftx_api.fetch_df_positions()
df_positions = data_preparation.process_positions(df_positions)

lst_symbols = df_account_usd_value.columns.tolist()
lst_pair_symbols = []
for symbol in lst_symbols:
    if symbol != 'USD':
        lst_pair_symbols.append(symbol + '/USD')

df_account_usd_value = df_account_usd_value.transpose()
account_usd_value = df_account_usd_value.usdValue.sum()

str_account_usd_value = 'Account total value in USD: $'+str(round(account_usd_value, 2))
str_cash_usd_value = 'Account available cash: $'+str(round(account_usd_cash, 2))
str_portfolio_value = 'Account portfolio assets engaged: $'+str(round(account_usd_portfolio, 2))

df_buy_and_sell = data_preparation.get_df_buy_and_sell(df_trades)
lst_symbols_trades = ['no_filter']
for symbol in df_buy_and_sell['symbol'].tolist():
    lst_symbols_trades.append(symbol)
lst_symbols_trades = list(dict.fromkeys(lst_symbols_trades))

ds = data_preparation.DataDescription(lst_pair_symbols)
start_date = df_trades['timestamp'][0]
start_date = start_date.strftime("%Y-%m-%d")
# start_date = start_date.strftime("%Y-%d-%m")
# start_date = '2020-01-01'

lst_data = data_preparation.record(ds, config.DIR_DATA, start_date, config.INTERVAL)
ds = data_preparation.lst_to_df(lst_data, ds)

lst_options = []
for symbol in ds.symbols:
    label = symbol
    value = symbol.split("/")[0]
    option = {'label': label, 'value': label}
    lst_options.append(option)

app.layout = html.Div(id='parent', children=[
    html.H1(id='H1', children='InTrade Research - FTX DASHBOARD', style={'textAlign': 'center', 'marginTop': 40, 'marginBottom': 40}),
    html.H1(id='H2', children='Account summary', style={'textAlign': 'center', 'marginTop': 40, 'marginBottom': 40}),

    dash_table.DataTable(id='table',
                         style_cell={'textAlign': 'center'}),

    html.H2(id='H3', children=str_account_usd_value,
            style={'textAlign': 'left', 'marginTop': 40, 'marginBottom': 40}),

    html.H2(id='H4', children=str_cash_usd_value,
            style={'textAlign': 'left', 'marginTop': 40, 'marginBottom': 40}),

    html.H2(id='H5', children=str_portfolio_value,
            style={'textAlign': 'left', 'marginTop': 40, 'marginBottom': 40}),

    dcc.Dropdown(id='dropdown_usd',
                 options=[
                     {'label': 'USD', 'value': 'usdValue'},
                     {'label': 'Size', 'value': 'availableForWithdrawal'},
                 ],
                 value='usdValue'),
    dcc.Graph(id='bar_plot'),

    dcc.Dropdown(id='dropdown',
                 options=lst_options,
                 value=lst_options[0]['value']),
    dcc.Graph(id="graph"),

    html.H1(id='H6', children='Trades performed',
            style={'textAlign': 'center', 'marginTop': 40, 'marginBottom': 40}),

    dcc.Dropdown(id='dropdown_trades_table',
                 options=lst_symbols_trades,
                 value=lst_symbols_trades[0],
                 multi=True),
    dash_table.DataTable(id='table_trades',
                         style_cell={'textAlign': 'center'}),

    html.H1(id='H7', children='Trades',
            style={'textAlign': 'center', 'marginTop': 40, 'marginBottom': 40}),

    dcc.Dropdown(id='dropdown_trades',
                 options=lst_symbols_trades,
                 value=lst_symbols_trades[0]),
    dcc.Graph(id="graph_trades"),

    dcc.Graph(id="graph_trades_2"),

    html.H1(id='H8', children='Positions',
            style={'textAlign': 'center', 'marginTop': 40, 'marginBottom': 40}),
    dash_table.DataTable(id='table_positions',
                         style_cell={'textAlign': 'center'}),
])

@app.callback(
    Output("graph", "figure"),
    Input("dropdown", "value"))
def display_candlestick(value):
    position = ds.symbols.index(value)
    df = ds.lst_data[position]
    fig = go.Figure(go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close']
    ))

    fig.update_layout(
        xaxis_rangeslider_visible='slider' in value
    )
    return fig

@app.callback(
    Output("bar_plot", "figure"),
    Input("dropdown_usd", "value"))
def display_final_status(value):
    figure = px.bar(df_account_usd_value, y=value, height=400, text=value)
    return figure


@app.callback([Output(component_id='table', component_property='data'),
               Output(component_id='table', component_property='columns')],
               Input("dropdown_usd", "value"))
def update_table(user_selection):
    df = df_account_usd_value.copy()
    df.reset_index(inplace=True)
    df.rename({'availableForWithdrawal': 'SIZES'}, axis=1, inplace=True)
    df.rename({'usdValue': 'USD VALUES'}, axis=1, inplace=True)
    df.rename({'index': 'SYMBOLS'}, axis=1, inplace=True)

    columns = [{'name': col, 'id': col} for col in df.columns]
    data = df.to_dict(orient='records')
    return data, columns

@app.callback([Output(component_id='table_trades', component_property='data'),
               Output(component_id='table_trades', component_property='columns')],
               Input("dropdown_trades_table", "value"))
def update_table_trades(value):
    df = df_trades.copy()
    for symbol in value:
        if(symbol != 'no_filter'):
            df.drop(df[df['symbol'] == symbol].index, inplace=True)
    columns = [{'name': col, 'id': col} for col in df.columns]
    data = df.to_dict(orient='records')
    return data, columns

@app.callback([Output(component_id='table_positions', component_property='data'),
               Output(component_id='table_positions', component_property='columns')],
               Input("dropdown_usd", "value"))
def update_table_positions(user_selection):
    df = df_positions.copy()
    columns = [{'name': col, 'id': col} for col in df.columns]
    data = df.to_dict(orient='records')
    return data, columns

@app.callback(
    Output("graph_trades", "figure"),
    Input("dropdown_trades", "value"))
def display_buy_and_sell(value):
    df = df_buy_and_sell.copy()
    if(value != 'no_filter'):
        df.drop(df[df['symbol'] != value].index, inplace=True)

    # df.set_index('timestamp', inplace=True)
    fig = px.bar(df, y="buy_sell", text="price")

    fig.update_layout(
        xaxis_rangeslider_visible='slider' in value
    )
    return fig

@app.callback(
    Output("graph_trades_2", "figure"),
    Input("dropdown_trades", "value"))
def display_buy_and_sell(value):
    df = df_buy_and_sell.copy()
    if(value != 'no_filter'):
        df.drop(df[df['symbol'] != value].index, inplace=True)
    # df['timestamp'] = df['timestamp'].apply(lambda x: x.replace(microsecond=0))
    # df['timestamp'] = df['timestamp'].apply(lambda x: x.replace(second=0))

    fig = px.scatter(df, x="timestamp", y="price", text='price')
    # fig = go.Figure([go.Scatter(x=df['timestamp'], y=df['price'])])
    fig.update_layout(
        xaxis_rangeslider_visible='slider' in value
    )
    return fig

if __name__ == '__main__':
    app.run_server()