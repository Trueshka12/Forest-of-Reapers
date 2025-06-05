LOG_CHANNEL_ID = 1376859187794939974  # глобально доступный ID лог-канала

import discord.ui as ui
import random
import discord
from discord.ext import commands

bot1 = commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot2 = commands.Bot(command_prefix='?', intents=discord.Intents.all())


import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
import time
TIMEOUT_DURATION = 1800  # 30 минут по умолчанию
import logging

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)


# Настройка логирования

verification_codes = {}  # перемещено
MENU_CHANNEL_ID = 1376868344850026516 # ← замените на настоящий ID канала

class VerificationModal(discord.ui.Modal, title="Верификация"):
    def __init__(self):
        super().__init__()
        self.code_input = discord.ui.TextInput(
            label="Введите число",
            placeholder="Введите число, указанное на кнопке",
            required=True,
            max_length=4
        )
        self.add_item(self.code_input)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        entered_code = self.code_input.value

        # Получаем правильный код из словаря
        expected_code = verification_codes.get(user_id)

        if not expected_code:
            await interaction.response.send_message("❌ Не найден код для верификации. Попробуйте снова.", ephemeral=True)
            return

        if entered_code == str(expected_code):
            # Выдача роли после верификации
            role_verified = discord.utils.get(interaction.guild.roles, name="User")
            role_unverified = discord.utils.get(interaction.guild.roles, name="unverify")
            if role_verified:
                await interaction.user.add_roles(role_verified)
                if role_unverified:
                    await interaction.user.remove_roles(role_unverified)
                await interaction.response.send_message("✅ Вы успешно верифицированы!", ephemeral=True)
            else:
                await interaction.response.send_message("⚠️ Роль 'User' не найдена.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Неверный код. Попробуйте ещё раз.", ephemeral=True)
class ApplicationModal(discord.ui.Modal):
    def __init__(self, composition: str):
        super().__init__(title=f"Заявка в {composition}")
        self.composition = composition

    age = discord.ui.TextInput(
        label="Сколько Вам Лет?",
        placeholder="Укажите ваш возраст...",
        required=True,
        max_length=3
    )
    
    clans_experience = discord.ui.TextInput(
        label="В Каких Кланах Вы Уже Были?",
        placeholder="Расскажите о своём опыте в кланах...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=4000
    )
    
    skills = discord.ui.TextInput(
        label="Что Вы Умеете?",
        placeholder="Расскажите о ваших навыках и умениях...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=4000
    )
    
    time_dedication = discord.ui.TextInput(
        label="Сколько Готовы Уделять Времени Клану?",
        placeholder="Сколько времени в день/неделю готовы уделять клану...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=4000
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = interaction.user.id
            now = datetime.utcnow()

            # Проверка кулдауна
            if user_id in last_application_times:
                delta = now - last_application_times[user_id]
                if delta < APPLICATION_COOLDOWN:
                    remaining = APPLICATION_COOLDOWN - delta
                    minutes = int(remaining.total_seconds() // 60)
                    seconds = int(remaining.total_seconds() % 60)
                    return await interaction.response.send_message(
                        f"⏳ Пожалуйста, подождите **{minutes}м {seconds}с** перед отправкой новой заявки.",
                        ephemeral=True
                    )

            last_application_times[user_id] = now

            # Отправка заявки в канал
            channel = bot1.get_channel(APPLICATION_CHANNEL_ID)
            if not channel:
                await interaction.response.send_message("❌ Канал для заявок не найден.", ephemeral=True)
                return

            embed = discord.Embed(
                title="📨 Новая заявка в клан",
                description=f"**Состав:** {self.composition}",
                color=discord.Color.blue()
            )
            embed.add_field(name="👤 Пользователь", value=f"{interaction.user.mention}\n`{interaction.user}`", inline=True)
            embed.add_field(name="🎂 Возраст", value=f"`{self.age.value}`", inline=True)
            embed.add_field(name="⏰ Время для клана", value=f"```{self.time_dedication.value[:500]}```", inline=True)
            embed.add_field(name="🏛️ Опыт в кланах", value=f"```{self.clans_experience.value[:800]}```", inline=False)
            embed.add_field(name="🛠️ Навыки и умения", value=f"```{self.skills.value[:800]}```", inline=False)
            
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.set_footer(text=f"ID: {interaction.user.id} • {now.strftime('%d.%m.%Y %H:%M')}")

            await channel.send(embed=embed, view=ModActionView(interaction.user, self.composition))

            # ЛС пользователю
            try:
                user_embed = discord.Embed(
                    title="✅ Заявка отправлена!",
                    description=f"Ваша заявка на **{self.composition}** успешно отправлена модераторам.",
                    color=discord.Color.green()
                )
                user_embed.add_field(name="📋 Что дальше?", 
                                   value="• Модераторы рассмотрят заявку\n• Вам придёт уведомление о решении\n• При принятии вы получите роль", 
                                   inline=False)
                await interaction.user.send(embed=user_embed)
            except Exception as e:
                logger.warning(f"Не удалось отправить ЛС: {e}")

            await interaction.response.send_message(
                f"✅ Заявка на **{self.composition}** отправлена! Проверьте ЛС для подтверждения.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке заявки: {e}")
            await interaction.response.send_message("❌ Произошла ошибка. Попробуйте позже.", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        logger.error(f"Ошибка в модальном окне: {error}")

# Кнопки Принять/Отклонить (для модераторов)
class ModActionView(discord.ui.View):
    def __init__(self, applicant: discord.Member, composition: str):
        super().__init__(timeout=None)
        self.applicant = applicant
        self.composition = composition

    @discord.ui.button(label="✅ Принять", style=discord.ButtonStyle.success, custom_id="mod_accept")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Обновляем embed с решением
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.green()
            embed.title = "✅ ЗАЯВКА ПРИНЯТА"
            embed.add_field(name="👨‍💼 Модератор", value=f"{interaction.user.mention}", inline=True)
            embed.add_field(name="📅 Время решения", value=f"<t:{int(datetime.utcnow().timestamp())}:R>", inline=True)
            
            await interaction.response.edit_message(embed=embed, view=None)
            
            try:
                accept_embed = discord.Embed(
                    title="🎉 Поздравляем! Заявка принята!",
                    description=f"Ваша заявка на **{self.composition}** была **принята**!",
                    color=discord.Color.green()
                )
                accept_embed.add_field(name="🎯 Следующие шаги", 
                                      value="• Вам выдана роль участника\n• Ознакомьтесь с правилами клана\n• Добро пожаловать в команду!", 
                                      inline=False)
                await self.applicant.send(embed=accept_embed)
            except Exception as e:
                logger.warning(f"Не удалось отправить ЛС при принятии: {e}")
                await interaction.followup.send("⚠️ Не удалось отправить сообщение в ЛС пользователю.", ephemeral=True)
        except Exception as e:
            logger.error(f"Ошибка при принятии заявки: {e}")

    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.danger, custom_id="mod_reject")
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RejectModal(self.applicant, self.composition, interaction.message))

    @discord.ui.button(label="❓ Запросить информацию", style=discord.ButtonStyle.secondary, custom_id="mod_info")
    async def info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(InfoRequestModal(self.applicant))

# Модальное окно для причины отклонения
class RejectModal(discord.ui.Modal):
    def __init__(self, applicant: discord.Member, composition: str, message):
        super().__init__(title="Причина отклонения")
        self.applicant = applicant
        self.composition = composition
        self.message = message

    reason = discord.ui.TextInput(
        label="Причина отклонения",
        placeholder="Укажите причину отклонения заявки...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Обновляем embed
            embed = self.message.embeds[0]
            embed.color = discord.Color.red()
            embed.title = "❌ ЗАЯВКА ОТКЛОНЕНА"
            embed.add_field(name="👨‍💼 Модератор", value=f"{interaction.user.mention}", inline=True)
            embed.add_field(name="📅 Время решения", value=f"<t:{int(datetime.utcnow().timestamp())}:R>", inline=True)
            embed.add_field(name="📝 Причина", value=f"```{self.reason.value}```", inline=False)
            
            await interaction.response.edit_message(embed=embed, view=None)
            
            try:
                reject_embed = discord.Embed(
                    title="😞 Заявка отклонена",
                    description=f"К сожалению, ваша заявка на **{self.composition}** была отклонена.",
                    color=discord.Color.red()
                )
                reject_embed.add_field(name="📝 Причина", value=f"```{self.reason.value}```", inline=False)
                reject_embed.add_field(name="🔄 Что делать дальше?", 
                                     value="• Учтите указанные замечания\n• Можете подать заявку повторно через 5 минут\n• Обратитесь к модераторам за советом", 
                                     inline=False)
                await self.applicant.send(embed=reject_embed)
            except Exception as e:
                logger.warning(f"Не удалось отправить ЛС при отклонении: {e}")
                await interaction.followup.send("⚠️ Не удалось отправить сообщение в ЛС пользователю.", ephemeral=True)
        except Exception as e:
            logger.error(f"Ошибка при отклонении заявки: {e}")

# Хранилище для активных вопросов модераторов
pending_questions = {}

# Модальное окно для запроса дополнительной информации
class InfoRequestModal(discord.ui.Modal):
    def __init__(self, applicant: discord.Member):
        super().__init__(title="Запрос информации")
        self.applicant = applicant

    question = discord.ui.TextInput(
        label="Вопрос к заявителю",
        placeholder="Введите вопрос или запрос дополнительной информации...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Генерируем уникальный ID для вопроса
            question_id = f"{self.applicant.id}_{int(datetime.utcnow().timestamp())}"
            
            # Сохраняем вопрос в базе данных
            pending_questions[question_id] = {
                "applicant": self.applicant,
                "moderator": interaction.user,
                "question": self.question.value,
                "timestamp": datetime.utcnow(),
                "guild": interaction.guild
            }
            
            info_embed = discord.Embed(
                title="❓ Запрос дополнительной информации",
                description="По вашей заявке нужна дополнительная информация:",
                color=discord.Color.orange()
            )
            info_embed.add_field(name="📝 Вопрос от модератора", value=f"```{self.question.value}```", inline=False)
            info_embed.add_field(name="💬 Как ответить?", 
                               value=f"Используйте команду: `!ответ {question_id} ваш ответ`\n"
                                     f"Например: `!ответ {question_id} Я люблю пить пивасик`", 
                               inline=False)
            info_embed.add_field(name="🆔 ID вопроса", value=f"`{question_id}`", inline=True)
            info_embed.set_footer(text="Скопируйте ID вопроса точно как показано выше")
            
            await self.applicant.send(embed=info_embed)
            await interaction.response.send_message(f"✅ Запрос отправлен пользователю {self.applicant.mention}\nID вопроса: `{question_id}`", ephemeral=True)
            
            # Логируем в канал модерации
            try:
                channel = bot1.get_channel(APPLICATION_CHANNEL_ID)
                if channel:
                    log_embed = discord.Embed(
                        title="📤 Отправлен запрос информации",
                        color=discord.Color.blue()
                    )
                    log_embed.add_field(name="👤 Пользователь", value=f"{self.applicant.mention}", inline=True)
                    log_embed.add_field(name="👨‍💼 Модератор", value=f"{interaction.user.mention}", inline=True)
                    log_embed.add_field(name="🆔 ID", value=f"`{question_id}`", inline=True)
                    log_embed.add_field(name="❓ Вопрос", value=f"```{self.question.value}```", inline=False)
                    await channel.send(embed=log_embed)
            except Exception as log_e:
                logger.warning(f"Не удалось залогировать запрос: {log_e}")
                
        except Exception as e:
            logger.error(f"Ошибка при запросе информации: {e}")
            await interaction.response.send_message("❌ Не удалось отправить сообщение пользователю.", ephemeral=True)

# Меню заявок (пользователь выбирает состав)
class ApplicationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="I Состав", style=discord.ButtonStyle.primary, emoji="🏆", custom_id="app_i_composition")
    async def i_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal("I — Лидирующий по силе состав"))

    @discord.ui.button(label="II Состав", style=discord.ButtonStyle.primary, emoji="⚔️", custom_id="app_ii_composition")
    async def ii_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal("II — Второй состав по силе"))

    @discord.ui.button(label="III Состав", style=discord.ButtonStyle.primary, emoji="🛡️", custom_id="app_iii_composition")
    async def iii_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal("III — Третий состав"))

    @discord.ui.button(label="IV Состав", style=discord.ButtonStyle.primary, emoji="💻", custom_id="app_iv_composition")
    async def iv_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal("IV — Кодеры, пентест, дизайнеры"))

    @discord.ui.button(label="Family", style=discord.ButtonStyle.secondary, emoji="🏠", custom_id="app_family_composition")
    async def family_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal("Family — Мирные"))


# === АНТИ-СПАМ НАСТРОЙКИ ===
MENTION_LIMIT = 5  # Лимит упоминаний в сообщении
SPAM_THRESHOLD = 5  # Кол-во сообщений за интервал
SPAM_INTERVAL = 10  # Интервал в секундах

from collections import defaultdict
user_message_log = defaultdict(list)

# === Заглушка для apply_strike ===
async def apply_strike(user, reason, guild):
    pass  # Здесь можно реализовать реальную систему страйков


@bot1.event
async def on_ready():
    logger.info(f"✅ Бот заявок запущен как {bot1.user}")
    print(f"✅ Бот заявок запущен как {bot1.user}")
    
    # Регистрируем персистентные View
    bot1.add_view(ApplicationView())
    
    # Автоматически создаем меню в канале при запуске
    try:
        channel = bot1.get_channel(MENU_CHANNEL_ID)
        if channel:
            # Проверяем, есть ли уже меню (ищем сообщения бота)
            async for message in channel.history(limit=50):
                if message.author == bot1.user and message.embeds:
                    embed = message.embeds[0]
                    if "Заявки в клан Forest of Reapers" in embed.title:
                        logger.info("📋 Меню заявок уже существует")
                        return
            
            # Создаем новое меню
            embed = discord.Embed(
                title="📋 Заявки в клан Forest of Reapers",
                description="""**Добро пожаловать!** 🌟

Заявки в клан **Forest of Reapers** открыты!

**🎯 Выберите подходящий состав:**

🏆 **I Состав** — Лидирующий по силе состав
Самый сильный состав клана , собранный из специалистов своего дела.
Максимально силён и опытен
⚔️ **II Состав** —  Второй состав по силе
Менее опытны чем первый состав, но так-же является очень сильным составом собранным из людей которые готовы развиваться и идти дальше к цели.  
🛡️ **III Состав** — Этот состав сформирован из людей которые хотят развиваться в своей сфере что-бы стать сильнее, выше, лучше и опытнее!
💻 **IV Состав** — Кодеры, пентест, дизайнеры и тд.
Тут находятся программисты , пентестеры , люди которые занимаются DDoS-атаками , дизайнеры и люди в подобных тому направлениях.
🏠 **Family** — Мирные участники

**📝 Процесс подачи заявки:**
1. Нажмите на кнопку нужного состава
2. Заполните форму с информацией о себе
3. Дождитесь рассмотрения модераторами
4. Получите уведомление о решении в ЛС

_Удачи в подаче заявки!_ ✨
""",
                color=discord.Color.blue()
            )
            embed.set_footer(text="Forest of Reapers • Система заявок")
            await channel.send(embed=embed, view=ApplicationView())
            logger.info("📋 Меню заявок автоматически создано")
        else:
            logger.warning(f"❌ Канал меню не найден: {MENU_CHANNEL_ID}")
    except Exception as e:
        logger.error(f"❌ Ошибка при создании меню: {e}")

@bot1.command()
@commands.has_permissions(administrator=True)
async def setup_menu(ctx):
    """Настройка меню заявок в текущем канале"""
    embed = discord.Embed(
        title="📋 Заявки в клан Forest of Reapers",
        description="""**Добро пожаловать!** 🌟

Заявки в клан **Forest of Reapers** открыты!

**🎯 Выберите подходящий состав:**

🏆 **I Состав** — Лидирующий по силе состав
Самый сильный состав клана , собранный из специалистов своего дела.
Максимально силён и опытен
⚔️ **II Состав** —  Второй состав по силе
Менее опытны чем первый состав, но так-же является очень сильным составом собранным из людей которые готовы развиваться и идти дальше к цели.  
🛡️ **III Состав** — Этот состав сформирован из людей которые хотят развиваться в своей сфере что-бы стать сильнее, выше, лучше и опытнее!
💻 **IV Состав** — Кодеры, пентест, дизайнеры и тд.
Тут находятся программисты , пентестеры , люди которые занимаются DDoS-атаками , дизайнеры и люди в подобных тому направлениях.
🏠 **Family** — Мирные участники

**📝 Процесс подачи заявки:**
1. Нажмите на кнопку нужного состава
2. Заполните форму с информацией о себе
3. Дождитесь рассмотрения модераторами
4. Получите уведомление о решении в ЛС

_Удачи в подаче заявки!_ ✨
""",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Forest of Reapers • Система заявок")
    msg = await ctx.send(embed=embed, view=ApplicationView())
    await ctx.send(f"✅ Меню заявок создано! ID сообщения: `{msg.id}`", delete_after=10)

@bot1.command()
@commands.has_permissions(moderate_members=True)
async def application_stats(ctx):
    """Статистика заявок"""
    total_apps = len(last_application_times)
    recent_apps = sum(1 for timestamp in last_application_times.values() 
                     if datetime.utcnow() - timestamp < timedelta(hours=24))
    
    embed = discord.Embed(
        title="📊 Статистика заявок",
        color=discord.Color.blue()
    )
    embed.add_field(name="📈 Всего заявок", value=f"`{total_apps}`", inline=True)
    embed.add_field(name="🕐 За последние 24ч", value=f"`{recent_apps}`", inline=True)
    embed.add_field(name="⏱️ Кулдаун", value=f"`{APPLICATION_COOLDOWN.total_seconds()//60} минут`", inline=True)
    
    await ctx.send(embed=embed)

@bot1.command()
@commands.has_permissions(administrator=True)
async def set_cooldown(ctx, minutes: int):
    """Изменить кулдаун между заявками"""
    global APPLICATION_COOLDOWN
    APPLICATION_COOLDOWN = timedelta(minutes=minutes)
    await ctx.send(f"✅ Кулдаун изменён на **{minutes} минут**")

@bot1.command()
@commands.has_permissions(administrator=True)
async def recreate_menu(ctx):
    """Пересоздать меню заявок в указанном канале"""
    try:
        channel = bot1.get_channel(MENU_CHANNEL_ID)
        if not channel:
            await ctx.send(f"❌ Канал не найден: {MENU_CHANNEL_ID}")
            return
        
        # Удаляем старые меню
        deleted_count = 0
        async for message in channel.history(limit=100):
            if message.author == bot1.user and message.embeds:
                embed = message.embeds[0]
                if "Заявки в клан Forest of Reapers" in embed.title:
                    await message.delete()
                    deleted_count += 1
        
        # Создаем новое меню
        embed = discord.Embed(
            title="📋 Заявки в клан Forest of Reapers",
            description="""**Добро пожаловать!** 🌟

Заявки в клан **Forest of Reapers** открыты!

**🎯 Выберите подходящий состав:**

🏆 **I Состав** — Лидирующий по силе состав
Самый сильный состав клана , собранный из специалистов своего дела.
Максимально силён и опытен
⚔️ **II Состав** —  Второй состав по силе
Менее опытны чем первый состав, но так-же является очень сильным составом собранным из людей которые готовы развиваться и идти дальше к цели.  
🛡️ **III Состав** — Этот состав сформирован из людей которые хотят развиваться в своей сфере что-бы стать сильнее, выше, лучше и опытнее!
💻 **IV Состав** — Кодеры, пентест, дизайнеры и тд.
Тут находятся программисты , пентестеры , люди которые занимаются DDoS-атаками , дизайнеры и люди в подобных тому направлениях.
🏠 **Family** — Мирные участники

**📝 Процесс подачи заявки:**
1. Нажмите на кнопку нужного состава
2. Заполните форму с информацией о себе
3. Дождитесь рассмотрения модераторами
4. Получите уведомление о решении в ЛС

_Удачи в подаче заявки!_ ✨
""",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Forest of Reapers • Система заявок")
        
        await channel.send(embed=embed, view=ApplicationView())
        await ctx.send(f"✅ Меню пересоздано! Удалено старых меню: {deleted_count}")
        
    except Exception as e:
        await ctx.send(f"❌ Ошибка при пересоздании меню: {e}")

@bot1.command()
@commands.has_permissions(moderate_members=True)
async def clear_cooldown(ctx, user: discord.Member):
    """Сбросить кулдаун для пользователя"""
    if user.id in last_application_times:
        del last_application_times[user.id]
        await ctx.send(f"✅ Кулдаун сброшен для {user.mention}")
    else:
        await ctx.send(f"❌ У {user.mention} нет активного кулдауна")

@bot1.command(name="ответ")
async def answer_question(ctx, question_id: str, *, answer: str):
    """Ответить на вопрос модератора"""
    try:
        # Проверяем, есть ли такой вопрос
        if question_id not in pending_questions:
            await ctx.send("❌ Вопрос с таким ID не найден или уже обработан.", delete_after=10)
            return
        
        question_data = pending_questions[question_id]
        
        # Проверяем, что отвечает правильный пользователь
        if ctx.author.id != question_data["applicant"].id:
            await ctx.send("❌ Вы можете отвечать только на свои вопросы.", delete_after=10)
            return
        
        # Отправляем ответ в канал заявок
        channel = bot1.get_channel(APPLICATION_CHANNEL_ID)
        if channel:
            response_embed = discord.Embed(
                title="💬 Получен ответ на вопрос",
                color=discord.Color.green()
            )
            response_embed.add_field(name="👤 Пользователь", value=f"{ctx.author.mention}", inline=True)
            response_embed.add_field(name="👨‍💼 Модератор задавший вопрос", value=f"{question_data['moderator'].mention}", inline=True)
            response_embed.add_field(name="🆔 ID вопроса", value=f"`{question_id}`", inline=True)
            response_embed.add_field(name="❓ Изначальный вопрос", value=f"```{question_data['question']}```", inline=False)
            response_embed.add_field(name="💬 Ответ пользователя", value=f"```{answer}```", inline=False)
            response_embed.set_thumbnail(url=ctx.author.display_avatar.url)
            response_embed.set_footer(text=f"Время ответа: {datetime.utcnow().strftime('%d.%m.%Y %H:%M')}")
            
            await channel.send(embed=response_embed)
        
        # Уведомляем модератора в ЛС
        try:
            mod_embed = discord.Embed(
                title="📬 Получен ответ на ваш вопрос",
                description=f"Пользователь {ctx.author.mention} ответил на ваш вопрос:",
                color=discord.Color.blue()
            )
            mod_embed.add_field(name="❓ Ваш вопрос", value=f"```{question_data['question']}```", inline=False)
            mod_embed.add_field(name="💬 Ответ", value=f"```{answer}```", inline=False)
            mod_embed.add_field(name="🔗 Сервер", value=f"{question_data['guild'].name}", inline=True)
            await question_data["moderator"].send(embed=mod_embed)
        except Exception as e:
            logger.warning(f"Не удалось отправить ЛС модератору: {e}")
        
        # Удаляем вопрос из ожидающих
        del pending_questions[question_id]
        
        await ctx.send("✅ Ваш ответ отправлен модераторам!", delete_after=10)
        
        # Удаляем команду пользователя для чистоты
        try:
            await ctx.message.delete()
        except:
            pass
            
    except Exception as e:
        logger.error(f"Ошибка при обработке ответа: {e}")
        await ctx.send("❌ Произошла ошибка при отправке ответа.", delete_after=10)

@bot1.command()
@commands.has_permissions(moderate_members=True)
async def pending_questions_list(ctx):
    """Показать список ожидающих ответа вопросов"""
    try:
        if not pending_questions:
            await ctx.send("📭 Нет ожидающих ответа вопросов.")
            return
        
        embed = discord.Embed(
            title="📋 Ожидающие ответа вопросы",
            description=f"Всего вопросов: {len(pending_questions)}",
            color=discord.Color.orange()
        )
        
        count = 0
        for question_id, data in pending_questions.items():
            if count >= 10:  # Ограничиваем количество для читаемости
                embed.add_field(name="⚠️", value=f"И ещё {len(pending_questions) - 10} вопросов...", inline=False)
                break
                
            time_ago = datetime.utcnow() - data["timestamp"]
            hours = int(time_ago.total_seconds() // 3600)
            minutes = int((time_ago.total_seconds() % 3600) // 60)
            
            embed.add_field(
                name=f"🆔 {question_id}",
                value=f"👤 {data['applicant'].display_name}\n"
                      f"👨‍💼 {data['moderator'].display_name}\n"
                      f"⏰ {hours}ч {minutes}м назад\n"
                      f"❓ {data['question'][:50]}{'...' if len(data['question']) > 50 else ''}",
                inline=True
            )
            count += 1
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Ошибка при получении списка вопросов: {e}")
        await ctx.send("❌ Ошибка при получении списка вопросов.")

@bot1.command()
@commands.has_permissions(moderate_members=True)
async def remove_question(ctx, question_id: str):
    """Удалить вопрос из ожидающих (если больше не актуален)"""
    try:
        if question_id not in pending_questions:
            await ctx.send("❌ Вопрос с таким ID не найден.")
            return
        
        question_data = pending_questions[question_id]
        del pending_questions[question_id]
        
        embed = discord.Embed(
            title="🗑️ Вопрос удален",
            description=f"Вопрос к {question_data['applicant'].mention} удален из ожидающих",
            color=discord.Color.red()
        )
        embed.add_field(name="❓ Удаленный вопрос", value=f"```{question_data['question']}```", inline=False)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Ошибка при удалении вопроса: {e}")
        await ctx.send("❌ Ошибка при удалении вопроса.")

@bot1.command()
@commands.has_permissions(administrator=True)
async def status(ctx):
    """Проверить статус бота"""
    embed = discord.Embed(
        title="🤖 Статус бота заявок",
        color=discord.Color.green()
    )
    embed.add_field(name="📊 Состояние", value="✅ Онлайн", inline=True)
    embed.add_field(name="🏓 Пинг", value=f"`{round(bot1.latency * 1000)}ms`", inline=True)
    embed.add_field(name="🔗 Серверы", value=f"`{len(bot1.guilds)}`", inline=True)
    await ctx.send(embed=embed)

# === ВТОРОЙ БОТ - МОДЕРАЦИЯ ===

class VerifyButton(ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Обязательно для persistent view

    @ui.button(label="Пройти верификацию", style=discord.ButtonStyle.success, custom_id="verify_button")
    async def verify(self, interaction: discord.Interaction, button: ui.Button):
        code = random.randint(1000, 9999)
        verification_codes[interaction.user.id] = code
        modal = VerificationModal()
        modal.code_input.label = f"Введите число: {code}"
        if not interaction.response.is_done():
            await interaction.response.send_modal(modal)

@bot2.command()
@commands.has_permissions(administrator=True)
async def verify_setup(ctx):
    embed = discord.Embed(
        title="🛡️ Верификация",
        description="Нажмите кнопку ниже и введите указанное число, чтобы получить доступ к серверу.",
        color=discord.Color.green()
    )
    embed.set_image(url="https://cdn.discordapp.com/attachments/900731112811290655/1378050895337623693/Frame_2.png?ex=683b3168&is=6839dfe8&hm=2edef35f12ce2aa3f7ae23cab0369e6d52726d00f88857edcdaec6b51a6b69f7&")
    await ctx.send(embed=embed, view=VerifyButton())


@bot2.event
async def on_ready():
    logger.info(f"✅ Бот модерации запущен как {bot2.user}")
    print(f"✅ Бот модерации запущен как {bot2.user}")
    bot2.add_view(VerifyButton())  # Регистрируем кнопку

    # === АВТО-СОЗДАНИЕ МЕНЮ ВЕРИФИКАЦИИ ===
    VERIFY_MENU_CHANNEL_ID = 1378032629680574546 # Заменить при необходимости

    try:
        channel = bot2.get_channel(VERIFY_MENU_CHANNEL_ID)
        if channel:
            async for message in channel.history(limit=50):
                if message.author == bot2.user and message.embeds:
                    embed = message.embeds[0]
                    if "Верификация" in embed.title:
                        logger.info("🛡️ Меню верификации уже существует")
                        return

            embed = discord.Embed(
                title="🛡️ Верификация",
                description="Нажмите кнопку ниже и введите указанное число, чтобы получить доступ к серверу.",
                color=discord.Color.green()
            )
            embed.set_image(url="https://cdn.discordapp.com/attachments/900731112811290655/1378050895337623693/Frame_2.png?ex=683b3168&is=6839dfe8&hm=2edef35f12ce2aa3f7ae23cab0369e6d52726d00f88857edcdaec6b51a6b69f7&")
            await channel.send(embed=embed, view=VerifyButton())
            logger.info("🛡️ Меню верификации создано автоматически")
        else:
            logger.warning(f"❌ Канал с ID {VERIFY_MENU_CHANNEL_ID} не найден.")
    except Exception as e:
        logger.error(f"❌ Ошибка при создании меню верификации: {e}")

@bot2.event


async def on_message(message):
    """Улучшенная обработка сообщений с антикраш системой"""
    if message.author.bot:
        return

    try:
        # Проверяем базовые условия
        if not message.guild:
            return  # Игнорируем ЛС
            
        if not isinstance(message.author, discord.Member):
            logger.warning(f"⚠️ Автор сообщения не является участником сервера: {message.author}")
            return

        author = message.author
        content = message.content.lower()

        # Проверяем права модератора (модераторы освобождены от фильтров)
        if author.guild_permissions.moderate_members or author.guild_permissions.administrator:
            await bot2.process_commands(message)
            return

        # === АНТИ-@EVERYONE И @HERE ===
        try:
            if "@everyone" in content or "@here" in content:
                await handle_violation(message, author, "Попытка упомянуть @everyone / @here")
                return
        except Exception as e:
            logger.error(f"❌ Ошибка в анти-@everyone: {e}")

        # === АНТИ-ССЫЛКИ ===
        try:
            if any(bad in content for bad in ["discord.gg/", "discord.com"]) and not any(allowed in content for allowed in ["tenor.com", "imgur.com"]):
                await handle_violation(message, author, "Отправка ссылок запрещена")
                return
        except Exception as e:
            logger.error(f"❌ Ошибка в анти-ссылки: {e}")

        # === АНТИ-ПИНГ ===
        try:
            if len(message.mentions) >= MENTION_LIMIT:
                mention_users = [f"{user.display_name}" for user in message.mentions[:3]]
                await handle_violation(message, author, f"Массовое упоминание ({len(message.mentions)} пользователей: {', '.join(mention_users)}...)")
                return
        except Exception as e:
            logger.error(f"❌ Ошибка в анти-пинг: {e}")

        # === АНТИ-ОПАСНЫЕ ВЛОЖЕНИЯ ===
        try:
            dangerous_exts = [".exe", ".bat", ".scr", ".cmd", ".js"]
            for attachment in message.attachments:
                if any(attachment.filename.lower().endswith(ext) for ext in dangerous_exts):
                    await handle_violation(message, author, f"Опасное вложение: {attachment.filename}")
                    return
        except Exception as e:
            logger.error(f"❌ Ошибка в анти-вложения: {e}")


        # === АНТИ-СПАМ ===
        try:
            now = time.time()
            user_log = user_message_log[author.id]
            user_log.append(now)
            
            # Очищаем старые записи
            user_message_log[author.id] = [t for t in user_log if now - t <= SPAM_INTERVAL]

            if len(user_message_log[author.id]) > SPAM_THRESHOLD:
                await handle_violation(message, author, f"Спам: {len(user_message_log[author.id])} сообщений за {SPAM_INTERVAL} сек")
                user_message_log[author.id] = []  # Сбрасываем счетчик
                return
        except Exception as e:
            logger.error(f"❌ Ошибка в анти-спам: {e}")
            # Сбрасываем счетчик при ошибке чтобы избежать накопления
            try:
                user_message_log[author.id] = []
            except:
                pass

        # === АНТИ-КАПС (дополнительная защита) ===
        try:
            if len(content) > 10:  # Проверяем только длинные сообщения
                caps_count = sum(1 for char in message.content if char.isupper())
                caps_ratio = caps_count / len(message.content)
                
                if caps_ratio > 0.7 and caps_count > 15:  # 70% заглавных букв
                    await handle_violation(message, author, f"Злоупотребление заглавными буквами ({caps_count} из {len(message.content)})")
                    return
        except Exception as e:
            logger.error(f"❌ Ошибка в анти-капс: {e}")

        # Обрабатываем команды если все проверки пройдены
        await bot2.process_commands(message)
        
    except discord.Forbidden:
        logger.warning(f"⚠️ Нет прав для обработки сообщения от {message.author}")
    except discord.HTTPException as e:
        logger.error(f"❌ HTTP ошибка при обработке сообщения: {e}")
    except Exception as e:
        import traceback
        logger.error(f"❌ Критическая ошибка в обработке сообщения от {message.author}: {e}")
        logger.error(f"Трейсбек: {traceback.format_exc()}")
        
        # Пытаемся залогировать критическую ошибку в Discord
        try:
            if message.guild:
                log_channel = message.guild.get_channel(LOG_CHANNEL_ID)
                if log_channel:
                    error_embed = discord.Embed(
                        title="💥 Критическая ошибка модерации",
                        description="Произошла критическая ошибка при обработке сообщения",
                        color=discord.Color.red()
                    )
                    error_embed.add_field(name="👤 Автор", value=f"{message.author.mention}", inline=True)
                    error_embed.add_field(name="📍 Канал", value=f"{message.channel.mention}", inline=True)
                    error_embed.add_field(name="🔥 Ошибка", value=f"```{str(e)[:500]}```", inline=False)
                    error_embed.timestamp = discord.utils.utcnow()
                    await log_channel.send(embed=error_embed)
        except Exception as log_error:
            logger.error(f"❌ Не удалось залогировать критическую ошибку: {log_error}")

# === УЛУЧШЕННАЯ ОБРАБОТКА НАРУШЕНИЙ ===
async def handle_violation(message, user, reason):
    """Улучшенная обработка нарушений с детальным логированием"""
    deletion_success = False
    timeout_success = False
    log_success = False
    
    # Попытка удалить сообщение
    try:
        await message.delete()
        deletion_success = True
        logger.info(f"✅ Сообщение удалено: {user} - {reason}")
    except discord.NotFound:
        logger.warning(f"⚠️ Сообщение уже удалено: {user}")
        deletion_success = True  # Считаем успехом, так как цель достигнута
    except discord.Forbidden:
        logger.error(f"❌ Нет прав для удаления сообщения: {user}")
    except Exception as e:
        logger.error(f"❌ Неизвестная ошибка при удалении: {e}")
    
    # Попытка выдать тайм-аут
    try:
        timeout_success = await timeout_user(user, reason)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при тайм-ауте: {e}")
    
    # Попытка залогировать нарушение
    try:
        log_success = await log_violation(message.guild, user, reason, message.content, deletion_success, timeout_success)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при логировании: {e}")
    
    # Итоговое логирование результата
    logger.info(f"📊 Обработка нарушения завершена: {user} | Удаление: {deletion_success} | Тайм-аут: {timeout_success} | Лог: {log_success}")
    await apply_strike(user, reason, message.guild)

async def timeout_user(member: discord.Member, reason="Нарушение", duration=TIMEOUT_DURATION):
    """Улучшенная функция выдачи тайм-аута с возвратом статуса"""
    try:
        # Проверяем, можем ли мы управлять этим пользователем
        if member.guild_permissions.administrator:
            logger.warning(f"⚠️ Попытка замутить администратора: {member}")
            return False
            
        if member.top_role >= member.guild.me.top_role:
            logger.warning(f"⚠️ Роль пользователя выше роли бота: {member}")
            return False
        
        until = discord.utils.utcnow() + timedelta(seconds=duration)
        await member.timeout(until, reason=reason)
        logger.info(f"⏳ Тайм-аут выдан {member}: {reason} (на {duration//60} мин)")
        return True
        
    except discord.Forbidden:
        logger.warning(f"❌ Нет прав для выдачи тайм-аута: {member}")
        return False
    except discord.HTTPException as e:
        logger.error(f"❌ HTTP ошибка при тайм-ауте: {e}")
        return False
    except Exception as e:
        logger.error(f"⚠️ Неизвестная ошибка при тайм-ауте: {e}")
        return False

async def log_violation(guild, user, reason, msg_content="", deletion_success=True, timeout_success=True):
    try:
        channel = bot2.get_channel(LOG_CHANNEL_ID)
        if not channel or (guild and channel.guild.id != guild.id):
            logger.warning("Лог-канал не найден или не соответствует серверу.")
            return False

        embed = discord.Embed(title="Нарушение", color=0xff0000)
        embed.add_field(name="Пользователь", value=str(user), inline=True)
        embed.add_field(name="Причина", value=reason, inline=True)

        status = "Удаление: " + ("✅" if deletion_success else "❌") + " | Тайм-аут: " + ("✅" if timeout_success else "❌")
        embed.add_field(name="Статус", value=status, inline=True)

        if msg_content.strip():
            embed.add_field(name="Сообщение", value=msg_content[:1000], inline=False)

        embed.set_footer(text="Модерация: " + guild.name)

        await channel.send(embed=embed)
        logger.info("Залогировано нарушение от " + str(user))
        return True

    except Exception as e:
        logger.error("Ошибка при логировании: " + str(e))
        return False
            
        # Создаем детальный embed
        embed = discord.Embed(title="🚨 Нарушение обнаружено", color=0xff0000)
        embed.add_field(name="👤 Пользователь", value=f"{user.mention}\n`{user}` (ID: {user.id})", inline=True)
        embed.add_field(name="🚨 Причина", value=f"```{reason}```", inline=True)
        embed.add_field(name="📊 Статус действий", 
                       value=f"🗑️ Удаление: {'✅' if deletion_success else '❌'}\n"
                             f"⏳ Тайм-аут: {'✅' if timeout_success else '❌'}", 
                       inline=True)
        
        if msg_content and len(msg_content.strip()) > 0:
            # Обрезаем сообщение если оно слишком длинное
            content_preview = msg_content[:800] + "..." if len(msg_content) > 800 else msg_content
            embed.add_field(name="📝 Содержимое сообщения", value=f"```{content_preview}```", inline=False)
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Система модерации • {guild.name}")
        embed.timestamp = discord.utils.utcnow()
        
        await channel.send(embed=embed)
        logger.info(f"📝 Нарушение залогировано: {user}")
        return True
        
    except discord.Forbidden:
        logger.error(f"❌ Нет прав для отправки в лог-канал")
        return False
    except discord.HTTPException as e:
        logger.error(f"❌ HTTP ошибка при логировании: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Неизвестная ошибка при логировании: {e}")
        return False

# === КОМАНДЫ МОДЕРАЦИИ ===

@bot2.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, minutes: int = 30, *, reason="Без причины"):
    """Выдать тайм-аут пользователю"""
    try:
        duration = minutes * 60
        await timeout_user(member, reason, duration)
        await ctx.send(f"⏳ {member.mention} получил тайм-аут на {minutes} минут. Причина: {reason}")
        await log_violation(ctx.guild, member, f"Командный тайм-аут: {reason}")
    except Exception as e:
        await ctx.send(f"❌ Ошибка: {e}")

@bot2.command()
@commands.has_permissions(moderate_members=True)
async def untimeout(ctx, member: discord.Member):
    """Снять тайм-аут с пользователя"""
    try:
        await member.timeout(None)
        await ctx.send(f"✅ Тайм-аут снят с {member.mention}")
    except Exception as e:
        await ctx.send(f"❌ Ошибка при снятии тайм-аута: {e}")

@bot2.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    """Очистить сообщения в канале"""
    try:
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 чтобы удалить команду
        await ctx.send(f"🧹 Удалено {len(deleted) - 1} сообщений.", delete_after=5)
    except Exception as e:
        await ctx.send(f"❌ Ошибка при очистке: {e}")

@bot2.command()
@commands.has_permissions(moderate_members=True)
async def warn(ctx, member: discord.Member, *, reason="Без причины"):
    """Выдать предупреждение"""
    try:
        await ctx.send(f"⚠️ {member.mention} получил предупреждение. Причина: {reason}")
        await log_violation(ctx.guild, member, f"Предупреждение: {reason}")
    except Exception as e:
        await ctx.send(f"❌ Ошибка: {e}")

@bot2.command()
@commands.has_permissions(administrator=True)
async def status(ctx):
    """Расширенная проверка статуса бота модерации"""
    try:
        # Подсчет активных пользователей в спам-логе
        active_users = len([user_id for user_id, timestamps in user_message_log.items() if timestamps])
        
        # Проверка лог-канала
        log_channel = ctx.guild.get_channel(LOG_CHANNEL_ID)
        log_status = "✅ Доступен" if log_channel else "❌ Не найден"
        
        embed = discord.Embed(
            title="🤖 Расширенный статус системы модерации",
            description="Детальная информация о работе бота",
            color=discord.Color.green()
        )
        embed.add_field(name="📊 Состояние", value="✅ Онлайн", inline=True)
        embed.add_field(name="🏓 Пинг", value=f"`{round(bot2.latency * 1000)}ms`", inline=True)
        embed.add_field(name="🔗 Серверы", value=f"`{len(bot2.guilds)}`", inline=True)
        
        embed.add_field(name="📝 Лог-канал", value=log_status, inline=True)
        embed.add_field(name="👥 Активных пользователей", value=f"`{active_users}`", inline=True)
        embed.add_field(name="⚙️ Модули", value="✅ Все активны", inline=True)
        
        embed.add_field(name="🛡️ Настройки защиты", 
                       value=f"• Лимит упоминаний: `{MENTION_LIMIT}`\n"
                             f"• Порог спама: `{SPAM_THRESHOLD} за {SPAM_INTERVAL}с`\n"
                             f"• Тайм-аут: `{TIMEOUT_DURATION//60} минут`", 
                       inline=False)
        
        embed.set_footer(text=f"Бот запущен • ID: {bot2.user.id}")
        embed.timestamp = discord.utils.utcnow()
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"❌ Ошибка в команде status: {e}")
        await ctx.send("❌ Ошибка при получении статуса системы")

@bot2.command()
@commands.has_permissions(moderate_members=True)
async def antispam_stats(ctx):
    """Статистика анти-спам системы"""
    try:
        if not user_message_log:
            await ctx.send("📊 Анти-спам лог пуст")
            return
            
        total_tracked = len(user_message_log)
        active_now = len([uid for uid, msgs in user_message_log.items() if msgs])
        
        embed = discord.Embed(
            title="📊 Статистика анти-спам системы",
            color=discord.Color.blue()
        )
        embed.add_field(name="👥 Всего отслеживается", value=f"`{total_tracked}`", inline=True)
        embed.add_field(name="🔥 Активны сейчас", value=f"`{active_now}`", inline=True)
        embed.add_field(name="⚙️ Интервал", value=f"`{SPAM_INTERVAL}с`", inline=True)
        
        # Топ самых активных (последние 5)
        if active_now > 0:
            top_users = sorted(
                [(uid, len(msgs)) for uid, msgs in user_message_log.items() if msgs],
                key=lambda x: x[1], reverse=True
            )[:5]
            
            top_text = ""
            for uid, count in top_users:
                try:
                    user = ctx.guild.get_member(uid)
                    name = user.display_name if user else f"ID:{uid}"
                    top_text += f"• {name}: `{count}` сообщений\n"
                except:
                    top_text += f"• ID:{uid}: `{count}` сообщений\n"
                    
            embed.add_field(name="🔥 Самые активные", value=top_text or "Нет данных", inline=False)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"❌ Ошибка в antispam_stats: {e}")
        await ctx.send("❌ Ошибка при получении статистики")

@bot2.command()
@commands.has_permissions(administrator=True)
async def clear_spam_log(ctx):
    """Очистить лог анти-спам системы"""
    try:
        old_count = len(user_message_log)
        user_message_log.clear()
        await ctx.send(f"🧹 Лог анти-спам очищен! Удалено записей: `{old_count}`")
        logger.info(f"Лог анти-спам очищен администратором {ctx.author}")
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке лога: {e}")
        await ctx.send("❌ Ошибка при очистке лога")

# === ФУНКЦИЯ ЗАПУСКА С АВТОМАТИЧЕСКИМ ПЕРЕЗАПУСКОМ ===
async def run_bot1_with_restart(bot1, token, name):
    """Запуск бота с автоматическим перезапуском при ошибках"""
    while True:
        try:
            logger.info(f"🚀 Запуск {name}...")
            await bot1.start(token)
        except discord.LoginFailure:
            logger.error(f"❌ Неверный токен для {name}")
            break
        except Exception as e:
            logger.error(f"❌ {name} упал с ошибкой: {e}")
            logger.info(f"🔄 Перезапуск {name} через 5 секунд...")
            await asyncio.sleep(5)
        finally:
            if not bot1.is_closed():
                await bot1.close()

# === ЗАПУСК ОБОИХ БОТОВ ===

@bot2.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name="unverify")
    if role:
        await member.add_roles(role)
        logger.info(f"✅ Выдана роль 'unverify' пользователю {member}")


async def main():
    """Главная функция запуска"""
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(run_bot1_with_restart(
                bot1, 
                "MTM3Njg3NjM5Mjc2MzEwMTI5Ng.GeBnqx.JlvnY-fv2sbjxoPAlyrYJkX6jNW2n5VTER908k",
                "Бот заявок"
            ))
            tg.create_task(run_bot1_with_restart(
                bot2, 
                "MTM3Njg1ODQxMTk0MTEwNTY5NA.GOXnKn.OZ1O8z4vvc4UD6FB23bIr1V81qyjNbgnCDdyFc",
                "Бот модерации"
            ))
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        logger.info("Перезапуск через 10 секунд...")
        await asyncio.sleep(10)
        await main()

if __name__ == "__main__":
    logger.info("🎯 Запуск системы ботов...")
    asyncio.run(main())





import random

verification_codes = {}


class VerifyButton(ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Обязательно для persistent view

    @ui.button(label="Пройти верификацию", style=discord.ButtonStyle.success, custom_id="verify_button")
    async def verify(self, interaction: discord.Interaction, button: ui.Button):
        code = random.randint(1000, 9999)
        verification_codes[interaction.user.id] = code
        modal = VerificationModal()
        modal.code_input.label = f"Введите число: {code}"
        if not interaction.response.is_done():
            await interaction.response.send_modal(modal)

@bot2.command()
@commands.has_permissions(administrator=True)
async def verify_setup(ctx):
    embed = discord.Embed(
        title="🛡️ Верификация",
        description="Нажмите кнопку ниже и введите указанное число, чтобы получить доступ к серверу.",
        color=discord.Color.green()
    )
    embed.set_image(url="https://cdn.discordapp.com/attachments/900731112811290655/1378050895337623693/Frame_2.png?ex=683b3168&is=6839dfe8&hm=2edef35f12ce2aa3f7ae23cab0369e6d52726d00f88857edcdaec6b51a6b69f7&")
    await ctx.send(embed=embed, view=VerifyButton())


@bot2.event
async def on_ready():
    logger.info(f"✅ Бот модерации запущен как {bot2.user}")
    print(f"✅ Бот модерации запущен как {bot2.user}")
    bot2.add_view(VerifyButton())  # Регистрируем кнопку

    # === АВТО-СОЗДАНИЕ МЕНЮ ВЕРИФИКАЦИИ ===
    VERIFY_MENU_CHANNEL_ID = 1378032629680574546  # Заменить при необходимости

    try:
        channel = bot2.get_channel(VERIFY_MENU_CHANNEL_ID)
        if channel:
            async for message in channel.history(limit=50):
                if message.author == bot2.user and message.embeds:
                    embed = message.embeds[0]
                    if "Верификация" in embed.title:
                        logger.info("🛡️ Меню верификации уже существует")
                        return

            embed = discord.Embed(
                title="🛡️ Верификация",
                description="Нажмите кнопку ниже и введите указанное число, чтобы получить доступ к серверу.",
                color=discord.Color.green()
            )
            embed.set_image(url="https://cdn.discordapp.com/attachments/900731112811290655/1378050895337623693/Frame_2.png?ex=683b3168&is=6839dfe8&hm=2edef35f12ce2aa3f7ae23cab0369e6d52726d00f88857edcdaec6b51a6b69f7&")
            await channel.send(embed=embed, view=VerifyButton())
            logger.info("🛡️ Меню верификации создано автоматически")
        else:
            logger.warning(f"❌ Канал с ID {VERIFY_MENU_CHANNEL_ID} не найден.")
    except Exception as e:
        logger.error(f"❌ Ошибка при создании меню верификации: {e}")

@bot2.event


async def on_message(message):
    """Улучшенная обработка сообщений с антикраш системой"""
    if message.author.bot:
        return

    try:
        # Проверяем базовые условия
        if not message.guild:
            return  # Игнорируем ЛС
            
        if not isinstance(message.author, discord.Member):
            logger.warning(f"⚠️ Автор сообщения не является участником сервера: {message.author}")
            return

        author = message.author
        content = message.content.lower()

        # Проверяем права модератора (модераторы освобождены от фильтров)
        if author.guild_permissions.moderate_members or author.guild_permissions.administrator:
            await bot2.process_commands(message)
            return

        # === АНТИ-@EVERYONE И @HERE ===
        try:
            if "@everyone" in content or "@here" in content:
                await handle_violation(message, author, "Попытка упомянуть @everyone / @here")
                return
        except Exception as e:
            logger.error(f"❌ Ошибка в анти-@everyone: {e}")

        # === АНТИ-ССЫЛКИ ===
        try:
            if any(bad in content for bad in ["discord.gg/", "discord.com"]) and not any(allowed in content for allowed in ["tenor.com", "imgur.com"]):
                await handle_violation(message, author, "Отправка ссылок запрещена")
                return
        except Exception as e:
            logger.error(f"❌ Ошибка в анти-ссылки: {e}")

        # === АНТИ-ПИНГ ===
        try:
            if len(message.mentions) >= MENTION_LIMIT:
                mention_users = [f"{user.display_name}" for user in message.mentions[:3]]
                await handle_violation(message, author, f"Массовое упоминание ({len(message.mentions)} пользователей: {', '.join(mention_users)}...)")
                return
        except Exception as e:
            logger.error(f"❌ Ошибка в анти-пинг: {e}")

        # === АНТИ-ОПАСНЫЕ ВЛОЖЕНИЯ ===
        try:
            dangerous_exts = [".exe", ".bat", ".scr", ".cmd", ".js"]
            for attachment in message.attachments:
                if any(attachment.filename.lower().endswith(ext) for ext in dangerous_exts):
                    await handle_violation(message, author, f"Опасное вложение: {attachment.filename}")
                    return
        except Exception as e:
            logger.error(f"❌ Ошибка в анти-вложения: {e}")


        # === АНТИ-СПАМ ===
        try:
            now = time.time()
            user_log = user_message_log[author.id]
            user_log.append(now)
            
            # Очищаем старые записи
            user_message_log[author.id] = [t for t in user_log if now - t <= SPAM_INTERVAL]

            if len(user_message_log[author.id]) > SPAM_THRESHOLD:
                await handle_violation(message, author, f"Спам: {len(user_message_log[author.id])} сообщений за {SPAM_INTERVAL} сек")
                user_message_log[author.id] = []  # Сбрасываем счетчик
                return
        except Exception as e:
            logger.error(f"❌ Ошибка в анти-спам: {e}")
            # Сбрасываем счетчик при ошибке чтобы избежать накопления
            try:
                user_message_log[author.id] = []
            except:
                pass

        # === АНТИ-КАПС (дополнительная защита) ===
        try:
            if len(content) > 10:  # Проверяем только длинные сообщения
                caps_count = sum(1 for char in message.content if char.isupper())
                caps_ratio = caps_count / len(message.content)
                
                if caps_ratio > 0.7 and caps_count > 15:  # 70% заглавных букв
                    await handle_violation(message, author, f"Злоупотребление заглавными буквами ({caps_count} из {len(message.content)})")
                    return
        except Exception as e:
            logger.error(f"❌ Ошибка в анти-капс: {e}")

        # Обрабатываем команды если все проверки пройдены
        await bot2.process_commands(message)
        
    except discord.Forbidden:
        logger.warning(f"⚠️ Нет прав для обработки сообщения от {message.author}")
    except discord.HTTPException as e:
        logger.error(f"❌ HTTP ошибка при обработке сообщения: {e}")
    except Exception as e:
        import traceback
        logger.error(f"❌ Критическая ошибка в обработке сообщения от {message.author}: {e}")
        logger.error(f"Трейсбек: {traceback.format_exc()}")
        
        # Пытаемся залогировать критическую ошибку в Discord
        try:
            if message.guild:
                log_channel = message.guild.get_channel(LOG_CHANNEL_ID)
                if log_channel:
                    error_embed = discord.Embed(
                        title="💥 Критическая ошибка модерации",
                        description="Произошла критическая ошибка при обработке сообщения",
                        color=discord.Color.red()
                    )
                    error_embed.add_field(name="👤 Автор", value=f"{message.author.mention}", inline=True)
                    error_embed.add_field(name="📍 Канал", value=f"{message.channel.mention}", inline=True)
                    error_embed.add_field(name="🔥 Ошибка", value=f"```{str(e)[:500]}```", inline=False)
                    error_embed.timestamp = discord.utils.utcnow()
                    await log_channel.send(embed=error_embed)
        except Exception as log_error:
            logger.error(f"❌ Не удалось залогировать критическую ошибку: {log_error}")

# === УЛУЧШЕННАЯ ОБРАБОТКА НАРУШЕНИЙ ===
async def handle_violation(message, user, reason):
    """Улучшенная обработка нарушений с детальным логированием"""
    deletion_success = False
    timeout_success = False
    log_success = False
    
    # Попытка удалить сообщение
    try:
        await message.delete()
        deletion_success = True
        logger.info(f"✅ Сообщение удалено: {user} - {reason}")
    except discord.NotFound:
        logger.warning(f"⚠️ Сообщение уже удалено: {user}")
        deletion_success = True  # Считаем успехом, так как цель достигнута
    except discord.Forbidden:
        logger.error(f"❌ Нет прав для удаления сообщения: {user}")
    except Exception as e:
        logger.error(f"❌ Неизвестная ошибка при удалении: {e}")
    
    # Попытка выдать тайм-аут
    try:
        timeout_success = await timeout_user(user, reason)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при тайм-ауте: {e}")
    
    # Попытка залогировать нарушение
    try:
        log_success = await log_violation(message.guild, user, reason, message.content, deletion_success, timeout_success)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при логировании: {e}")
    
    # Итоговое логирование результата
    logger.info(f"📊 Обработка нарушения завершена: {user} | Удаление: {deletion_success} | Тайм-аут: {timeout_success} | Лог: {log_success}")
    await apply_strike(user, reason, message.guild)

async def timeout_user(member: discord.Member, reason="Нарушение", duration=TIMEOUT_DURATION):
    """Улучшенная функция выдачи тайм-аута с возвратом статуса"""
    try:
        # Проверяем, можем ли мы управлять этим пользователем
        if member.guild_permissions.administrator:
            logger.warning(f"⚠️ Попытка замутить администратора: {member}")
            return False
            
        if member.top_role >= member.guild.me.top_role:
            logger.warning(f"⚠️ Роль пользователя выше роли бота: {member}")
            return False
        
        until = discord.utils.utcnow() + timedelta(seconds=duration)
        await member.timeout(until, reason=reason)
        logger.info(f"⏳ Тайм-аут выдан {member}: {reason} (на {duration//60} мин)")
        return True
        
    except discord.Forbidden:
        logger.warning(f"❌ Нет прав для выдачи тайм-аута: {member}")
        return False
    except discord.HTTPException as e:
        logger.error(f"❌ HTTP ошибка при тайм-ауте: {e}")
        return False
    except Exception as e:
        logger.error(f"⚠️ Неизвестная ошибка при тайм-ауте: {e}")
        return False

async def log_violation(guild, user, reason, msg_content="", deletion_success=True, timeout_success=True):
    try:
        channel = bot2.get_channel(LOG_CHANNEL_ID)
        if not channel or (guild and channel.guild.id != guild.id):
            logger.warning("Лог-канал не найден или не соответствует серверу.")
            return False

        embed = discord.Embed(title="Нарушение", color=0xff0000)
        embed.add_field(name="Пользователь", value=str(user), inline=True)
        embed.add_field(name="Причина", value=reason, inline=True)

        status = "Удаление: " + ("✅" if deletion_success else "❌") + " | Тайм-аут: " + ("✅" if timeout_success else "❌")
        embed.add_field(name="Статус", value=status, inline=True)

        if msg_content.strip():
            embed.add_field(name="Сообщение", value=msg_content[:1000], inline=False)

        embed.set_footer(text="Модерация: " + guild.name)

        await channel.send(embed=embed)
        logger.info("Залогировано нарушение от " + str(user))
        return True

    except Exception as e:
        logger.error("Ошибка при логировании: " + str(e))
        return False
            
        # Создаем детальный embed
        embed = discord.Embed(title="🚨 Нарушение обнаружено", color=0xff0000)
        embed.add_field(name="👤 Пользователь", value=f"{user.mention}\n`{user}` (ID: {user.id})", inline=True)
        embed.add_field(name="🚨 Причина", value=f"```{reason}```", inline=True)
        embed.add_field(name="📊 Статус действий", 
                       value=f"🗑️ Удаление: {'✅' if deletion_success else '❌'}\n"
                             f"⏳ Тайм-аут: {'✅' if timeout_success else '❌'}", 
                       inline=True)
        
        if msg_content and len(msg_content.strip()) > 0:
            # Обрезаем сообщение если оно слишком длинное
            content_preview = msg_content[:800] + "..." if len(msg_content) > 800 else msg_content
            embed.add_field(name="📝 Содержимое сообщения", value=f"```{content_preview}```", inline=False)
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Система модерации • {guild.name}")
        embed.timestamp = discord.utils.utcnow()
        
        await channel.send(embed=embed)
        logger.info(f"📝 Нарушение залогировано: {user}")
        return True
        
    except discord.Forbidden:
        logger.error(f"❌ Нет прав для отправки в лог-канал")
        return False
    except discord.HTTPException as e:
        logger.error(f"❌ HTTP ошибка при логировании: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Неизвестная ошибка при логировании: {e}")
        return False

# === КОМАНДЫ МОДЕРАЦИИ ===

@bot2.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, minutes: int = 30, *, reason="Без причины"):
    """Выдать тайм-аут пользователю"""
    try:
        duration = minutes * 60
        await timeout_user(member, reason, duration)
        await ctx.send(f"⏳ {member.mention} получил тайм-аут на {minutes} минут. Причина: {reason}")
        await log_violation(ctx.guild, member, f"Командный тайм-аут: {reason}")
    except Exception as e:
        await ctx.send(f"❌ Ошибка: {e}")

@bot2.command()
@commands.has_permissions(moderate_members=True)
async def untimeout(ctx, member: discord.Member):
    """Снять тайм-аут с пользователя"""
    try:
        await member.timeout(None)
        await ctx.send(f"✅ Тайм-аут снят с {member.mention}")
    except Exception as e:
        await ctx.send(f"❌ Ошибка при снятии тайм-аута: {e}")

@bot2.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    """Очистить сообщения в канале"""
    try:
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 чтобы удалить команду
        await ctx.send(f"🧹 Удалено {len(deleted) - 1} сообщений.", delete_after=5)
    except Exception as e:
        await ctx.send(f"❌ Ошибка при очистке: {e}")

@bot2.command()
@commands.has_permissions(moderate_members=True)
async def warn(ctx, member: discord.Member, *, reason="Без причины"):
    """Выдать предупреждение"""
    try:
        await ctx.send(f"⚠️ {member.mention} получил предупреждение. Причина: {reason}")
        await log_violation(ctx.guild, member, f"Предупреждение: {reason}")
    except Exception as e:
        await ctx.send(f"❌ Ошибка: {e}")

@bot2.command()
@commands.has_permissions(administrator=True)
async def status(ctx):
    """Расширенная проверка статуса бота модерации"""
    try:
        # Подсчет активных пользователей в спам-логе
        active_users = len([user_id for user_id, timestamps in user_message_log.items() if timestamps])
        
        # Проверка лог-канала
        log_channel = ctx.guild.get_channel(LOG_CHANNEL_ID)
        log_status = "✅ Доступен" if log_channel else "❌ Не найден"
        
        embed = discord.Embed(
            title="🤖 Расширенный статус системы модерации",
            description="Детальная информация о работе бота",
            color=discord.Color.green()
        )
        embed.add_field(name="📊 Состояние", value="✅ Онлайн", inline=True)
        embed.add_field(name="🏓 Пинг", value=f"`{round(bot2.latency * 1000)}ms`", inline=True)
        embed.add_field(name="🔗 Серверы", value=f"`{len(bot2.guilds)}`", inline=True)
        
        embed.add_field(name="📝 Лог-канал", value=log_status, inline=True)
        embed.add_field(name="👥 Активных пользователей", value=f"`{active_users}`", inline=True)
        embed.add_field(name="⚙️ Модули", value="✅ Все активны", inline=True)
        
        embed.add_field(name="🛡️ Настройки защиты", 
                       value=f"• Лимит упоминаний: `{MENTION_LIMIT}`\n"
                             f"• Порог спама: `{SPAM_THRESHOLD} за {SPAM_INTERVAL}с`\n"
                             f"• Тайм-аут: `{TIMEOUT_DURATION//60} минут`", 
                       inline=False)
        
        embed.set_footer(text=f"Бот запущен • ID: {bot2.user.id}")
        embed.timestamp = discord.utils.utcnow()
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"❌ Ошибка в команде status: {e}")
        await ctx.send("❌ Ошибка при получении статуса системы")

@bot2.command()
@commands.has_permissions(moderate_members=True)
async def antispam_stats(ctx):
    """Статистика анти-спам системы"""
    try:
        if not user_message_log:
            await ctx.send("📊 Анти-спам лог пуст")
            return
            
        total_tracked = len(user_message_log)
        active_now = len([uid for uid, msgs in user_message_log.items() if msgs])
        
        embed = discord.Embed(
            title="📊 Статистика анти-спам системы",
            color=discord.Color.blue()
        )
        embed.add_field(name="👥 Всего отслеживается", value=f"`{total_tracked}`", inline=True)
        embed.add_field(name="🔥 Активны сейчас", value=f"`{active_now}`", inline=True)
        embed.add_field(name="⚙️ Интервал", value=f"`{SPAM_INTERVAL}с`", inline=True)
        
        # Топ самых активных (последние 5)
        if active_now > 0:
            top_users = sorted(
                [(uid, len(msgs)) for uid, msgs in user_message_log.items() if msgs],
                key=lambda x: x[1], reverse=True
            )[:5]
            
            top_text = ""
            for uid, count in top_users:
                try:
                    user = ctx.guild.get_member(uid)
                    name = user.display_name if user else f"ID:{uid}"
                    top_text += f"• {name}: `{count}` сообщений\n"
                except:
                    top_text += f"• ID:{uid}: `{count}` сообщений\n"
                    
            embed.add_field(name="🔥 Самые активные", value=top_text or "Нет данных", inline=False)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"❌ Ошибка в antispam_stats: {e}")
        await ctx.send("❌ Ошибка при получении статистики")

@bot2.command()
@commands.has_permissions(administrator=True)
async def clear_spam_log(ctx):
    """Очистить лог анти-спам системы"""
    try:
        old_count = len(user_message_log)
        user_message_log.clear()
        await ctx.send(f"🧹 Лог анти-спам очищен! Удалено записей: `{old_count}`")
        logger.info(f"Лог анти-спам очищен администратором {ctx.author}")
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке лога: {e}")
        await ctx.send("❌ Ошибка при очистке лога")

# === ФУНКЦИЯ ЗАПУСКА С АВТОМАТИЧЕСКИМ ПЕРЕЗАПУСКОМ ===
async def run_bot1_with_restart(bot1, token, name):
    """Запуск бота с автоматическим перезапуском при ошибках"""
    while True:
        try:
            logger.info(f"🚀 Запуск {name}...")
            await bot1.start(token)
        except discord.LoginFailure:
            logger.error(f"❌ Неверный токен для {name}")
            break
        except Exception as e:
            logger.error(f"❌ {name} упал с ошибкой: {e}")
            logger.info(f"🔄 Перезапуск {name} через 5 секунд...")
            await asyncio.sleep(5)
        finally:
            if not bot1.is_closed():
                await bot1.close()

# === ЗАПУСК ОБОИХ БОТОВ ===

@bot2.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name="unverify")
    if role:
        await member.add_roles(role)
        logger.info(f"✅ Выдана роль 'unverify' пользователю {member}")


async def main():
    """Главная функция запуска"""
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(run_bot1_with_restart(
                bot1, 
                "MTM3Njg3NjM5Mjc2MzEwMTI5Ng.GeBnqx.JlvnY-fv2sbjxoPAlyrYJkX6jNW2n5VTER908k",
                "Бот заявок"
            ))
            tg.create_task(run_bot1_with_restart(
                bot2, 
                "MTM3Njg1ODQxMTk0MTEwNTY5NA.GOXnKn.OZ1O8z4vvc4UD6FB23bIr1V81qyjNbgnCDdyFc",
                "Бот модерации"
            ))
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        logger.info("Перезапуск через 10 секунд...")
        await asyncio.sleep(10)
        await main()

if __name__ == "__main__":
    logger.info("🎯 Запуск системы ботов...")
    asyncio.run(main())





import random

verification_codes = {}


class VerificationModal(ui.Modal, title="Верификация"):
    code_input = ui.TextInput(label="Введите число", placeholder="Пример: 1234")

    async def on_submit(self, interaction: discord.Interaction):
        expected_code = verification_codes.get(interaction.user.id)
        try:
            if expected_code and self.code_input.value.strip() == str(expected_code):
                del verification_codes[interaction.user.id]
                role = discord.utils.get(interaction.guild.roles, name="User")
                if role:
                    await interaction.user.add_roles(role)
                    # Удалим роль 'unverify' если есть
                    unverify_role = discord.utils.get(interaction.guild.roles, name="unverify")
                    if unverify_role in interaction.user.roles:
                        await interaction.user.remove_roles(unverify_role)
                    await interaction.response.send_message("✅ Верификация успешна!", ephemeral=True)
                else:
                    await interaction.response.send_message("⚠️ Роль 'User' не найдена.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Неверный код. Попробуйте снова.", ephemeral=True)
        except Exception as e:
            logger.error(f"Ошибка при верификации: {e}")
            await interaction.response.send_message("❌ Ошибка на стороне сервера.", ephemeral=True)




@bot2.command()
@commands.has_permissions(administrator=True)
async def testlog(ctx):
    """Тестовая команда для логирования"""
    fake_user = ctx.author
    fake_reason = "Тест логирования"
    fake_msg = "Проверка лог-канала."
    result = await log_violation(ctx.guild, fake_user, fake_reason, fake_msg)
    if result:
        await ctx.send("✅ Лог отправлен.")
    else:
        await ctx.send("❌ Лог не отправлен.")

@bot2.command()
@commands.has_permissions(administrator=True)
async def status(ctx):
    try:
        channel = bot2.get_channel(LOG_CHANNEL_ID)
        if not channel:
            await ctx.send("❌ Лог-канал не найден.")
            return

        perms = channel.permissions_for(ctx.guild.me)
        embed = discord.Embed(title="📊 Статус системы", color=0x00ff00)
        embed.add_field(name="Лог-канал", value=f"{channel.mention}", inline=False)
        embed.add_field(name="Права", value=f"Embed Links: {'✅' if perms.embed_links else '❌'}\nSend Messages: {'✅' if perms.send_messages else '❌'}", inline=False)
        await ctx.send(embed=embed)
    except Exception as e:
        logger.error(f"❌ Ошибка в команде status: {e}")
        await ctx.send("❌ Ошибка при получении статуса.")
