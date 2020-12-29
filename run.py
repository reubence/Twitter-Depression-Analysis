import flask
import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import requests
from bs4 import BeautifulSoup
import datetime
import nltk
import numpy as np
import re
from dash.dependencies import Output, Input, State
import snscrape.modules.twitter as sntwitter
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer

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


nltk.download('vader_lexicon')
sid = SentimentIntensityAnalyzer()


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
                    dbc.ModalHeader(html.H1("Null Hypothesis : This Individual is depressed")),
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
            if i > 10:
                break
            tweets_list1.append([tweet.date, tweet.id, tweet.content, tweet.user.username])
        # Creating a dataframe from the tweets list above
        tweets = pd.DataFrame(tweets_list1, columns=['Datetime', "TweetID", 'Text', "username"])
        Sentiments = []
        timings = []
        lexicon_count = []
        # print(tweets["Text"][7])
        for i,r in tweets.iterrows():
            print("i",i)
            latest = preprocess(r["Text"])
            print("latest",type(latest))
            if type(latest)==type("yolo"):
                compound = sid.polarity_scores(latest)
                print("compppoung",compound)
                if compound["compound"] >= 0:
                    Sentiments.append(1)
                else:
                    Sentiments.append(-1) # 1 = happy

                tokens = nltk.word_tokenize(latest)
                for i in tokens:
                    if i in lexicon_words:
                        lexicon_count.append(-1)
                        break
                    elif i == tokens[-1]:
                        lexicon_count.append(1)

            else:
                Sentiments.append(0)
            # clean_tweets.append(latest.strip())
            temp = str(r["Datetime"])
            if datetime.datetime.strptime("01:30:00","%H:%M:%S") <= datetime.datetime.strptime(temp[11:18],"%H:%M:%S") and datetime.datetime.strptime("04:30:00", "%H:%M:%S") >= datetime.datetime.strptime(temp[11:18],"%H:%M:%S"):
                timings.append(-1) #1 = yes awake late
            else: timings.append(1)

        print("lexi",lexicon_count)
        print("Sentis",Sentiments)
        print("Times",timings)

        t = (np.mean(Sentiments) - (-1))/np.std(Sentiments)/len(Sentiments)
        import scipy.stats
        pval = scipy.stats.t.sf(abs(t), df=len(Sentiments)-1)

        print("p - values", pval)
        if pval < 0.05:  # alpha value is 0.05 or 5%
            result_sentis = "Result of Negative Opinion Analysis :  We are Rejecting Null Hypothesis"
        else:
            result_sentis = "Result of Negative Opinion Analysis :  We are Accepting Null Hypothesis"


        t = (np.mean(lexicon_count) - (-1))/np.std(lexicon_count)/len(lexicon_count)
        import scipy.stats
        pval = scipy.stats.t.sf(abs(t), df=len(lexicon_count)-1)

        print("p - values", pval)
        if pval < 0.05:  # alpha value is 0.05 or 5%
            result_lexi = "Result of Lexicon Base Analysis :  We are Rejecting Null Hypothesis"
        else:
            result_lexi = "Result of Lexicon Base Analysis :  We are Accepting Null Hypothesis"


        t = (np.mean(timings) - (-1))/np.std(timings)/len(timings)
        import scipy.stats
        pval = scipy.stats.t.sf(abs(t), df=len(timings)-1)

        print("p - values", pval)
        if pval < 0.05:  # alpha value is 0.05 or 5%
            result_time = "Result of Tweet Timing Analysis :  We are Rejecting Null Hypothesis"
        else:
            result_time = "Result of Tweet Timing Analysis :  We are Accepting Null Hypothesis"

        return ([html.H5(result_sentis), html.H5(result_lexi),html.H5(result_time)])


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