import discord
from discord import app_commands
from discord.ext import commands
import sys
import time
from datetime import datetime, timezone
import logging

# Try to import psutil, but continue without it if not available
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Stability Calculator
# ═══════════════════════════════════════════════════════════════

class StabilityCalculator:
    """คำนวณความเสถียรของบอท"""

    def __init__(self):
        self.start_time = time.time()
        self.error_count = 0
        self.reconnect_count = 0

    def add_error(self):
        """เพิ่มจำนวน error"""
        self.error_count += 1

    def add_reconnect(self):
        """เพิ่มจำนวนการ reconnect"""
        self.reconnect_count += 1

    def calculate_stability(self) -> int:
        """
        คำนวณความเสถียร (0-100%)

        Formula:
        uptime_seconds = now - start_time
        error_rate = (error_count / max(uptime_seconds, 1)) * 100
        stability = max(0, min(100, 100 - error_rate))

        Returns:
            float: ความเสถียรเป็นเปอร์เซ็นต์
        """
        uptime_seconds = time.time() - self.start_time
        error_rate = (self.error_count / max(uptime_seconds, 1)) * 100
        stability = max(0, min(100, int(100 - error_rate)))
        return int(round(stability))

    def get_uptime(self) -> str:
        """
        ดึง uptime ในรูปแบบอ่านง่าย

        Returns:
            str: uptime (เช่น "2d 5h 30m 15s")
        """
        uptime_seconds = int(time.time() - self.start_time)

        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")

        return " ".join(parts)


# ═══════════════════════════════════════════════════════════════
# Health Monitor
# ═══════════════════════════════════════════════════════════════

class HealthMonitor:
    """ตรวจสอบสุขภาพระบบ"""

    @staticmethod
    def get_cpu_usage() -> str:
        """ดึง CPU usage หรือ N/A ถ้าไม่มี psutil"""
        if not PSUTIL_AVAILABLE or psutil is None:
            return "N/A"
        try:
            cpu = psutil.cpu_percent(interval=0.5)  # type: ignore
            return f"{cpu:.1f}"
        except (ValueError, TypeError, AttributeError):
            return "N/A"

    @staticmethod
    def get_memory_info() -> tuple[str, str]:
        if not PSUTIL_AVAILABLE or psutil is None:
            return "N/A", "N/A"

        try:
            assert psutil is not None
            mem = psutil.virtual_memory()  # type: ignore[attr-defined]

            return f"{mem.percent:.1f}", f"{int(mem.used / (1024 * 1024))}"

        except (ValueError, TypeError, AttributeError):
            return "N/A", "N/A"


# ═══════════════════════════════════════════════════════════════
# Inspect View (Dropdown)
# ═══════════════════════════════════════════════════════════════

class InspectView(discord.ui.View):
    """View สำหรับ Bot Inspect Panel"""

    def __init__(
            self,
            bot: commands.Bot,
            stability_calc: StabilityCalculator,
            author_id: int,
    ):
        super().__init__(timeout=300)
        self.bot = bot
        self.stability_calc = stability_calc
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                ":x: Panel นี้เป็นของคนที่เปิดเท่านั้น",
                ephemeral=True
            )
            return False

        return True

    @discord.ui.select(
        placeholder="📊 เลือกหน้าที่ต้องการดู",
        options=[
            discord.SelectOption(
                label="Overview",
                description="ภาพรวมของบอท",
                emoji="📊",
                value="overview",
                default=True
            ),
            discord.SelectOption(
                label="Commands",
                description="รายชื่อคำสั่งทั้งหมด",
                emoji="⚙️",
                value="commands"
            ),
            discord.SelectOption(
                label="System Health",
                description="สุขภาพระบบและ performance",
                emoji="💊",
                value="health"
            ),
            discord.SelectOption(
                label="Capabilities",
                description="ความสามารถของบอท",
                emoji="✨",
                value="capabilities"
            ),
            discord.SelectOption(
                label="Architecture",
                description="สถาปัตยกรรมระบบ",
                emoji="🏗️",
                value="architecture"
            ),
        ],
    )
    async def select_callback(
            self,
            interaction: discord.Interaction,
            select: discord.ui.Select,
    ):
        """เมื่อเลือกเมนู"""
        page = select.values[0]

        # สร้าง embed ตามหน้าที่เลือก
        if page == "overview":
            embed = await self._build_overview()
        elif page == "commands":
            embed = self._build_commands()
        elif page == "health":
            embed = self._build_health()
        elif page == "capabilities":
            embed = self._build_capabilities()
        elif page == "architecture":
            embed = self._build_architecture()
        else:
            embed = await self._build_overview()

        # อัปเดต default option
        for option in select.options:
            option.default = (option.value == page)

        await interaction.response.edit_message(embed=embed, view=self)

    async def _build_overview(self) -> discord.Embed:
        """สร้างหน้า Overview"""
        embed = discord.Embed(
            title="📊 Overview",
            description="ข้อมูลนี้เปิดเผยได้บางส่วนสำหรับการตรวจสอบระบบ",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )

        # ดึงข้อมูล creator
        try:
            app_info = await self.bot.application_info()
            creator = str(app_info.owner)
        except (ValueError, TypeError, AttributeError):
            creator = "ไม่สามารถดึงข้อมูลได้"

        # คำนวณสถิติ
        total_members = sum(g.member_count for g in self.bot.guilds)
        prefix_cmds = len([c for c in self.bot.commands])
        slash_cmds = len(self.bot.tree.get_commands())

        embed.add_field(
            name="👑 Creator",
            value=f"`{creator}`",
            inline=True
        )

        embed.add_field(
            name="🤖 Bot ID",
            value=f"`{self.bot.user.id}`",
            inline=True
        )

        embed.add_field(
            name="📅 วันที่สร้างบอท",
            value=discord.utils.format_dt(self.bot.user.created_at, 'D'),
            inline=True
        )

        embed.add_field(
            name="🕒 Uptime",
            value=f"`{self.stability_calc.get_uptime()}`",
            inline=True
        )

        embed.add_field(
            name="🌍 จำนวนเซิร์ฟเวอร์",
            value=f"`{len(self.bot.guilds):,}`",
            inline=True
        )

        embed.add_field(
            name="👥 สมาชิกทั้งหมด",
            value=f"`{total_members:,}`",
            inline=True
        )

        embed.add_field(
            name="⚙ Prefix Commands",
            value=f"`{prefix_cmds}`",
            inline=True
        )

        embed.add_field(
            name="⚙ Slash Commands",
            value=f"`{slash_cmds}`",
            inline=True
        )

        embed.add_field(
            name="📡 Latency",
            value=f"`{int(round(self.bot.latency * 1000))} ms`",
            inline=True
        )

        embed.add_field(
            name="📊 Stability",
            value=f"`{self.stability_calc.calculate_stability()}%`",
            inline=True
        )

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Secure Diagnostic Panel • No sensitive data exposed")

        return embed

    def _build_commands(self) -> discord.Embed:
        """สร้างหน้า Commands"""
        embed = discord.Embed(
            title="⚙️ Commands",
            description="ข้อมูลนี้เปิดเผยได้บางส่วนสำหรับการตรวจสอบระบบ",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )

        # จัดกลุ่มคำสั่งตาม Cog
        cog_commands: dict[str, list[str]] = {}

        # Prefix commands
        for cmd in self.bot.commands:
            cog_name = cmd.cog_name or "ไม่มี Cog"
            if cog_name not in cog_commands:
                cog_commands[cog_name] = []
            cog_commands[cog_name].append(f"`!{cmd.name}` (Prefix)")

        # Slash commands
        for cmd in self.bot.tree.get_commands():
            # หา cog ที่เป็นเจ้าของคำสั่งนี้
            cog_name = "ไม่มี Cog"
            for cog in self.bot.cogs.values():
                if hasattr(cog, cmd.name):
                    cog_name = cog.__class__.__name__
                    break

            if cog_name not in cog_commands:
                cog_commands[cog_name] = []
            cog_commands[cog_name].append(f"`/{cmd.name}` (Slash)")

        # สรุป
        total_prefix = len([c for c in self.bot.commands])
        total_slash = len(self.bot.tree.get_commands())

        embed.add_field(
            name="📊 สรุป",
            value=(
                f"**Prefix Commands:** `{total_prefix}`\n"
                f"**Slash Commands:** `{total_slash}`\n"
                f"**รวมทั้งหมด:** `{total_prefix + total_slash}`"
            ),
            inline=False
        )

        # แสดงคำสั่งแยกตาม Cog
        for cog_name, commands_list in sorted(cog_commands.items()):
            # จำกัดความยาวไม่เกิน 1024 ตัวอักษร
            cmd_text = "\n".join(commands_list[:15])  # แสดงแค่ 15 คำสั่งแรก

            if len(commands_list) > 15:
                cmd_text += f"\n... และอีก {len(commands_list) - 15} คำสั่ง"

            embed.add_field(
                name=f"📁 {cog_name} ({len(commands_list)})",
                value=cmd_text or "ไม่มีคำสั่ง",
                inline=False
            )

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Secure Diagnostic Panel • No sensitive data exposed")

        return embed

    def _build_health(self) -> discord.Embed:
        """สร้างหน้า System Health"""
        embed = discord.Embed(
            title="💊 System Health",
            description="ข้อมูลนี้เปิดเผยได้บางส่วนสำหรับการตรวจสอบระบบ",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )

        # ดึงข้อมูลระบบ
        cpu_usage = HealthMonitor.get_cpu_usage()
        ram_percent, ram_mb = HealthMonitor.get_memory_info()

        embed.add_field(
            name="💻 CPU Usage",
            value=f"`{cpu_usage}%`" if cpu_usage != "N/A" else "`N/A`",
            inline=True
        )

        embed.add_field(
            name="🧠 RAM Usage",
            value=f"`{ram_percent}%`" if ram_percent != "N/A" else "`N/A`",
            inline=True
        )

        embed.add_field(
            name="💾 Memory Used",
            value=f"`{ram_mb} MB`" if ram_mb != "N/A" else "`N/A`",
            inline=True
        )

        embed.add_field(
            name="📡 Ping",
            value=f"`{int(round(self.bot.latency * 1000))} ms`",
            inline=True
        )

        embed.add_field(
            name="🔄 Reconnect Count",
            value=f"`{self.stability_calc.reconnect_count}`",
            inline=True
        )

        embed.add_field(
            name="❌ Error Count",
            value=f"`{self.stability_calc.error_count}`",
            inline=True
        )

        embed.add_field(
            name="🕒 Uptime (ละเอียด)",
            value=f"`{self.stability_calc.get_uptime()}`",
            inline=True
        )

        embed.add_field(
            name="📊 Stability",
            value=f"`{self.stability_calc.calculate_stability()}%`",
            inline=True
        )

        # แสดงสุขภาพรวม
        stability = self.stability_calc.calculate_stability()
        if stability >= 99:
            health_status = "🟢 ดีเยี่ยม"
        elif stability >= 95:
            health_status = "🟡 ดี"
        elif stability >= 90:
            health_status = "🟠 พอใช้"
        else:
            health_status = "🔴 ต้องปรับปรุง"

        embed.add_field(
            name="🏥 สุขภาพรวม",
            value=f"`{health_status}`",
            inline=True
        )

        if not PSUTIL_AVAILABLE:
            embed.add_field(
                name="⚠️ หมายเหตุ",
                value="`psutil ไม่พร้อมใช้งาน - ข้อมูล CPU/RAM แสดงเป็น N/A`",
                inline=False
            )

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Secure Diagnostic Panel • No sensitive data exposed")

        return embed

    def _build_capabilities(self) -> discord.Embed:
        """สร้างหน้า Capabilities"""
        embed = discord.Embed(
            title="✨ Capabilities",
            description="ข้อมูลนี้เปิดเผยได้บางส่วนสำหรับการตรวจสอบระบบ",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )

        # ตรวจสอบความสามารถ
        capabilities = []

        if len(self.bot.tree.get_commands()) > 0:
            capabilities.append("✅ รองรับ Slash Commands")

        if len(self.bot.cogs) > 0:
            capabilities.append("✅ ใช้ Cog System")

        capabilities.append("✅ มี Logging System")
        capabilities.append("✅ มี Permission Validation")
        capabilities.append("✅ มี Error Handling")
        capabilities.append("✅ มี Monitoring System")

        if len(self.bot.guilds) > 1:
            capabilities.append("✅ รองรับ Multi-Guild")

        capabilities.append("✅ ใช้ Async Architecture")

        embed.add_field(
            name="🎯 ความสามารถ",
            value="\n".join(capabilities),
            inline=False
        )

        embed.add_field(
            name="📊 สถิติเพิ่มเติม",
            value=(
                f"**Loaded Cogs:** `{len(self.bot.cogs)}`\n"
                f"**Event Listeners:** `{len(self.bot.extra_events)}`\n"
                f"**Total Guilds:** `{len(self.bot.guilds)}`"
            ),
            inline=False
        )

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Secure Diagnostic Panel • No sensitive data exposed")

        return embed

    def _build_architecture(self) -> discord.Embed:
        """สร้างหน้า Architecture"""
        embed = discord.Embed(
            title="🏗️ Architecture",
            description="ข้อมูลนี้เปิดเผยได้บางส่วนสำหรับการตรวจสอบระบบ",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )

        # ข้อมูล Python และ discord.py
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        embed.add_field(
            name="🐍 Python Version",
            value=f"`{python_version}`",
            inline=True
        )

        embed.add_field(
            name="📦 discord.py Version",
            value=f"`{discord.__version__}`",
            inline=True
        )

        embed.add_field(
            name="📁 Loaded Cogs",
            value=f"`{len(self.bot.cogs)}`",
            inline=True
        )

        embed.add_field(
            name="📡 Event Listeners",
            value=f"`{len(self.bot.extra_events)}`",
            inline=True
        )

        embed.add_field(
            name="🏛️ โครงสร้าง",
            value="```\nModular\n```",
            inline=True
        )

        # รายชื่อ Cogs
        if self.bot.cogs:
            cog_list = "\n".join(f"• `{name}`" for name in sorted(self.bot.cogs.keys())[:12])
            if len(self.bot.cogs) > 12:
                cog_list += f"\n... และอีก {len(self.bot.cogs) - 12} cogs"

            embed.add_field(
                name="📂 รายชื่อ Cogs",
                value=cog_list,
                inline=False
            )

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Secure Diagnostic Panel • No sensitive data exposed")

        return embed

    async def on_timeout(self):
        """เมื่อหมดเวลา"""
        self.clear_items()


# ═══════════════════════════════════════════════════════════════
# Bot Inspect Cog
# ═══════════════════════════════════════════════════════════════

class BotInspect(commands.Cog):
    """Owner-Only Secure Bot Diagnostic Panel"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.stability = StabilityCalculator()

    @commands.Cog.listener()
    async def on_disconnect(self):
        """เมื่อบอท disconnect"""
        self.stability.add_reconnect()
        logger.warning("Bot disconnected - reconnect count increased")

    @commands.Cog.listener()
    async def on_command_error(self, _ctx: commands.Context, error: commands.CommandError):
        """เมื่อเกิด error ใน prefix command"""
        self.stability.add_error()
        logger.error(f"Command error: {error}")

    @commands.Cog.listener()
    async def on_app_command_error(
            self,
            _interaction: discord.Interaction,
            error: app_commands.AppCommandError
    ):
        """เมื่อเกิด error ใน slash command"""
        self.stability.add_error()
        logger.error(f"App command error: {error}")

    @app_commands.command(
        name="bot-inspect",
        description="🔒 Owner-Only Secure Bot Diagnostic Panel"
    )
    async def inspect(self, interaction: discord.Interaction):
        """เปิด Bot Inspect Panel"""

        # ตรวจสอบว่าใช้ในเซิร์ฟเวอร์
        if not interaction.guild:
            return await interaction.response.send_message(
                "❌ คำสั่งนี้ใช้ได้เฉพาะในเซิร์ฟเวอร์เท่านั้น",
                ephemeral=True
            )

        # ตรวจสอบว่าเป็นเจ้าของเซิร์ฟหรือไม่
        if interaction.guild.owner_id != interaction.user.id:
            return await interaction.response.send_message(
                "❌ คำสั่งนี้สำหรับเจ้าของเซิร์ฟเวอร์เท่านั้น",
                ephemeral=True
            )

        # สร้าง View
        view = InspectView(self.bot, self.stability, interaction.user.id)

        # สร้าง embed เริ่มต้น (Overview)
        embed = await view._build_overview()

        # ส่ง panel
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True
        )


# ═══════════════════════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════════════════════

async def setup(bot: commands.Bot):
    await bot.add_cog(BotInspect(bot))