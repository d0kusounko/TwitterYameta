#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import tweepy
import webbrowser
import urllib
import json
import datetime
import time

CONSUMER_KEY = os.environ['CONSUMER_KEY']         # API Key
CONSUMER_SECRET = os.environ['CONSUMER_SECRET']   # API Secret


def get_oauth_token(url: str) -> str:
    querys = urllib.parse.urlparse(url).query
    querys_dict = urllib.parse.parse_qs(querys)
    return querys_dict["oauth_token"][0]


if __name__ == '__main__':
    args = sys.argv

    # args[1] : Mode l:Login, r:Run tweet delete
    if args[1] == 'l':
        # Login.
        #
        # This code quotes below
        # https://gist.github.com/sleepless-se/8784328322311a5e86cfa0e2ae91addd
        # Licensed by sleepless-se

        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)

        try:
            redirect_url = auth.get_authorization_url()
            print("Redirect URL:", redirect_url)
        except tweepy.TweepError:
            print("Error! Failed to get request token.")

        oauth_token = get_oauth_token(redirect_url)
        print("oauth_token:", oauth_token)
        auth.request_token['oauth_token'] = oauth_token

        # Please confirm at twitter after login.
        webbrowser.open(redirect_url)

        verifier = input("You can check Verifier on url parameter. Please input Verifier:")
        auth.request_token['oauth_token_secret'] = verifier

        try:
            auth.get_access_token(verifier)
        except tweepy.TweepError:
            print('Error! Failed to get access token.')

        print("access token key:", auth.access_token)
        print("access token secret:", auth.access_token_secret)

        with open("auth_info.text", mode="w") as file:
            text = "key:{}\nsecret:{}".format(auth.access_token, auth.access_token_secret)
            file.write(text)

        print("DONE")

    elif args[1] == 'r':
        # Tweet delete.
        #
        # args[2] : Access token
        # args[3] : Access token secret
        # args[4] : JSON file(tweet.js) path
        # args[5] : Since date : YYYYMMDDHHMMSS
        # args[6] : Until date : YYYYMMDDHHMMSS

        # Twitter Login.
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(args[2], args[3])
        api = tweepy.API(auth)

        # Create timezone.
        local_tz = datetime.timezone(datetime.timedelta(hours=9))  # JST

        # Get args date.
        date_since = datetime.datetime.strptime(args[5], '%Y%m%d%H%M%S').replace(tzinfo=local_tz)
        date_until = datetime.datetime.strptime(args[6], '%Y%m%d%H%M%S').replace(tzinfo=local_tz)
        print('Since date : ' + str(date_since))
        print('Until date : ' + str(date_until))

        # JSON parse.
        json_parse = None
        with open(args[4], 'r', encoding='utf-8') as json_file:

            # Delete text 'window.YTD.tweet.part0 = '
            json_text = json_file.read()
            json_text = json_text.replace('window.YTD.tweet.part0 = ', '')

            # Text to dictionary
            json_parse = json.loads(json_text)

        if json_parse:
            for tweet in json_parse:
                tweet_id    = tweet.get('tweet', {}).get('id')
                created_at  = tweet.get('tweet', {}).get('created_at')

                # Delete tweet.
                if (tweet_id is not None) and (created_at is not None):
                    # print(tweet_id + ' : ' + created_at)

                    # Convert tweet date timezone.
                    tweet_dt = datetime.datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')
                    tweet_dt = tweet_dt.astimezone(local_tz)

                    print('Tweet: [id]' + str(tweet_id) + ' [date]' + str(tweet_dt))

                    if date_since <= tweet_dt <= date_until:
                        while True:
                            try:
                                api.get_status(tweet_id)
                                api.destroy_status(tweet_id)    # Delete
                                print("-> Delete.")
                            except tweepy.RateLimitError:
                                print("Twitter's API rate limit. Wait 10 minutes.")
                                time.sleep(60 * 10)
                            except tweepy.TweepError as e:
                                if e.response is None:
                                    # Retry.
                                    print(e.reason)
                                if e.api_code == 144:
                                    print("No status found with that ID.")
                                    break
                                elif e.api_code == 179:
                                    print("Sorry, you are not authorized to see this status.")
                                    break
                                elif e.api_code == 136:
                                    print("You have been blocked from the author of this tweet.")
                                    break
                                elif e.api_code == 63:
                                    print("User has been suspended.")
                                    break
                                else:
                                    raise
                            else:
                                break

    else:
        print("Undefined Mode.")
