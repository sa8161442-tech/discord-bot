import discord
from discord.ext import commands
import asyncio
import time

MAX_MESSAGES = 10000


def _is_authorized(ctx: commands.Context) -> bool:
    member: discord.Member = ctx.author  # type: ignore[assignment]
    return (
        ctx.guild.owner_id == member.id
        or member.guild_permissions.administrator
    )


class Clear(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="clear")
    async def clear(self, ctx: commands.Context, amount: int | None = None) -> None:

        # ── ตรวจสอบสิทธิ์ ──────────────────────────────────────
        if not _is_authorized(ctx):
            embed = discord.Embed(
                description="❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed, delete_after=5)
            try:
                await ctx.message.delete()
            except discord.HTTPException:
                pass
            return

        # ── ตรวจสอบ argument ────────────────────────────────────
        if amount is None:
            embed = discord.Embed(
                title="รูปแบบการใช้งาน",
                description="```!clear <จำนวน>```\nตัวอย่าง: `!clear 500`",
                color=discord.Color.orange(),
            )
            await ctx.send(embed=embed, delete_after=10)
            try:
                await ctx.message.delete()
            except discord.HTTPException:
                pass
            return

        if amount > MAX_MESSAGES:
            embed = discord.Embed(
                description=f"❌ จำกัดสูงสุด **{MAX_MESSAGES:,}** ข้อความต่อครั้ง",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed, delete_after=8)
            try:
                await ctx.message.delete()
            except discord.HTTPException:
                pass
            return

        if amount < 1:
            embed = discord.Embed(
                description="❌ จำนวนต้องมากกว่า 0",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed, delete_after=8)
            try:
                await ctx.message.delete()
            except discord.HTTPException:
                pass
            return

        # ── ลบคำสั่งผู้ใช้ ──────────────────────────────────────
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

        # ── Embed แจ้ง: กำลังดำเนินการ ─────────────────────────
        processing_embed = discord.Embed(
            title="ระบบกำลังดำเนินการลบข้อความ…",
            description=(
                f"**กำลังลบจำนวน:** `{amount:,}` ข้อความ\n"
                "โปรดรอสักครู่"
            ),
            color=discord.Color.yellow(),
        )
        processing_msg = await ctx.send(embed=processing_embed)

        # ── เริ่มจับเวลา ────────────────────────────────────────
        start_time = time.monotonic()

        # ── Purge ───────────────────────────────────────────────
        deleted_count = 0
        try:
            deleted = await ctx.channel.purge(
                limit=amount,
                check=lambda m: m.id != processing_msg.id,
                bulk=True,
            )
            deleted_count = len(deleted)

        except discord.Forbidden:
            error_embed = discord.Embed(
                description="❌ บอทไม่มีสิทธิ์ลบข้อความในช่องนี้",
                color=discord.Color.red(),
            )
            await processing_msg.edit(embed=error_embed)
            await asyncio.sleep(8)
            try:
                await processing_msg.delete()
            except discord.HTTPException:
                pass
            return

        except discord.HTTPException:
            error_embed = discord.Embed(
                description="❌ เกิดข้อผิดพลาดขณะลบข้อความ กรุณาลองใหม่",
                color=discord.Color.red(),
            )
            await processing_msg.edit(embed=error_embed)
            await asyncio.sleep(8)
            try:
                await processing_msg.delete()
            except discord.HTTPException:
                pass
            return

        # ── คำนวณสถิติ ──────────────────────────────────────────
        total_seconds: float = time.monotonic() - start_time
        average_speed: float = (
            deleted_count / total_seconds if total_seconds > 0 else deleted_count
        )

        # ── ลบ processing embed ─────────────────────────────────
        try:
            await processing_msg.delete()
        except discord.HTTPException:
            pass

        # ── Embed สรุปผล ────────────────────────────────────────
        result_embed = discord.Embed(
            title="รายงานการลบข้อความ",
            color=discord.Color.dark_red(),
        )

        result_embed.add_field(
            name="ผู้ดำเนินการ",
            value=ctx.author.mention,
            inline=False,
        )
        result_embed.add_field(
            name="ระบบที่ดำเนินการ",
            value=f"{self.bot.user.name}",
            inline=False,
        )
        result_embed.add_field(
            name="จำนวนที่ลบ",
            value=f"`{deleted_count:,}` ข้อความ",
            inline=False,
        )
        result_embed.add_field(
            name="ใช้เวลาทั้งหมด",
            value=f"`{total_seconds:.2f}` วินาที",
            inline=False,
        )
        result_embed.add_field(
            name="ความเร็วเฉลี่ย",
            value=f"`{average_speed:.2f}` ข้อความ/วินาที",
            inline=False,
        )
        result_embed.add_field(
            name="ระดับ",
            value="มาตรฐานระดับโปร",
            inline=False,
        )

        result_embed.set_footer(
            text="ข้อความนี้จะหายไปใน 60 วินาที",
            icon_url=self.bot.user.display_avatar.url,
        )

        await ctx.send(embed=result_embed, delete_after=60)

    @clear.error
    async def clear_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                description="❌ กรุณาระบุจำนวนเป็นตัวเลขเท่านั้น\n```!clear <จำนวน>```",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed, delete_after=8)
            try:
                await ctx.message.delete()
            except discord.HTTPException:
                pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Clear(bot))