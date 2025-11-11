# ---- KEEP ALIVE FOR RENDER ----
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()
# ---- END KEEP ALIVE ----

import discord
from discord.ext import commands, tasks
import random
import asyncio
import logging
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

CHANNEL_ID = {
    1369783760727576677: 1392662112559435940,
    1066790649002737664: 1392678220683284530,
}
HIDDEN_CHANNEL_ID = {
    1369783760727576677: 1392916865159794728,
    1066790649002737664: 1393368239274463322,
}

BOT_USER_ID = 716390085896962058

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ───────────── STATE ─────────────
active = {sid: False for sid in HIDDEN_CHANNEL_ID}
paused = {sid: False for sid in HIDDEN_CHANNEL_ID}
server_tasks = {}

# ───────────── PER-SERVER SPAWNER ─────────────

async def pokemon_spawning(server_id: int):
    """Independent spawning loop per server."""
    await bot.wait_until_ready()
    channel_id = HIDDEN_CHANNEL_ID[server_id]
    interval = 0.9

    try:
        channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
    except Exception as e:
        print(f"[{server_id}] ❌ Cannot find hidden channel: {e}")
        return
    
    print(f"[{server_id}] ✅ Pokemon are spawning in {channel}")

    await asyncio.sleep(random.uniform(0, 0.5))

    next_time = asyncio.get_event_loop().time()

    while active.get(server_id, False):
        if not paused.get(server_id, False):
            try:
                letter = chr(random.randint(97, 122))
                await channel.send(letter)
            except Exception as e:
                print(f"[{server_id}] ⚠️ Send Error: {e}")
                await asyncio.sleep(1)

        next_time += interval
        delay = max(0, next_time - asyncio.get_event_loop().time())
        await asyncio.sleep(delay)
    
    print(f"[{server_id}] 🛑 Spawning stopped")

    
# ───────────── COMMANDS ─────────────

@bot.command()
async def start(ctx):
    server_id = ctx.guild.id
    if active.get(server_id, False):
        await ctx.send("⚠️ Already Spawning")
        return
    
    active[server_id] = True
    paused[server_id] = False

    task = asyncio.create_task(pokemon_spawning(server_id))
    server_tasks[server_id] = task

    await ctx.send(f"✅ Pokemon spawning started in ({server_id}).")

@bot.command()
async def stop(ctx):
    server_id = ctx.guild.id
    active[server_id] = False
    paused[server_id] = False
    
    task = server_tasks.pop(server_id, None)
    if task:
        task.cancel()
    await ctx.send(f"🛑 Pokemon spawning stopped in ({server_id}).")

    
# ───────────── EVENT HANDLING ─────────────

@bot.event
async def on_message(message):
    if message.author.id == bot.user.id:
        return
    
    server_id = getattr(message.guild, "id", None)
    if (
        server_id in CHANNEL_ID
        and message.channel.id == CHANNEL_ID[server_id]
        and message.author.id == BOT_USER_ID
    ):
        paused[server_id] = True
        print(f"[{server_id}] ⏸️ Paused, Pokemon Spawned")
        await asyncio.sleep(10)
        paused[server_id] = False
        print(f"[{server_id}] ▶️ Spawning Resumed!")

    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"✅ Ready to spawn as {bot.user}")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
