import discord
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import spotipy.oauth2 as oauth2
import json

with open('config.json', 'r') as f:
    config = json.load(f)

# TODO maybe add
username = config['username']

# Read the file and add Bearer in front of the access token automatically
try:
    # read input file
    fin = open(".cache-Xyrai", "r")
    # read file contents to string
    data = fin.read()
    # replace all occurrences of the required string
    if data.startswith("{\"access_token\": \"Bearer "):
        pass
    else:
        data = data.replace("{\"access_token\": \"", "{\"access_token\": \"Bearer ")
        # close the input file
        fin.close()
        # open the input file in write mode
        fin = open(".cache-Xyrai", "w")
        # override the input file with the resulting data
        fin.write(data)
        # close the file
        fin.close()
except:
    pass

scope = 'streaming app-remote-control user-read-private ugc-image-upload user-read-playback-state ' \
        'user-modify-playback-state user-read-currently-playing user-read-private playlist-read-collaborative ' \
        'playlist-modify-public playlist-read-private playlist-modify-private user-library-modify user-library-read ' \
        'user-top-read user-read-playback-position user-read-recently-played user-follow-read user-follow-modify'

auth_manager = oauth2.SpotifyOAuth(scope=scope, username=username)
token = auth_manager.get_access_token()
spotify = spotipy.Spotify(auth=token)

# TODO
# link steam acc
# play track
# go back to previous track
# play playlist
# lookup history of played songs
# repeat
# volume
# voice to text command

# Refresh the auth token if it is expired
def refresh_token():
    cached_token = auth_manager.get_cached_token()
    refreshed_token = cached_token['refresh_token']
    new_token = auth_manager.refresh_access_token(refreshed_token)
    spotipy.Spotify(auth=new_token['access_token'])
    return new_token


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='info')
    async def info(self, ctx):
        user_details = spotify.me()

        embed = discord.Embed(title='Spotify details', description=user_details['display_name'])

        await ctx.send(embed=embed)

    @commands.command(name='next', alias='skip')
    async def next(self, ctx):

        # Under the hood implementation
        # headers = {
        #     'Accept': 'application/json',
        #     'Content-Type': 'application/json',
        #     'Authorization': 'config['auth_token]',
        # }
        #
        # params = (('device_id', config['spotify_device_id']),)
        #
        # requests.post('https://api.spotify.com/v1/me/player/next', headers=headers, params=params)

        # Easy library implementation
        spotify.next_track(config['spotify_device_id'])

        # TODO: if done get currently playing track and send it to discord can be done with spotify var

        await ctx.send('skipped song')

    @commands.command(name='previous', alias='return')
    async def previous(self, ctx):
        try:
            spotify.previous_track(config['spotify_device_id'])
        except:
            pass
            await ctx.send('There is no previous song')

        await ctx.send('previous song')

    @commands.command(name='play')
    async def play(self, ctx, song_uri):
        # Valid contexts are albums, artists, playlists
        song_array = [song_uri]

        try:
            spotify.start_playback(config['spotify_device_id'], uris=song_array)

        except:
            refresh_token()
            spotify.start_playback(config['spotify_device_id'], uris=song_uri)

        await ctx.send("Started playing your track")

    @commands.command(name='add')
    async def add(self, ctx, song_uri):
        try:
            spotify.add_to_queue(song_uri, config['spotify_device_id'])

        except:
            refresh_token()
            spotify.add_to_queue(song_uri, config['spotify_device_id'])

        await ctx.send("Added your song to the queue!")

    @commands.command(name='current')
    async def current(self, ctx):
        try:
            current_song_info = spotify.currently_playing()

        except:
            refresh_token()
            current_song_info = spotify.currently_playing()

        current_song_name = current_song_info['item']['name']
        await ctx.send(f'Now playing: {current_song_name}')


def setup(bot):
    bot.add_cog(General(bot))
