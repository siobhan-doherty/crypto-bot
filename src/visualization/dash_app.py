import dash 
from dash import html
from dash import dcc
import pandas as pd
from pymongo import MongoClient




# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['cryptobot']
collection = db['historical_data']


app = dash.Dash(__name__)
app.layout =  html.Div(children = " Crypto Dash API")

if __name__ == '__main__':
    app.run(debug=True, host = 'localhost', port = 8080)