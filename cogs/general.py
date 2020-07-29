import discord
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import spotipy.oauth2 as oauth2
import json
from datetime import datetime


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
except FileNotFoundError:
    pass

scope = 'streaming app-remote-control user-read-private ugc-image-upload user-read-playback-state ' \
        'user-modify-playback-state user-read-currently-playing user-read-private playlist-read-collaborative ' \
        'playlist-modify-public playlist-read-private playlist-modify-private user-library-modify user-library-read ' \
        'user-top-read user-read-playback-position user-read-recently-played user-follow-read user-follow-modify'

auth_manager = oauth2.SpotifyOAuth(scope=scope, username=username)
token = auth_manager.get_access_token()
# TODO
# link steam acc
# play track
# go back to previous track
# play playlist
# lookup history of played songs
# repeat
# volume
# voice to text command


def create_song_embed(current_song_info):
    song_name = current_song_info['item']['name']
    song_image = current_song_info['item']['album']['images'][0]['url']
    song_link = current_song_info['item']['album']['external_urls']['spotify']
    song_artists = current_song_info['item']['artists']
    song_album = current_song_info['item']['album']['name']
    song_release_date = datetime.strptime(current_song_info['item']['album']['release_date'], '%Y-%m-%d')

    artists = []

    for artist in song_artists:
        artists.append(f'[{artist["name"]}]({artist["external_urls"]["spotify"]})')

    embed = discord.Embed(title=song_name,
                          url=song_link,
                          description=f'by {", ".join(artists)}', color=0x1eb660)
    embed.set_thumbnail(url=song_image)
    embed.add_field(name='Album', value=song_album, inline=False)
    embed.add_field(name='Release Date', value=song_release_date.strftime('%d %B %Y'), inline=False)

    return embed


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spotify = spotipy.Spotify(auth=token)

    # Refresh the auth token if it is expired
    def refresh_token(self):
        cached_token = auth_manager.get_cached_token()
        refreshed_token = cached_token['refresh_token']
        new_token = auth_manager.refresh_access_token(refreshed_token)
        self.spotify = spotipy.Spotify(auth=new_token['access_token'])
        return new_token

    @commands.command(name='info', aliases=['i'])
    async def info(self, ctx):
        try:
            user_details = self.spotify.me()
            embed = discord.Embed(title='Spotify details', description=user_details['display_name'])
        except spotipy.client.SpotifyException:
            self.refresh_token()
            return await self.info(ctx)

        await ctx.send(embed=embed)

    @commands.command(name='skip', aliases=['next', 's'])
    async def skip(self, ctx):

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
        try:
            self.spotify.next_track(config['spotify_device_id'])
        except spotipy.client.SpotifyException:
            self.refresh_token()
            return await self.skip(ctx)

        # TODO: if done get currently playing track and send it to discord can be done with spotify var

        await ctx.send('skipped song')

    @commands.command(name='previous', aliases=['return', 'back', 'b'])
    async def previous(self, ctx):
        try:
            self.spotify.previous_track(config['spotify_device_id'])
        except spotipy.client.SpotifyException:
            self.refresh_token()
            return await self.previous(ctx)

        # previous_track() does not return any data, so recall the currently playing track function
        song_details = self.spotify.currently_playing()

        await ctx.send(embed=create_song_embed(song_details))

    # Play or resume a track
    @commands.command(name='play', aliases=['p'])
    async def play(self, ctx, song_uri=None):
        if song_uri is None:
            try:
                self.spotify.start_playback(config['spotify_device_id'])
                return await ctx.send('Resuming track')
            except spotipy.client.SpotifyException:
                return

        # Valid contexts are albums, artists, playlists
        song_array = [song_uri]

        try:
            self.spotify.start_playback(config['spotify_device_id'], uris=song_array)
        except spotipy.client.SpotifyException:
            self.refresh_token()
            return await self.play(ctx, song_uri)

        await ctx.send("Started playing your track")

    @commands.command(name='add', aliases=['a'])
    async def add(self, ctx, song_uri):
        try:
            self.spotify.add_to_queue(song_uri, config['spotify_device_id'])
        except spotipy.client.SpotifyException:
            self.refresh_token()
            return await self.add(ctx, song_uri)

        await ctx.send("Added your song to the queue!")

    @commands.command(name='current', aliases=['c'])
    async def current(self, ctx):
        try:
            current_song_info = self.spotify.currently_playing()

            # Check if there is no song playing
            if current_song_info is None:
                return await ctx.send('Could not find the current song/a song is not playing, try again.')
        except spotipy.client.SpotifyException:
            self.refresh_token()
            return await self.current(ctx)

        await ctx.send(embed=create_song_embed(current_song_info))

    @commands.command(name='volume', aliases=['v'])
    async def volume(self, ctx, v_level: int):
        try:
            self.spotify.volume(v_level, config['spotify_device_id'])
        except spotipy.client.SpotifyException:
            self.refresh_token()
            return await self.volume(ctx, v_level)

        await ctx.send(f'Turned volume to: {v_level}')

    @commands.command(name='pause', aliases=['pa'])
    async def pause(self, ctx):
        try:
            self.spotify.pause_playback(config['spotify_device_id'])
        except spotipy.client.SpotifyException:
            self.refresh_token()
            return await self.pause(ctx)

        await ctx.send(f'Paused song')

    @commands.command(name='repeat', aliases=['loop', 'r'])
    async def repeat(self, ctx, state=None):
        # Required
        # track, context or off.
        # track will repeat the current track.
        # context will repeat the current context.
        # off will turn repeat off.
        valid_states = ('track', 'context', 'off')

        if state not in valid_states:
            return await ctx.send('Not a valid repeat state.\nValid choices: `track`, `context`, `off`')

        try:
            self.spotify.repeat(state, config['spotify_device_id'])
        except spotipy.client.SpotifyException:
            self.refresh_token()
            return await self.repeat(ctx, state)

        await ctx.send(f'Repeating song')

    @commands.command(name='history', aliases=['h'])
    async def history(self, ctx, amount=3):
        try:
            song_history = self.spotify.current_user_recently_played(limit=amount)
        except spotipy.client.SpotifyException:
            self.refresh_token()
            return await self.history(ctx, amount)

        prev_song_list = []
        for track in song_history['items']:
            prev_song_list.append(track['track']['name'])

        await ctx.send('History:\n' + '\n'.join(prev_song_list))


def setup(bot):
    bot.add_cog(General(bot))
