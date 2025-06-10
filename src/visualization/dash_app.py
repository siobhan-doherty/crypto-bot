import dash 
from dash import html, dcc
import dash_bootstrap_components as dbc
from pymongo import MongoClient
import pandas as pd


client = MongoClient("mongodb://crypto_project:dst123@crypto_mongo:27017/")
db = client["cryptobot"]            
collection = db["historical_data"]    


# BOOTSTRAP, CERULEAN, DARKLY, FLATLY, LITERA, LUX, MATERIA, MINTY, PULSE, SANDSTONE, SIMPLEX, SKETCHY, SLATE, SOLAR, SPACELAB, UNITED
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.layout =  html.Div(children = " Crypto Dash API")

if __name__ == '__main__':
    app.run(debug=True, host = 'localhost', port = 8080)
