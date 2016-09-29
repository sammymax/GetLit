import os
import json
import urllib
from flask import Flask, url_for, request, redirect, session, render_template, flash
from flask_oauthlib.client import OAuth, OAuthException
import amazon.api
import socket
socket.setdefaulttimeout(5)

application = Flask(__name__)
application.secret_key = 'b7a1c997d34891f8f99401db8be762aa'
oauth = OAuth(application)

# needed permissions we need from Spotify API
spotifyScopes = ' '.join([
    'user-top-read'
])
spotify = oauth.remote_app(
    'spotify',
    consumer_key        = os.getenv('SPOTIFY_APP_ID'),
    consumer_secret     = os.getenv('SPOTIFY_APP_SECRET'),
    base_url            = 'https://api.spotify.com/v1/',
    request_token_params= {'scope' : spotifyScopes},
    request_token_url   = None,
    access_token_url    = 'https://accounts.spotify.com/api/token',
    authorize_url       = 'https://accounts.spotify.com/authorize',
    content_type        = 'application/json'
)

amazonObj = amazon.api.AmazonAPI(
        os.getenv('AMAZON_ACCESS_KEY'),
        os.getenv('AMAZON_SECRET_KEY'),
        os.getenv('AMAZON_ASSOC_TAG'))
amazon.api.MaxQPS = 0.9 # we need one query per artist; need this so we don't run over rate limit

@spotify.tokengetter
def getSpotifyToken():
    return session.get('oauth_token')

@application.route('/lit')
def index():
    args = {'in' : False, 'txt' : '', 'items' : []}
    if 'oauth_token' in session:
        args['in'] = True
        try:
            # get top 5 artists of user in Spotify
            req = urllib.request.Request('https://api.spotify.com/v1/me/top/artists?limit=5')
            req.add_header('Authorization', 'Bearer ' + session['oauth_token'])
            jsonResp = json.loads(urllib.request.urlopen(req).read().decode('utf8'))
            artists = [item['name'] for item in jsonResp['items']]
            args['txt'] = 'Showing swag for ' + ', '.join(artists)
        except urllib.error.HTTPError as e:
            args['txt'] = 'HTTP Error {}: {}'.format(e.code, e.read())
            render_template('index.html', **args)
        except json.JSONDecodeError as e:
            args['txt'] = 'Spotify API Json Error: ' + e.msg
            render_template('index.html', **args)

        i = 0
        for a in artists:
            # top artists have more of their products listed
            num = 5 - (i // 2)
            i += 1
            try:
                # Should try these out: ArtsAndCrafts, Books, Fashion, Collectibles
                prods = amazonObj.search_n(num, Keywords=a, SearchIndex='Collectibles')
            except amazon.api.SearchException:
                continue # found no results; just move on
            args['items'] += [(p.title, p.medium_image_url, p.offer_url) for p in prods]
    return render_template('index.html', **args)

@application.route('/lit/login')
def login():
    # _external=True so that we get full, not relative URL
    return spotify.authorize(callback = url_for('onAuth', _external = True))

@application.route('/lit/authorized')
@spotify.authorized_handler
def onAuth(resp):
    if resp is None or isinstance(resp, OAuthException):
        flash(u'Sign-in error.')
        nextUrl = request.args.get('next') or url_for('index')
        return redirect(nextUrl)
    session['oauth_token'] = resp['access_token']
    return redirect(url_for('index'))

if __name__ == '__main__':
    application.run(host='0.0.0.0')
