import discord
from discord.ext import commands, tasks
import os
import sys
import asyncio
from datetime import datetime, timezone
from typing import List

TOKEN = os.getenv("DISCORD_TOKEN")
TOKEN_2 = os.getenv("DISCORD_TOKEN_2")
PREFIX = "!"
OWNER_ID = 427563032080547840

if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is required")


def create_intents() -> discord.Intents:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.guilds = True
    intents.presences = False
    return intents


def get_time_based_status() -> discord.Status:
    hour = datetime.now().hour
    if 6 <= hour < 12:
        return discord.Status.online
    elif 12 <= hour < 19:
        return discord.Status.idle
    else:
        return discord.Status.dnd


class BotBase(commands.Bot):
    def __init__(self, prefix: str, cogs: List[str], bot_name: str):
        super().__init__(
            command_prefix=prefix,
            intents=create_intents(),
            help_command=None,
            owner_id=OWNER_ID if prefix == PREFIX else None,
            case_insensitive=True
        )
        self.cogs_to_load = cogs
        self.bot_name = bot_name
        self.start_time = datetime.now(timezone.utc)

    async def setup_hook(self):
        await self._load_cogs()

    async def _load_cogs(self):
        print(f"📦 [{self.bot_name}] กำลังโหลด Cogs...")
        loaded = 0
        failed = 0

        for cog in self.cogs_to_load:
            try:
                await self.load_extension(cog)
                print(f"  ✅ [{self.bot_name}] โหลด {cog} สำเร็จ")
                loaded += 1
            except Exception as e:
                print(f"  ❌ [{self.bot_name}] โหลด {cog} ล้มเหลว: {e}")
                failed += 1

        print(f"📊 [{self.bot_name}] สรุป: {loaded}/{len(self.cogs_to_load)} Cogs")
        if failed > 0:
            print(f"⚠️  [{self.bot_name}] ล้มเหลว {failed} Cogs")


class MainBot(BotBase):
    def __init__(self):
        super().__init__(
            prefix=PREFIX,
            cogs=[
                "verify",
                "admin",
                "dm_syaem",
                "hely",
                "userinfo",
                "bot_inspect",
                "shop",
                "vc"
            ],
            bot_name="BOT1"
        )
        self.status_index = 0
        self.status_activities = [
            ("📖 /help - วิธีใช้คำสั่งทั้งหมด", discord.ActivityType.playing),
            ("</> พัฒนาเพื่อการศึกษา", discord.ActivityType.watching),
            ("🎶 Boulevard of Broken Dreams", discord.ActivityType.listening),
            ("✅ ระบบยืนยันตัวตนอัตโนมัติ", discord.ActivityType.watching),
            ("☢️ ดูแลโดยทีมงาน 24/7", discord.ActivityType.watching)
        ]


class SecondaryBot(BotBase):
    def __init__(self):
        super().__init__(
            prefix=">>",
            cogs=["channel"],
            bot_name="BOT2"
        )
        self.status_index = 0
        self.status_activities = [
            ("🌐 Monitoring Channels", discord.ActivityType.watching),
            ("📡 Auto Management System", discord.ActivityType.watching),
            ("⚙️ Channel Operations", discord.ActivityType.watching),
            ("🔧 System Active", discord.ActivityType.watching),
            ("💼 Background Worker", discord.ActivityType.watching)
        ]


bot = MainBot()
bot2 = SecondaryBot()


@bot.event
async def on_ready():
    print("\n" + "=" * 50)
    print(f"🤖 [BOT1] บอทออนไลน์แล้ว!")
    print(f"👤 ชื่อ: {bot.user}")
    print(f"🆔 ID: {bot.user.id}")
    print(f"⏰ เริ่มต้นเมื่อ: {bot.start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 50 + "\n")

    try:
        synced = await bot.tree.sync()
        print(f"✅ [BOT1] ซิงค์ Slash Commands สำเร็จ ({len(synced)} คำสั่ง)")
    except Exception as e:
        print(f"❌ [BOT1] ซิงค์ Slash Commands ล้มเหลว: {e}")

    if not change_status.is_running():
        change_status.start()
        print(f"✅ [BOT1] เริ่ม Status Rotation")
        print(f"⏰ [BOT1] Time-Based Status: {get_time_based_status()}\n")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("❌ บอทไม่มีสิทธิ์ดำเนินการนี้")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ ขาดพารามิเตอร์: `{error.param.name}`")
    else:
        print(f"❌ [BOT1] Command Error: {type(error).__name__}: {error}")


@bot.event
async def on_error(event, *_args, **_kwargs):
    print(f"❌ [BOT1] Error in {event}:")
    import traceback
    traceback.print_exc()


@bot2.event
async def on_ready():
    print("\n" + "=" * 50)
    print(f"🤖 [BOT2] บอทออนไลน์แล้ว!")
    print(f"👤 ชื่อ: {bot2.user}")
    print(f"🆔 ID: {bot2.user.id}")
    print(f"⏰ เริ่มต้นเมื่อ: {bot2.start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 50 + "\n")

    try:
        synced = await bot2.tree.sync()
        print(f"✅ [BOT2] ซิงค์ Slash Commands สำเร็จ ({len(synced)} คำสั่ง)")
    except Exception as e:
        print(f"❌ [BOT2] ซิงค์ Slash Commands ล้มเหลว: {e}")

    if not change_status_bot2.is_running():
        change_status_bot2.start()
        print(f"✅ [BOT2] เริ่ม Status Rotation")
        print(f"⏰ [BOT2] Time-Based Status: {get_time_based_status()}\n")


@bot2.event
async def on_error(event, *_args, **_kwargs):
    print(f"❌ [BOT2] Error in {event}:")
    import traceback
    traceback.print_exc()


@tasks.loop(seconds=10)
async def change_status():
    text, activity_type = bot.status_activities[bot.status_index]
    await bot.change_presence(
        activity=discord.Activity(type=activity_type, name=text),
        status=get_time_based_status()
    )
    bot.status_index = (bot.status_index + 1) % len(bot.status_activities)


@change_status.before_loop
async def before_change_status():
    await bot.wait_until_ready()


@tasks.loop(seconds=10)
async def change_status_bot2():
    text, activity_type = bot2.status_activities[bot2.status_index]
    await bot2.change_presence(
        activity=discord.Activity(type=activity_type, name=text),
        status=get_time_based_status()
    )
    bot2.status_index = (bot2.status_index + 1) % len(bot2.status_activities)


@change_status_bot2.before_loop
async def before_change_status_bot2():
    await bot2.wait_until_ready()


@bot.command(name="reload", hidden=True)
@commands.is_owner()
async def reload_cog(ctx, cog_name: str):
    try:
        await bot.reload_extension(f"cogs.{cog_name}")
        await ctx.send(f"✅ โหลด `{cog_name}` ใหม่สำเร็จ")
    except Exception as e:
        await ctx.send(f"❌ โหลด `{cog_name}` ล้มเหลว: {e}")


@bot.command(name="load", hidden=True)
@commands.is_owner()
async def load_cog(ctx, cog_name: str):
    try:
        await bot.load_extension(f"cogs.{cog_name}")
        await ctx.send(f"✅ โหลด `{cog_name}` สำเร็จ")
    except Exception as e:
        await ctx.send(f"❌ โหลด `{cog_name}` ล้มเหลว: {e}")


@bot.command(name="unload", hidden=True)
@commands.is_owner()
async def unload_cog(ctx, cog_name: str):
    try:
        await bot.unload_extension(f"cogs.{cog_name}")
        await ctx.send(f"✅ ยกเลิกโหลด `{cog_name}` สำเร็จ")
    except Exception as e:
        await ctx.send(f"❌ ยกเลิกโหลด `{cog_name}` ล้มเหลว: {e}")


@bot.command(name="sync", hidden=True)
@commands.is_owner()
async def sync_commands(ctx):
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"✅ ซิงค์สำเร็จ ({len(synced)} คำสั่ง)")
    except Exception as e:
        await ctx.send(f"❌ ซิงค์ล้มเหลว: {e}")


@bot.command(name="shutdown", aliases=["stop"], hidden=True)
@commands.is_owner()
async def shutdown(ctx):
    await ctx.send("👋 กำลังปิดบอททั้งสอง...")
    await bot.close()
    if TOKEN_2:
        await bot2.close()


@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"**Latency:** `{latency}ms`",
        color=discord.Color.green() if latency < 100 else discord.Color.orange()
    )
    await ctx.send(embed=embed)


@bot.command(name="stats", aliases=["info", "botinfo"])
async def stats(ctx):
    uptime = datetime.now(timezone.utc) - bot.start_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    embed = discord.Embed(
        title=f"📊 สถิติของ {bot.user.name}",
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc)
    )

    embed.add_field(
        name="📈 สถิติ",
        value=f"**Ping:** {round(bot.latency * 1000)}ms",
        inline=True
    )

    embed.add_field(
        name="⏰ Uptime",
        value=f"{hours}ชม. {minutes}นาที {seconds}วินาที",
        inline=True
    )

    embed.add_field(
        name="💻 ข้อมูลเทคนิค",
        value=(
            f"**Discord.py:** {discord.__version__}\n"
            f"**Python:** {sys.version.split()[0]}\n"
            f"**Cogs:** {len(bot.cogs)}"
        ),
        inline=False
    )

    current_time = datetime.now().strftime("%H:%M")
    embed.add_field(
        name="🕒 สถานะปัจจุบัน",
        value=f"**เวลา:** {current_time}\n**Status:** {get_time_based_status()}",
        inline=False
    )

    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_footer(text=f"ขอโดย {ctx.author}", icon_url=ctx.author.display_avatar.url)

    await ctx.send(embed=embed)


async def run_bots():
    async def start_bot1():
        try:
            await bot.start(TOKEN)
        except discord.LoginFailure:
            print("\n❌ [BOT1] TOKEN ไม่ถูกต้อง!")
        except Exception as error:
            print(f"\n❌ [BOT1] เกิดข้อผิดพลาด: {error}")
            import traceback
            traceback.print_exc()

    async def start_bot2():
        if not TOKEN_2:
            print("\n⚠️  [BOT2] ไม่พบ DISCORD_TOKEN_2 - ข้าม Bot 2")
            return

        try:
            await bot2.start(TOKEN_2)
        except discord.LoginFailure:
            print("\n❌ [BOT2] TOKEN ไม่ถูกต้อง!")
        except Exception as error:
            print(f"\n❌ [BOT2] เกิดข้อผิดพลาด: {error}")
            import traceback
            traceback.print_exc()

    await asyncio.gather(start_bot1(), start_bot2())


if __name__ == "__main__":
    try:
        print("🚀 กำลังเริ่มบอททั้งสอง...\n")
        asyncio.run(run_bots())
    except KeyboardInterrupt:
        print("\n👋 ปิดบอททั้งสองโดยผู้ใช้")
    except Exception as error:
        print(f"\n❌ เกิดข้อผิดพลาด: {error}")
        import traceback

        traceback.print_exc()