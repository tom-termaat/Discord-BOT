from discord.ext import commands
import discord
import random
import asyncio
import requests

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(
    command_prefix="!",  # Change to desired prefix
    case_insensitive=True,  # Commands aren't case-sensitive
    intents=intents  # Set up basic permissions
)

bot.author_id = 232182490339606529  # Change to your discord id

# List of funny catchphrases
catchphrases = [
    "Because I said so!",
    "For excessive use of emojis 🙄",
    "You've been hit by the banhammer! ⚒️",
    "Reason? Banned for fun! 😄",
]

# Store a list of users who have received warnings
warning_list = {}

# Store a flag to track flood monitoring state
flood_monitoring = False

# Create a variable to hold the task reference
reset_task = None


@bot.event
async def on_ready():  # When the bot is ready
    print("I'm in")
    print(bot.user)  # Prints the bot's username and identifier


@bot.command()
async def pong(ctx):
    await ctx.send('pong')


@bot.command()
async def name(ctx):
    # Get the user's name
    user_name = ctx.author.name

    await ctx.send(user_name)


@bot.command()
async def d6(ctx):
    # Generate a random number between 1 and 6
    random_value = random.randint(1, 6)

    # Send the random value as a message
    await ctx.send(random_value)


@bot.event
async def on_message(message):
    global flood_monitoring
    global warning_list
    global reset_task

    if message.content.lower() == "salut tout le monde":
        # Send the response
        response = f"Salut tout seul, {message.author.mention}!"
        await message.channel.send(response)

    if message.content.lower() == "deactivate flood":
        # If flood monitoring is active, deactivate it
        flood_monitoring = False
        reset_task.cancel()
        warning_list.clear()
        await message.channel.send("Flood monitoring has been deactivated.")

    if flood_monitoring:
        await monitor_flood(message)

    await bot.process_commands(message)


@bot.command()
async def admin(ctx, member: discord.Member):
    # Check if the Admin role already exists, and if not, create it with specific permissions
    admin_permissions = discord.Permissions(manage_channels=True, kick_members=True, ban_members=True)
    admin_role = discord.utils.get(ctx.guild.roles, name="Admin")

    if admin_role is None:
        admin_role = await ctx.guild.create_role(name="Admin", permissions=admin_permissions)

    # Assign the Admin role to the specified member
    await member.add_roles(admin_role)

    # Send a confirmation message
    await ctx.send(f'{member.mention} is now an Admin with manage, kick, and ban permissions!')


@bot.command()
async def ban(ctx, member: discord.Member, *, reason=None):
    # Check if a reason was provided
    if reason is None:
        # If no reason is provided, choose a random catchphrase
        ban_reason = random.choice(catchphrases)
    else:
        # If a reason is provided, use it
        ban_reason = f"Ban reason: {reason}"

    # Attempt to ban the member and provide the reason
    try:
        await member.ban(reason=ban_reason)
        await ctx.send(f'{member.mention} has been banned. {ban_reason}')
    except discord.Forbidden:
        await ctx.send("I don't have permission to ban members.")


@bot.command()
async def flood(ctx):
    global flood_monitoring
    if flood_monitoring:
        # If flood monitoring is active, ask for confirmation to deactivate
        await ctx.send("Flood monitoring is currently active. Type 'deactivate flood' to deactivate.")
    else:
        # If flood monitoring is not active, activate it
        global reset_task
        flood_monitoring = True
        reset_task = bot.loop.create_task(reset_warning_list())
        await ctx.send("Flood monitoring has been activated.")


async def monitor_flood(message):
    user = message.author

    if user.id != bot.user.id:
        if user not in warning_list:
            warning_list[user] = 1
        else:
            warning_list[user] += 1

        if user in warning_list:
            print(f'{user}: {warning_list[user]}')

        if user in warning_list and warning_list[user] > 10:  # X = 10 messages
            await message.channel.send(f"{user.mention}, please refrain from flooding the chat.")


async def reset_warning_list():
    while True:
        await asyncio.sleep(60)  # Reset the warning_list every 1 minute
        warning_list.clear()  # Clear the warning_list

@bot.command()
async def xkcd(ctx):
    try:
        # Fetch XKCD JSON data
        response = requests.get("https://xkcd.com/info.0.json")
        if response.status_code == 200:
            xkcd_data = response.json()
            comic_number = random.randint(1, xkcd_data["num"])  # Get a random comic number

            # Fetch the random XKCD comic
            comic_response = requests.get(f"https://xkcd.com/{comic_number}/info.0.json")
            if comic_response.status_code == 200:
                comic_data = comic_response.json()
                comic_url = comic_data["img"]
                await ctx.send(comic_url)  # Send the comic URL
            else:
                await ctx.send("Failed to fetch XKCD comic.")
        else:
            await ctx.send("Failed to fetch XKCD data.")
    except Exception as e:
        print(e)
        await ctx.send("An error occurred while fetching the XKCD comic.")

@bot.command()
async def poll(ctx, question):
    # Mention @here and post the poll question
    poll_message = await ctx.send(f"@here {question}")

    # Add reactions to the poll message
    await poll_message.add_reaction("👍")  # Thumbs-up
    await poll_message.add_reaction("👎")  # Thumbs-down


# Schedule the reset_warning_list function using the event loop
if __name__ == '__main__':
    token = "<BOT TOKEN>"
    bot.run(token)  # Starts the bot
