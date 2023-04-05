from click import command
from dash import Dash, dash_table, Input, Output, callback_context
from dash import html
import pandas as pd
from sub import QR_condition_control, camera_alternative
import multiprocessing as mp
from google_spreadsheet import submitLogtoSheet

#---------------------------Not use now--------------------------------------------------------------------------------
# Import data via google sheet url then change it to csv file
sheet_url = "https://docs.google.com/spreadsheets/d/15nm6_e1Y7TERlAh3LYZOc_7Ia-PnVw_n75Ngsx7iRm8/edit#gid=0"
url_1 = sheet_url.replace('/edit#gid=','/export?format=csv&gid=') # Change google sheet file to csv file
data = pd.read_csv(url_1)
#-------------------------------------------------------------------------------------------------------------------------------

# Test with offline data [Use this as a test file]
# data = pd.read_csv('Offline Data.csv')

# Import font from google font
external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
        "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    }
]

app = Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Raspberry-Pi Web Application"

# Screen configuration
app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.H1(children="Raspberry-Pi Web Application", className="header-title"),
                html.P(
                children="Display Date, Direction of Object, and "
                "Where is the command from",
                className="header-description"
                ),
            ],
            className="header"
        ),

        html.Div(
            children=[
                html.Button('ForwardStop', id='btn-nclicks-1', n_clicks=0, className='button1'),
                html.Button('Center', id='btn-nclicks-2', n_clicks=0, className='button2'),
                html.Button('BackwardStop', id='btn-nclicks-3', n_clicks=0, className='button3'),
                html.Div(id='container-button-timestamp'),   
            ],
            className="button"
        ),
        html.Div(
            children=[
                html.Img(src='https://lh3.ggpht.com/e3oZddUHSC6EcnxC80rl_6HbY94sM63dn6KrEXJ-C4GIUN-t1XM0uYA_WUwyhbIHmVMH=w300', style={'float':'left', 'display': 'inline'},className='sheet-logo'),
                html.H1(children="Google Sheet Live Data ", className="data-header"),
                html.P(children="Shows Operation Data from google sheet", className="data-description"),   
               
            ],
            className="data-body"
        ),
        html.Div(
            children=[
                dash_table.DataTable(data.to_dict('records'),
                columns=[{'id': c, 'name': c} for c in data.columns],
                style_cell={
                    'textAlign': 'left',
                    'border': '1px solid grey'
                    },
                style_cell_conditional=[
                    {'if': {'column_id': 'Date'},
                    'width': '10%'},
                    {'if': {'column_id': 'Action'},
                    'width': '30%'},
                    {'if': {'column_id': 'Via'},
                    'width': '30%'},],
                style_data={
                    'color': 'black',
                    'backgroundColor': 'white'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(220, 220, 220)',
                    }
                ],)
            ],
            className="data-table"
        )
        
    ]
)

@app.callback(
    Output('container-button-timestamp', 'children'),
    Input('btn-nclicks-1', 'n_clicks'),
    Input('btn-nclicks-2', 'n_clicks'),
    Input('btn-nclicks-3', 'n_clicks')
)

def displayClick(btn1, btn2, btn3):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    if 'btn-nclicks-1' in changed_id:
        command = 'forwardStop'
    elif 'btn-nclicks-2' in changed_id:
        command = 'center'
    elif 'btn-nclicks-3' in changed_id:
        command = 'backwardStop'
    else:
        command = '(unregistered)'
    submitLogtoSheet(command, "Web App")
    QR_condition_control(command)        
    print(command)

# Start the application via dash sever
if __name__ == '__main__':
    # For Development only, otherwise use gunicorn or uwsgi to launch, e.g.
    # gunicorn -b 0.0.0.0:8050 index:app.server
    process_1 = mp.Process(target=camera_alternative)
    process_1.start()
    app.run_server(
        port=8050,
        host='172.20.10.13',
        debug=True
    )