import disnake
from disnake.ext import commands
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta




ROLE_PERMISSION_CHECK = 1261599527568412713
LOGS_WARNING = 1261589162478276659





load_dotenv()

intents = disnake.Intents.all()
activity = disnake.Activity(
    name="Bajn Development",
    type=disnake.ActivityType.playing,
)

def has_access():
    async def predicate(interaction: disnake.ApplicationCommandInteraction):
        role_id = ROLE_PERMISSION_CHECK
        user_roles = [role.id for role in interaction.user.roles]
        return role_id in user_roles
    return commands.check(predicate)


def issue_warning(user_id, reason, issued_by, duration_days):
    warnings = load_warnings()
    expiration = datetime.now() + timedelta(days=duration_days)
    expiration_str = expiration.strftime("%Y-%m-%d %H:%M:%S")
    time_issued = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if str(user_id) not in warnings:
        warnings[str(user_id)] = []

    if warnings[str(user_id)]:
        new_id = max(warning["id"] for warning in warnings[str(user_id)]) + 1
    else:
        new_id = 1

    warnings[str(user_id)].append({
        "id": new_id,
        "reason": reason,
        "expires": expiration_str,
        "issued_by": issued_by,
        "time_issued": time_issued
    })
    
    save_warnings(warnings)

def load_warnings():
    try:
        with open("warnings.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_warnings(warnings):
    with open("warnings.json", "w") as file:
        json.dump(warnings, file, indent=2)

def check_warning(user_id):
    warnings = load_warnings()
    if str(user_id) in warnings:
        current_time = datetime.now()
        updated_warnings = []
        for warning in warnings[str(user_id)]:
            expiration = datetime.strptime(warning["expires"], "%Y-%m-%d %H:%M:%S")
            if current_time < expiration:
                updated_warnings.append(warning)
        
        if updated_warnings:
            warnings[str(user_id)] = updated_warnings
        else:
            del warnings[str(user_id)]
        
        save_warnings(warnings)
        return updated_warnings
    return []
def remove_warning(user_id, warning_id):
    warnings = load_warnings()
    if str(user_id) in warnings:
        updated_warnings = [warning for warning in warnings[str(user_id)] if warning["id"] != warning_id]
        if updated_warnings:
            warnings[str(user_id)] = updated_warnings
        else:
            del warnings[str(user_id)]
        save_warnings(warnings)
        return True
    return False




bot = commands.Bot(intents=intents, command_prefix="!", activity=activity)

@bot.slash_command(name="warn")
@has_access()
async def give_warn_command(interaction, user: disnake.Member, reason: str, days: float, proof: str):
    warning_channel = disnake.utils.get(interaction.guild.text_channels, id=LOGS_WARNING)
    
    expiration = datetime.now() + timedelta(days=days)
    expiration_str = expiration.strftime("%Y-%m-%d %H:%M:%S")

    embed = disnake.Embed(
        title=":warning: You just got a warning :warning:",
        description=f"\nReason: {reason}\nExpires: {expiration_str}\nProof: {proof}",
        color=0xff0000)
    logs_embed = disnake.Embed(
        title=f"{user.name} | New Warning.",
        description=f"\nUser: {user.mention}\nReason: {reason}\nExpires: {expiration_str}\nProof: {proof}",
        color=0x008000)
    logs_embed.set_footer(text=f"Issued by {interaction.user.name} | {interaction.user.id}")
    
    issue_warning(user.id, reason, interaction.user.id, days)
    await interaction.send(f"You warned the user {user.mention}\nReason: {reason}\nExpires: {expiration_str}", ephemeral=True)
    await user.send(embed=embed)
    await warning_channel.send(embed=logs_embed)

@bot.slash_command(name="checkwarn")
async def check_warn_command(interaction, user: disnake.Member):
    warnings = check_warning(user.id)
    if warnings:
        response = f"{user.mention} has the following active warnings:\n"
        for warning in warnings:
            response += (f"\n``Warning ID: {warning['id']}``\n"
                         f"- **Reason: {warning['reason']}**\n"
                         f"- **Issued by: <@{warning['issued_by']}>**\n"
                         f"- **Time issued: {warning['time_issued']}**\n"
                         f"- **Expires: {warning['expires']}**\n\n")
    else:
        response = f"{user.mention} has no active warnings."
    await interaction.send(response, ephemeral=True)
@bot.slash_command(name="removewarn")
@has_access()
async def remove_warn_command(interaction, user: disnake.Member, warning_id: int):
    success = remove_warning(user.id, warning_id)
    if success:
        await interaction.send(f"Warning ID {warning_id} for user {user.mention} has been removed.", ephemeral=True)
    else:
        await interaction.send(f"Warning ID {warning_id} for user {user.mention} was not found or could not be removed.",  ephemeral=True)
@bot.event
async def on_slash_command_error(interaction: disnake.ApplicationCommandInteraction, error):
    if isinstance(error, commands.CheckFailure):
        await interaction.send("Permission Check Error", ephemeral=True)
    else:
        await interaction.send(f"An error occured: {str(error)}", ephemeral=True)
bot.run(os.getenv("TOKEN"))
