import discord
from discord.ext import commands, tasks
import os
import sys
import asyncio
from datetime import datetime, timezone

# =========================
# CONFIGURATION - BOT 1
# =========================
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "!"
OWNER_ID = 427563032080547840  # ใส่ไอดีของคุณ

# =========================
# CONFIGURATION - BOT 2
# =========================
TOKEN_2 = os.getenv("DISCORD_TOKEN_2")

# =========================
# INTENTS
# =========================
intents = discord.Intents.default()
intents.message_content = True  # สำหรับ prefix commands
intents.members = True  # สำหรับดูสมาชิก (สำคัญสำหรับ add_role)
intents.guilds = True  # สำหรับดูเซิร์ฟเวอร์
intents.presences = False  # ไม่จำเป็นต้องดู presence


# =========================
# TIME-BASED STATUS HELPER
# =========================
def get_time_based_status() -> discord.Status:
    """
    คำนวณสถานะบอทตามเวลาปัจจุบัน

    Returns:
        discord.Status: สถานะที่เหมาะสมตามช่วงเวลา
        - 06:00-11:59 → Online (เขียว)
        - 12:00-18:59 → Idle (เหลือง)
        - 19:00-05:59 → DND (แดง)
    """
    now = datetime.now()
    current_hour = now.hour

    if 6 <= current_hour < 12:
        return discord.Status.online
    elif 12 <= current_hour < 19:
        return discord.Status.idle
    else:
        return discord.Status.dnd


# =========================
# BOT 1 SETUP
# =========================
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=PREFIX,
            intents=intents,
            help_command=None,  # ปิด help command เดิม
            owner_id=OWNER_ID,
            case_insensitive=True,  # คำสั่งไม่สนใจตัวพิมพ์เล็ก-ใหญ่
        )
        self.start_time = datetime.now(timezone.utc)

    async def setup_hook(self):
        """เรียกทุกครั้งก่อนบอทจะเชื่อมต่อ"""
        await self.load_cogs()

    async def load_cogs(self):
        """โหลด cogs ทั้งหมดจากโฟลเดอร์ cogs"""
        cogs_to_load = [
            "cogs.verify",
            "cogs.admin",
            "cogs.dm_syaem",
            "cogs.hely",
            "cogs.userinfo",
            "cogs.bot_inspect",
            "cogs.shop",
            "cogs.vc",
        ]

        print("📦 [BOT1] กำลังโหลด Cogs...")
        loaded = 0
        failed = 0

        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                print(f"  ✅ [BOT1] โหลด {cog} สำเร็จ")
                loaded += 1
            except Exception as e:
                print(f"  ❌ [BOT1] โหลด {cog} ล้มเหลว: {e}")
                failed += 1

        print(f"\n📊 [BOT1] สรุป: โหลดสำเร็จ {loaded} / {len(cogs_to_load)} Cogs")
        if failed > 0:
            print(f"⚠️  [BOT1] ล้มเหลว {failed} Cogs")


bot = MyBot()


# =========================
# BOT 2 SETUP
# =========================
class MyBot2(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=">>",  # ใช้ prefix ที่ไม่ซ้ำ แต่ไม่ได้ใช้งานจริง
            intents=intents,
            help_command=None,
        )
        self.start_time = datetime.now(timezone.utc)

    async def setup_hook(self):
        """เรียกทุกครั้งก่อนบอทจะเชื่อมต่อ"""
        await self.load_cogs()

    async def load_cogs(self):
        """โหลด cogs สำหรับบอท 2"""
        cogs_to_load = [
            "cogs.channel",

        ]

        print("📦 [BOT2] กำลังโหลด Cogs...")
        loaded = 0
        failed = 0

        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                print(f"  ✅ [BOT2] โหลด {cog} สำเร็จ")
                loaded += 1
            except Exception as e:
                print(f"  ❌ [BOT2] โหลด {cog} ล้มเหลว: {e}")
                failed += 1

        print(f"\n📊 [BOT2] สรุป: โหลดสำเร็จ {loaded} / {len(cogs_to_load)} Cogs")
        if failed > 0:
            print(f"⚠️  [BOT2] ล้มเหลว {failed} Cogs")


bot2 = MyBot2()

# =========================
# STATUS LIST (BOT 1 ONLY)
# =========================
status_list = [
    ("📖 /help - วิธีใช้คำสั่งทั้งหมด", discord.ActivityType.playing),
    ("</> พัฒนาเพื่อการศึกษา", discord.ActivityType.watching),
    ("🎶 Boulevard of Broken Dreams", discord.ActivityType.listening),
    ("✅ ระบบยืนยันตัวตนอัตโนมัติ", discord.ActivityType.watching),
    ("☢️ ดูแลโดยทีมงาน 24/7", discord.ActivityType.watching),
    (f"💫 อยู่ใน {len(bot.guilds)} เซิร์ฟเวอร์", discord.ActivityType.watching),
]

current_status = 0


# =========================
# EVENTS - BOT 1
# =========================
@bot.event
async def on_ready():
    """เมื่อบอทพร้อมใช้งาน"""
    print("\n" + "=" * 50)
    print(f"🤖 [BOT1] บอทออนไลน์แล้ว!")
    print(f"👤 ชื่อ: {bot.user}")
    print(f"🆔 ID: {bot.user.id}")
    print(f"🌍 เซิร์ฟเวอร์: {len(bot.guilds)} เซิร์ฟ")
    print(f"👥 สมาชิก: {sum(g.member_count for g in bot.guilds):,} คน")
    print(f"⏰ เริ่มต้นเมื่อ: {bot.start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 50 + "\n")

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"✅ [BOT1] ซิงค์ Slash Commands สำเร็จ ({len(synced)} คำสั่ง)")
    except Exception as e:
        print(f"❌ [BOT1] ซิงค์ Slash Commands ล้มเหลว: {e}")

    # เริ่ม status loop
    if not change_status.is_running():
        change_status.start()
        print("✅ [BOT1] เริ่ม Status Rotation แล้ว")
        print(f"⏰ [BOT1] Time-Based Status: {get_time_based_status()}\n")


@bot.event
async def on_guild_join(guild):
    """เมื่อบอทเข้าเซิร์ฟใหม่"""
    print(f"➕ [BOT1] เข้าเซิร์ฟใหม่: {guild.name} (ID: {guild.id}) | สมาชิก: {guild.member_count}")


@bot.event
async def on_guild_remove(guild):
    """เมื่อบอทออกจากเซิร์ฟ"""
    print(f"➖ [BOT1] ออกจากเซิร์ฟ: {guild.name} (ID: {guild.id})")


@bot.event
async def on_command_error(ctx, error):
    """จัดการ error ของ prefix commands"""
    if isinstance(error, commands.CommandNotFound):
        return  # ไม่แสดงอะไรถ้าไม่เจอคำสั่ง

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
    """จัดการ error ทั่วไป"""
    print(f"❌ [BOT1] Error in {event}:")
    import traceback
    traceback.print_exc()


# =========================
# EVENTS - BOT 2
# =========================
@bot2.event
async def on_ready():
    """เมื่อบอท 2 พร้อมใช้งาน"""
    print("\n" + "=" * 50)
    print(f"🤖 [BOT2] บอทออนไลน์แล้ว!")
    print(f"👤 ชื่อ: {bot2.user}")
    print(f"🆔 ID: {bot2.user.id}")
    print(f"🌍 เซิร์ฟเวอร์: {len(bot2.guilds)} เซิร์ฟ")
    print(f"👥 สมาชิก: {sum(g.member_count for g in bot2.guilds):,} คน")
    print(f"⏰ เริ่มต้นเมื่อ: {bot2.start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 50 + "\n")

    # Sync slash commands
    try:
        synced = await bot2.tree.sync()
        print(f"✅ [BOT2] ซิงค์ Slash Commands สำเร็จ ({len(synced)} คำสั่ง)\n")
    except Exception as e:
        print(f"❌ [BOT2] ซิงค์ Slash Commands ล้มเหลว: {e}\n")


@bot2.event
async def on_guild_join(guild):
    """เมื่อบอท 2 เข้าเซิร์ฟใหม่"""
    print(f"➕ [BOT2] เข้าเซิร์ฟใหม่: {guild.name} (ID: {guild.id}) | สมาชิก: {guild.member_count}")


@bot2.event
async def on_guild_remove(guild):
    """เมื่อบอท 2 ออกจากเซิร์ฟ"""
    print(f"➖ [BOT2] ออกจากเซิร์ฟ: {guild.name} (ID: {guild.id})")


@bot2.event
async def on_error(event, *_args, **_kwargs):
    """จัดการ error ทั่วไป"""
    print(f"❌ [BOT2] Error in {event}:")
    import traceback
    traceback.print_exc()


# =========================
# STATUS LOOP (BOT 1 ONLY)
# =========================
@tasks.loop(seconds=10)
async def change_status():
    """
    เปลี่ยน activity ทุก 10 วินาที พร้อมกับปรับสถานะตามเวลา

    Status ตามเวลา:
    - 06:00-11:59 → Online (เขียว)
    - 12:00-18:59 → Idle (เหลือง)
    - 19:00-05:59 → DND (แดง)
    """
    global current_status

    # อัปเดตจำนวนเซิร์ฟเวอร์ในสถานะที่ 5
    status_list[5] = (f"💫 อยู่ใน {len(bot.guilds)} เซิร์ฟเวอร์", discord.ActivityType.watching)

    # ดึง activity ปัจจุบัน
    status_text, activity_type = status_list[current_status]

    # ดึงสถานะตามเวลา
    time_status = get_time_based_status()

    # อัปเดตสถานะ
    await bot.change_presence(
        activity=discord.Activity(
            type=activity_type,
            name=status_text
        ),
        status=time_status
    )

    # หมุนเวียน activity
    current_status = (current_status + 1) % len(status_list)


@change_status.before_loop
async def before_change_status():
    """รอให้บอทพร้อมก่อนเริ่ม loop"""
    await bot.wait_until_ready()


# =========================
# OWNER COMMANDS (BOT 1 ONLY)
# =========================
@bot.command(name="reload", hidden=True)
@commands.is_owner()
async def reload_cog(ctx, cog_name: str):
    """โหลด cog ใหม่ (เฉพาะ owner)"""
    try:
        await bot.reload_extension(f"cogs.{cog_name}")
        await ctx.send(f"✅ โหลด `{cog_name}` ใหม่สำเร็จ")
    except Exception as e:
        await ctx.send(f"❌ โหลด `{cog_name}` ล้มเหลว: {e}")


@bot.command(name="load", hidden=True)
@commands.is_owner()
async def load_cog(ctx, cog_name: str):
    """โหลด cog (เฉพาะ owner)"""
    try:
        await bot.load_extension(f"cogs.{cog_name}")
        await ctx.send(f"✅ โหลด `{cog_name}` สำเร็จ")
    except Exception as e:
        await ctx.send(f"❌ โหลด `{cog_name}` ล้มเหลว: {e}")


@bot.command(name="unload", hidden=True)
@commands.is_owner()
async def unload_cog(ctx, cog_name: str):
    """ยกเลิกโหลด cog (เฉพาะ owner)"""
    try:
        await bot.unload_extension(f"cogs.{cog_name}")
        await ctx.send(f"✅ ยกเลิกโหลด `{cog_name}` สำเร็จ")
    except Exception as e:
        await ctx.send(f"❌ ยกเลิกโหลด `{cog_name}` ล้มเหลว: {e}")


@bot.command(name="sync", hidden=True)
@commands.is_owner()
async def sync_commands(ctx):
    """ซิงค์ slash commands ใหม่ (เฉพาะ owner)"""
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"✅ ซิงค์สำเร็จ ({len(synced)} คำสั่ง)")
    except Exception as e:
        await ctx.send(f"❌ ซิงค์ล้มเหลว: {e}")


@bot.command(name="shutdown", aliases=["stop"], hidden=True)
@commands.is_owner()
async def shutdown(ctx):
    """ปิดบอท (เฉพาะ owner)"""
    await ctx.send("👋 กำลังปิดบอททั้งสอง...")
    await bot.close()
    await bot2.close()


@bot.command(name="ping")
async def ping(ctx):
    """เช็ค latency ของบอท"""
    latency = round(bot.latency * 1000)

    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"**Latency:** `{latency}ms`",
        color=discord.Color.green() if latency < 100 else discord.Color.orange()
    )

    await ctx.send(embed=embed)


@bot.command(name="stats", aliases=["info", "botinfo"])
async def stats(ctx):
    """แสดงสถิติของบอท"""
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
        value=(
            f"**เซิร์ฟเวอร์:** {len(bot.guilds):,}\n"
            f"**สมาชิก:** {sum(g.member_count for g in bot.guilds):,}\n"
            f"**Ping:** {round(bot.latency * 1000)}ms"
        ),
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

    # แสดงสถานะปัจจุบัน
    current_time = datetime.now().strftime("%H:%M")
    embed.add_field(
        name="🕒 สถานะปัจจุบัน",
        value=(
            f"**เวลา:** {current_time}\n"
            f"**Status:** {get_time_based_status()}"
        ),
        inline=False
    )

    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_footer(text=f"ขอโดย {ctx.author}", icon_url=ctx.author.display_avatar.url)

    await ctx.send(embed=embed)


# =========================
# MAIN ASYNC RUNNER
# =========================
async def run_bots():
    """รันบอททั้งสองพร้อมกัน"""

    async def start_bot1():
        """เริ่มบอท 1"""
        try:
            await bot.start(TOKEN)
        except discord.LoginFailure:
            print("\n❌ [BOT1] TOKEN ไม่ถูกต้อง!")
            print("💡 ตรวจสอบ TOKEN ใน Developer Portal")
        except Exception as error:
            print(f"\n❌ [BOT1] เกิดข้อผิดพลาด: {error}")
            import traceback
            traceback.print_exc()

    async def start_bot2():
        """เริ่มบอท 2"""
        try:
            if TOKEN_2 == "YOUR_SECOND_BOT_TOKEN_HERE":
                print("\n⚠️  [BOT2] ไม่พบ TOKEN_2 - ข้าม Bot 2")
                return

            await bot2.start(TOKEN_2)
        except discord.LoginFailure:
            print("\n❌ [BOT2] TOKEN ไม่ถูกต้อง!")
            print("💡 ตรวจสอบ DISCORD_TOKEN_2 ใน environment variable")
        except Exception as error:
            print(f"\n❌ [BOT2] เกิดข้อผิดพลาด: {error}")
            import traceback
            traceback.print_exc()

    # รันทั้งสองบอทพร้อมกัน
    await asyncio.gather(
        start_bot1(),
        start_bot2()
    )


# =========================
# RUN BOT
# =========================
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