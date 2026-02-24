import discord
from discord import app_commands
from discord.ext import commands
from discord import Interaction, VoiceChannel, Embed, Color
import datetime


# หมวดหมู่: ชั้นนำเข้า
# นำเข้าเฉพาะสิ่งที่จำเป็นสำหรับการทำ Command Interface และ Embed เท่านั้น

class VoiceCommands(commands.Cog):
    """
    VoiceCommands (Command Interface Layer)
    ทำหน้าที่เป็นส่วนหน้าในการรับคำสั่งเชื่อมต่อและตัดการเชื่อมต่อห้องเสียง
    โดยไม่มีการยุ่งเกี่ยวกับระบบ Presence, Activity หรือ Business Logic ภายนอก
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def create_base_embed(self, interaction: Interaction, title: str, color: Color) -> Embed:
        """สร้างโครงสร้างพื้นฐานของ Embed ที่เป็นมาตรฐานสำหรับ COREx9"""
        embed = Embed(title=title, color=color, timestamp=datetime.datetime.now(datetime.timezone.utc))
        embed.add_field(name="🌐 Server Name", value=f"`{interaction.guild.name}`", inline=True)
        embed.add_field(name="🆔 Server ID", value=f"`{interaction.guild.id}`", inline=True)
        embed.add_field(name="👤 Requested By", value=interaction.user.mention, inline=False)
        embed.set_footer(text="COREx9 Voice Control System")
        return embed

    # หมวดหมู่: ชั้นรับคำสั่ง
    @app_commands.command(name="jump_vc", description="สั่งให้ COREx9 เข้าร่วมหรือย้ายไปยังห้องเสียงที่กำหนด")
    @app_commands.describe(channel="ห้องเสียงที่ต้องการให้บอทเข้าร่วม")
    @app_commands.checks.has_permissions(move_members=True)
    async def jump_vc(self, interaction: Interaction, channel: VoiceChannel):
        # หมวดหมู่: ตรวจสอบสิทธิ์
        await interaction.response.defer(thinking=True)

        guild = interaction.guild
        bot_member = guild.me
        voice_client = guild.voice_client

        # ตรวจสอบสิทธิ์การเข้าถึงห้องเสียงของตัวบอท
        permissions = channel.permissions_for(bot_member)
        if not permissions.connect or not permissions.speak:
            embed = self.create_base_embed(interaction, "🚨 Permission Denied", Color.red())
            embed.description = f"บอทขาดสิทธิ์ที่จำเป็นในการเข้าใช้งานห้องเสียง {channel.mention}"
            embed.add_field(name="❌ Missing Permissions", value="`Connect` หรือ `Speak`", inline=False)
            embed.add_field(name="🛠️ Solution", value="กรุณาตรวจสอบการตั้งค่า Permission ในห้องเสียงหรือ Role ของบอท",
                            inline=False)
            return await interaction.followup.send(embed=embed)

        # หมวดหมู่: เชื่อมต่อห้องเสียง
        try:
            status_action = ""
            embed_color = Color.green()

            if voice_client is None:
                # กรณีบอทยังไม่ได้เชื่อมต่อห้องใดเลย
                await channel.connect()
                status_action = "เชื่อมต่อสำเร็จ (Initial Connection)"
                embed_color = Color.green()
            elif voice_client.channel.id == channel.id:
                # กรณีบอทอยู่ในห้องนั้นอยู่แล้ว
                embed = self.create_base_embed(interaction, "ℹ️ Already Connected", Color.blue())
                embed.description = f"COREx9 ประจำการอยู่ในห้อง {channel.mention} เรียบร้อยแล้ว"
                embed.add_field(name="📍 Current Room", value=channel.name, inline=True)
                embed.add_field(name="📡 Execution Status", value="ไม่มีการดำเนินการ (Skip)", inline=True)
                return await interaction.followup.send(embed=embed)
            else:
                # กรณีบอทอยู่ห้องอื่นและต้องทำการย้าย
                await voice_client.move_to(channel)
                status_action = "ย้ายห้องสำเร็จ (Channel Migration)"
                embed_color = Color.blue()

            # แสดง Embed เมื่อดำเนินการสำเร็จ
            embed = self.create_base_embed(interaction, "✅ Jump VC Successful", embed_color)
            embed.description = f"COREx9 ดำเนินการเข้าสู่ห้องเสียงตามคำสั่งเรียบร้อยแล้ว"
            embed.add_field(name="🔊 Target Channel", value=f"`{channel.name}`", inline=True)
            embed.add_field(name="⚙️ Action Taken", value=status_action, inline=True)
            embed.add_field(name="📊 Connection Status", value="Connected & Active", inline=False)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await self.handle_error(interaction, e)

    # หมวดหมู่: ตัดการเชื่อมต่อ
    @app_commands.command(name="leave_vc", description="สั่งให้ COREx9 ตัดการเชื่อมต่อจากห้องเสียงปัจจุบัน")
    @app_commands.checks.has_permissions(move_members=True)
    async def leave_vc(self, interaction: Interaction):
        await interaction.response.defer(thinking=True)

        guild = interaction.guild
        voice_client = guild.voice_client

        if voice_client is None:
            embed = self.create_base_embed(interaction, "⚠️ Not Connected", Color.red())
            embed.description = "ไม่สามารถดำเนินการได้ เนื่องจาก COREx9 ไม่ได้เชื่อมต่อกับห้องเสียงใดๆ ในเซิร์ฟเวอร์นี้"
            return await interaction.followup.send(embed=embed)

        try:
            current_channel = voice_client.channel
            await voice_client.disconnect(force=True)

            embed = self.create_base_embed(interaction, "🔌 Disconnected Successful", Color.orange())
            embed.description = "COREx9 ตัดการเชื่อมต่อจากระบบเสียงเรียบร้อยแล้ว"
            embed.add_field(name="📍 Previous Channel", value=f"`{current_channel.name}`", inline=True)
            embed.add_field(name="📉 Action Taken", value="ตัดการเชื่อมต่อ (Force Disconnect)", inline=True)
            embed.add_field(name="📊 Final Status", value="Disconnected", inline=False)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await self.handle_error(interaction, e)

    # หมวดหมู่: จัดการข้อผิดพลาด
    async def handle_error(self, interaction: Interaction, error: Exception):
        """ระบบรวมศูนย์การจัดการข้อผิดพลาดและแสดงผลผ่าน Embed อย่างละเอียด"""
        embed = self.create_base_embed(interaction, "❌ Unexpected Error Occurred", Color.red())

        if isinstance(error, discord.Forbidden):
            error_msg = "บอทถูกปฏิเสธการเข้าถึง (Forbidden) อาจเกิดจาก Role ของบอทอยู่ต่ำกว่าเป้าหมาย หรือถูกแบน"
        elif isinstance(error, discord.HTTPException):
            error_msg = "เกิดข้อผิดพลาดในการส่งข้อมูลไปยัง Discord API (HTTP Exception)"
        else:
            error_msg = f"เกิดข้อผิดพลาดที่ไม่คาดคิด: `{str(error)}`"

        embed.description = "ไม่สามารถดำเนินการตามคำสั่งได้เนื่องจากปัญหาทางเทคนิค"
        embed.add_field(name="🔍 Error Details", value=f"```{error_msg}```", inline=False)
        embed.add_field(name="📋 Exception Type", value=f"`{type(error).__name__}`", inline=True)

        if interaction.response.is_done():
            await interaction.followup.send(embed=embed)
        else:
            await interaction.response.send_message(embed=embed)

    @jump_vc.error
    @leave_vc.error
    async def permission_error_handler(self, interaction: Interaction, error: app_commands.AppCommandError):
        """จัดการข้อผิดพลาดเรื่องสิทธิ์ของผู้ใช้งาน (Permission)"""
        if isinstance(error, app_commands.MissingPermissions):
            embed = self.create_base_embed(interaction, "🚫 User Permission Denied", Color.red())
            embed.description = "คุณไม่มีสิทธิ์เพียงพอในการสั่งการคำสั่ง Voice นี้"
            embed.add_field(name="🔑 Required Permission", value="`Move Members` หรือ `Manage Channels`", inline=False)
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)


# หมวดหมู่: ลงทะเบียน Cog
async def setup(bot: commands.Bot):
    """ลงทะเบียน Cog เข้าสู่ระบบบอทหลัก"""
    await bot.add_cog(VoiceCommands(bot))