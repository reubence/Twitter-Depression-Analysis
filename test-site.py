import flask
import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import requests
from bs4 import BeautifulSoup
import nltk
import numpy as np
import re
from dash.dependencies import Output, Input, State
import snscrape.modules.twitter as sntwitter
import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer

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

lexicon_words = []

with open("Lexicon-Word.txt", "r") as f:
    for line in f:
        lexicon_words.extend(line.split())

loaded_model = pickle.load(open("pipeline.sav", 'rb'))
tf_vec = pickle.load(open("tfidf.sav", 'rb'))


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
                    dbc.ModalBody([dbc.Spinner(color="primary", size="md")], id="depres"),
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
    # Creating list to append tweet data to
    tweets_list1 = []

    # Using TwitterSearchScraper to scrape data and append tweets to list
    if value != "":
        for i, tweet in enumerate(sntwitter.TwitterSearchScraper('from:'+str(value)).get_items()):
            if i > 5:
                break
            tweets_list1.append([tweet.date, tweet.id, tweet.content, tweet.user.username])

        # Creating a dataframe from the tweets list above
        tweets = pd.DataFrame(tweets_list1, columns=['Datetime', "TweetID", 'Text', "username"])
        clean_tweets = []
        Sentiments = []
        timings = []
        lexicon_count = []
        for i,r in tweets.iterrows():

            latest = [preprocess(r["Text"])]
            print(type(latest))
            tfg = tf_vec.transform(latest)
            Sentiments.append(loaded_model.predict(tfg))
            clean_tweets.append(latest.strip())
            timings.append(r["Datetime"])

        return html.H2(clean_tweets)



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