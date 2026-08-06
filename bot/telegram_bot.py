import asyncio
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from core.config import settings
from core.database import Database
from core.llm_client import LLMClient
from core.orchestrator import Orchestrator
from agents import EmailAgent, TabMonitorAgent, FreelanceHunterAgent, StatusTrackerAgent


class TelegramBot:
    def __init__(self, db: Database, orchestrator: Orchestrator):
        self.db = db
        self.orchestrator = orchestrator
        self.app: Optional[Application] = None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("📧 Check Email", callback_data="exec:email")],
            [InlineKeyboardButton("🔍 Check Platforms", callback_data="exec:tab_monitor")],
            [InlineKeyboardButton("💼 Find Jobs", callback_data="exec:freelance_hunter")],
            [InlineKeyboardButton("📊 Daily Report", callback_data="exec:status_tracker")],
            [InlineKeyboardButton("📋 All Commands", callback_data="show:commands")],
        ]
        await update.message.reply_text(
            "🏢 AgentOffice\n\nHello Boss! Your AI agents are ready.\nWhat would you like me to do?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    async def commands(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = """📋 Available Commands

🤖 Agent Commands:
/email - Check your Gmail inbox
/platforms - Check AI training platforms
/jobs [query] - Search freelance jobs
/report - Get daily productivity report

📝 Task Commands:
/status - View all agent statuses
/pending - View pending job proposals
/approve <id> - Approve a job application

🔧 System Commands:
/start - Show main menu
/commands - Show this help

🌐 Web Dashboard:
Open http://localhost:3000 to see your virtual office!"""
        await update.message.reply_text(text)

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            agents = await self.orchestrator.get_all_status()
            lines = ["🏢 Agent Status\n"]
            for a in agents:
                status_emoji = {"idle": "🟢", "working": "🔵", "error": "🔴"}.get(a["status"], "⚪")
                lines.append(f"{a['avatar']} {a['name']}: {status_emoji} {a['status']}")
            await update.message.reply_text("\n".join(lines))
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")

    async def email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("📧 Checking your inbox...")
        result = await self.orchestrator.execute("email")
        await update.message.reply_text(f"{'✅' if result.success else '❌'} {result.message}")

    async def platforms(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🔍 Checking AI training platforms...")
        result = await self.orchestrator.execute("tab_monitor")
        await update.message.reply_text(f"{'✅' if result.success else '❌'} {result.message}")

    async def jobs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = " ".join(context.args) if context.args else "python developer"
        await update.message.reply_text(f"💼 Searching jobs for: {query}...")
        result = await self.orchestrator.execute("freelance_hunter", query)
        await update.message.reply_text(f"{'✅' if result.success else '❌'} {result.message}")

    async def report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("📊 Generating report...")
        result = await self.orchestrator.execute("status_tracker", "report")
        await update.message.reply_text(result.message)

    async def pending(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        applications = await self.db.get_pending_applications()
        if not applications:
            await update.message.reply_text("No pending proposals.")
            return

        for app in applications[:5]:
            keyboard = [[
                InlineKeyboardButton("✅ Approve", callback_data=f"approve:{app['id']}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject:{app['id']}"),
            ]]
            text = f"""💼 *{app['job_title'][:50]}*
Platform: {app['platform']}
Budget: {app['budget']}

{app['proposal'][:300]}..."""
            await update.message.reply_text(
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

    async def approve(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Usage: /approve <id>")
            return
        try:
            app_id = int(context.args[0])
            await self.db.approve_application(app_id)
            await update.message.reply_text(f"✅ Approved application #{app_id}")
        except ValueError:
            await update.message.reply_text("Invalid ID")

    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        data = query.data
        if data.startswith("exec:"):
            agent = data.split(":")[1]
            await query.edit_message_text(f"⏳ Running {agent}...")
            result = await self.orchestrator.execute(agent)
            await query.edit_message_text(f"{'✅' if result.success else '❌'} {result.message[:500]}")

        elif data == "show:commands":
            text = """📋 Available Commands

🤖 Agent Commands:
/email - Check your Gmail inbox
/platforms - Check AI training platforms
/jobs [query] - Search freelance jobs
/report - Get daily productivity report

📝 Task Commands:
/status - View all agent statuses
/pending - View pending job proposals
/approve <id> - Approve a job application

🔧 System Commands:
/start - Show main menu
/commands - Show this help"""
            await query.edit_message_text(text)

        elif data.startswith("approve:"):
            app_id = int(data.split(":")[1])
            await self.db.approve_application(app_id)
            await query.edit_message_text(f"✅ Approved application #{app_id}")

        elif data.startswith("reject:"):
            app_id = int(data.split(":")[1])
            await self.db.execute(
                "UPDATE job_applications SET status = 'rejected' WHERE id = ?", (app_id,)
            )
            await query.edit_message_text(f"❌ Rejected application #{app_id}")

    def setup(self) -> Application:
        self.app = Application.builder().token(settings.telegram_bot_token).build()

        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("commands", self.commands))
        self.app.add_handler(CommandHandler("help", self.commands))
        self.app.add_handler(CommandHandler("status", self.status))
        self.app.add_handler(CommandHandler("email", self.email))
        self.app.add_handler(CommandHandler("platforms", self.platforms))
        self.app.add_handler(CommandHandler("jobs", self.jobs))
        self.app.add_handler(CommandHandler("report", self.report))
        self.app.add_handler(CommandHandler("pending", self.pending))
        self.app.add_handler(CommandHandler("approve", self.approve))
        self.app.add_handler(CallbackQueryHandler(self.callback_handler))

        return self.app

    async def run(self):
        app = self.setup()
        await app.initialize()
        await app.start()
        await app.updater.start_polling()


def main():
    import nest_asyncio
    nest_asyncio.apply()
    
    async def run():
        db = Database(settings.database_path)
        await db.connect()

        llm = LLMClient(db)
        orchestrator = Orchestrator(db, llm)

        orchestrator.register(EmailAgent())
        orchestrator.register(TabMonitorAgent())
        orchestrator.register(FreelanceHunterAgent())
        orchestrator.register(StatusTrackerAgent())

        bot = TelegramBot(db, orchestrator)
        app = bot.setup()
        
        print("🤖 Telegram bot starting...")
        await app.initialize()
        await app.start()
        print("🤖 Telegram bot started! Send /start to the bot.")
        await app.updater.start_polling(drop_pending_updates=True)
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
            await db.close()
    
    asyncio.get_event_loop().run_until_complete(run())


if __name__ == "__main__":
    main()
