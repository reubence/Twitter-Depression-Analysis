import flask
import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import requests
from bs4 import BeautifulSoup
import nltk
import re
from dash.dependencies import Output, Input, State

stylesheets = 'https://stackpath.bootstrapcdn.com/bootswatch/4.5.0/cyborg/bootstrap.min.css'

# server = flask.Flask(__name__)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX])
server = app.server

emoticons_sad = set([
    ':L', ':-/', '>:/', ':S', '>:[', ':@', ':-(', ':[', ':-||', '=L', ':<',
    ':-[', ':-<', '=\\', '=/', '>:(', ':(', '>.<', ":'-(", ":'(", ':\\', ':-c',
    ':c', ':{', '>:\\', ';('
    ])

emoticons_happy = set([
    ':-)', ':)', ';)', ':o)', ':]', ':3', ':c)', ':>', '=]', '8)', '=)', ':}',
    ':^)', ':-D', ':D', '8-D', '8D', 'x-D', 'xD', 'X-D', 'XD', '=-D', '=D',
    '=-3', '=3', ':-))', ":'-)", ":')", ':*', ':^*', '>:P', ':-P', ':P', 'X-P',
    'x-p', 'xp', 'XP', ':-p', ':p', '=p', ':-b', ':b', '>:)', '>;)', '>:-)',
    '<3'
    ])


def preprocess(text):  # text pre-processing function
    text = str(text)
    text = text.lower()  # lower case
    # text = text.replace(u'\U0001F494', "sad")
    text = ' '.join([w for w in text.split() if w not in emoticons])  # list-comprehension
    text = re.sub("&amp;", 'and', text)  # replace ampersand with and
    text = re.sub(r'<[^>]+>', '', text)  # html tags
    text = ' '.join(
        re.sub("(#[A-Za-z0-9]+)|(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", text).split())  # remove hashtags
    text = re.sub(r'\b(http|https):\/\/.*[^ alt]\b', '', text)  # html link remove
    text = re.sub("^\d+\s|\s\d+\s|\s\d+$", " ", text)  # numbers
    text = re.sub(r'[^\w\s]', ' ', text)  # PUNCTUATIONS

    return text if text != "" else np.nan  # NAN/ NULL

emoticons = emoticons_happy.union(emoticons_sad)


nav = dbc.Navbar(children=[
    dbc.Col(dbc.Button("Twitter Depression Analysis", color='orange', id='jiobutton', style={'color': '#FFFFFF', 'font-size': 25})),
],
    color="primary",
    dark=True,
    # className="mb-5",
    sticky='top',
)
app.layout = html.Div([
nav,

html.Div(
    [
        dbc.Input(id="input", placeholder="Enter Twitter Username...", type="text", bs_size="lg", style = {'width': '45%'}),
        html.Br(),
        html.P(id="output"),
    ],style = {'width': '100%', 'display': 'flex', 'align-items':'center', 'justify-content': 'center', "margin-top" : "15%"}
),
    html.Div(
        [
            dbc.Button("BEGIN ANALYSIS", color="primary", className="submit-val", id = "open"),
            dbc.Modal(
                [
                    dbc.ModalHeader("The Person is :"),
                    dbc.ModalBody(html.P(id="depres")),
                    dbc.ModalFooter(
                        dbc.Button("Close", id="close", className="ml-auto")
                    ),
                ],
                id="modal",
                size = "xl",
                centered=True
            ),

        ],
        style={'width': '100%', 'display': 'flex', 'align-items':'center', 'justify-content': 'center', "margin-top" : "5%"}
    )

])
@app.callback(Output("depres", "children"), [Input("input", "value")])
def output_text(value):
    contents = requests.get("https://mobile.twitter.com/"+value)
    soup = BeautifulSoup(contents.text, "html.parser")
    tweets = soup.find_all("tr", {"class": "tweet-container"})
    clean_tweets = []
    import re
    for i in tweets:
        latest = re.sub('Replying to', '', i.text)
        latest = re.sub('@[^\s]+', '', latest)
        clean_tweets.append(latest.strip())

    return preprocess(clean_tweets)



@app.callback(
    Output("modal", "is_open"),
    [Input("open", "n_clicks"), Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


if __name__ == '__main__':
    app.run_server(debug = True)