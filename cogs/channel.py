import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import datetime
import os
import asyncio
import time
from typing import Optional, Union


# --- DATABASE SETUP ---
class Database:
    def __init__(self, db_name="database/voice_data.db"):
        os.makedirs(os.path.dirname(db_name), exist_ok=True)
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("""
                         CREATE TABLE IF NOT EXISTS guild_sessions
                         (
                             guild_id
                             INTEGER
                             PRIMARY
                             KEY,
                             channel_id
                             INTEGER,
                             connected_at
                             REAL,
                             last_status
                             TEXT,
                             manual_leave_flag
                             INTEGER
                             DEFAULT
                             1
                         )
                         """)
            conn.commit()

    def update_session(self, guild_id, channel_id, status, manual_leave=0):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("""
                         INSERT INTO guild_sessions (guild_id, channel_id, connected_at, last_status, manual_leave_flag)
                         VALUES (?, ?, ?, ?, ?) ON CONFLICT(guild_id) DO
                         UPDATE SET
                             channel_id=excluded.channel_id,
                             connected_at=excluded.connected_at,
                             last_status=excluded.last_status,
                             manual_leave_flag=excluded.manual_leave_flag
                         """, (guild_id, channel_id, time.time(), status, manual_leave))

    def set_leave_flag(self, guild_id, flag):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("UPDATE guild_sessions SET manual_leave_flag = ? WHERE guild_id = ?", (flag, guild_id))

    def get_session(self, guild_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.execute("SELECT * FROM guild_sessions WHERE guild_id = ?", (guild_id,))
            return cursor.fetchone()


db = Database()


# --- COG IMPLEMENTATION ---
class VoiceControl(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def send_log(self, guild: discord.Guild, user: Union[discord.Member, discord.User, None], action: str,
                       channel_name: str, color: discord.Color = discord.Color.blue()):
        log_channel = discord.utils.get(guild.text_channels, name="bot-log")
        if not log_channel: return

        embed = discord.Embed(title="[VOICE LOG]", color=color, timestamp=discord.utils.utcnow())
        embed.add_field(name="User", value=user.mention if user else "System", inline=True)
        embed.add_field(name="Action", value=action, inline=True)
        embed.add_field(name="Channel", value=channel_name, inline=True)
        try:
            await log_channel.send(embed=embed)
        except:
            pass

    def get_uptime_string(self, start_timestamp: float) -> str:
        delta = datetime.timedelta(seconds=int(time.time() - start_timestamp))
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours} ชม. {minutes} นาที {seconds} วินาที"

    @app_commands.command(name="vc_channel", description="เชื่อมต่อบอทเข้าห้องเสียงและตั้งสถานะ")
    @app_commands.describe(channel="ห้องเสียงที่ต้องการให้เข้า", status="สถานะของบอท")
    @app_commands.choices(status=[
        app_commands.Choice(name="🟢 ออนไลน์", value="online"),
        app_commands.Choice(name="🌙 ไม่อยู่", value="idle"),
        app_commands.Choice(name="⛔ ห้ามรบกวน", value="dnd"),
        app_commands.Choice(name="⚫ ออฟไลน์", value="invisible"),
    ])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def vc_channel(self, interaction: discord.Interaction, channel: discord.VoiceChannel, status: str):
        await interaction.response.defer()

        guild = interaction.guild
        bot_member = guild.me
        voice_client = guild.voice_client

        perms = channel.permissions_for(bot_member)
        if not perms.connect or not perms.speak:
            embed = discord.Embed(title="❌ ข้อผิดพลาดด้านสิทธิ์",
                                  description=f"บอทไม่มีสิทธิ์ Connect หรือ Speak ใน {channel.mention}",
                                  color=discord.Color.red())
            return await interaction.followup.send(embed=embed)

        state_text = ""
        embed_color = discord.Color.green()

        try:
            if not voice_client:
                await channel.connect()
                state_text = "Connected"
                embed_color = discord.Color.green()
            elif voice_client.channel.id == channel.id:
                state_text = "Already Connected"
                embed_color = discord.Color.blue()
            else:
                await voice_client.move_to(channel)
                state_text = "Moved"
                embed_color = discord.Color.gold()

            status_obj = getattr(discord.Status, status, discord.Status.online)
            await self.bot.change_presence(status=status_obj, activity=None)
            db.update_session(guild.id, channel.id, status, manual_leave=0)

            session = db.get_session(guild.id)
            embed = discord.Embed(title="🎧 Voice System Control", color=embed_color)
            embed.add_field(name="📍 ห้องเสียง", value=channel.mention, inline=True)
            embed.add_field(name="🚦 สถานะบอท", value=status.capitalize(), inline=True)
            embed.add_field(name="⚡ Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
            embed.add_field(name="👥 สมาชิกในห้อง", value=str(len(channel.members) - 1), inline=True)
            embed.add_field(name="🕒 เวลาเริ่มเข้า", value=f"<t:{int(session[2])}:T>", inline=True)
            embed.add_field(name="⏳ Uptime", value=self.get_uptime_string(session[2]), inline=True)
            embed.add_field(name="🔗 Voice State", value=f"`{state_text}`", inline=False)
            embed.set_footer(text=f"System Monitoring Active | {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")

            await interaction.followup.send(embed=embed)
            await self.send_log(guild, interaction.user, state_text, channel.name, embed_color)

        except Exception as e:
            embed = discord.Embed(title="❌ เกิดข้อผิดพลาด", description=f"ไม่สามารถเชื่อมต่อได้: {str(e)}",
                                  color=discord.Color.red())
            await interaction.followup.send(embed=embed)
            await self.send_log(guild, interaction.user, "Error on Connect", channel.name, discord.Color.red())

    @app_commands.command(name="leave", description="ให้บอทออกจากห้องเสียง")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def leave(self, interaction: discord.Interaction):
        guild = interaction.guild
        voice_client = guild.voice_client

        if not voice_client:
            return await interaction.response.send_message("❌ บอทไม่ได้อยู่ในห้องเสียง", ephemeral=True)

        session = db.get_session(guild.id)
        channel_name = voice_client.channel.name

        uptime = self.get_uptime_string(session[2]) if session else "N/A"
        start_time = f"<t:{int(session[2])}:T>" if session else "N/A"
        end_time = f"<t:{int(time.time())}:T>"

        await voice_client.disconnect()
        db.set_leave_flag(guild.id, 1)
        await self.bot.change_presence(status=discord.Status.online, activity=None)

        embed = discord.Embed(title="👋 Voice Session Ended", color=discord.Color.red())
        embed.add_field(name="📍 ห้อง", value=channel_name, inline=True)
        embed.add_field(name="🕒 เข้าเมื่อ", value=start_time, inline=True)
        embed.add_field(name="🕒 ออกเมื่อ", value=end_time, inline=True)
        embed.add_field(name="⏳ รวมเวลา", value=uptime, inline=False)

        await interaction.response.send_message(embed=embed)
        await self.send_log(guild, interaction.user, "Left", channel_name, discord.Color.red())

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.id != self.bot.user.id: return

        if before.channel and not after.channel:
            session = db.get_session(member.guild.id)
            if session and session[4] == 0:
                guild = member.guild
                channel_id = session[1]
                channel = guild.get_channel(channel_id)

                if channel:
                    await self.send_log(guild, None, "Bot Kicked (Auto-reconnecting)", channel.name,
                                        discord.Color.orange())

                    retries = 3
                    for i in range(retries):
                        try:
                            await asyncio.sleep(5 * (i + 1))
                            await channel.connect()
                            await self.send_log(guild, None, "Auto-reconnect Successful", channel.name,
                                                discord.Color.green())
                            break
                        except Exception as e:
                            if i == retries - 1:
                                await self.send_log(guild, None, f"Auto-reconnect Failed: {str(e)}", channel.name,
                                                    discord.Color.red())

    @vc_channel.error
    @leave.error
    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(title="🚫 สิทธิ์ไม่เพียงพอ", description="คุณต้องมีสิทธิ์ `Manage Guild` เพื่อใช้งาน",
                                  color=discord.Color.red())
        else:
            embed = discord.Embed(title="⚠️ Error", description=str(error), color=discord.Color.red())

        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceControl(bot))