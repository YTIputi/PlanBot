from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import sqlite3

# Создание базы данных
def init_db():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я ваш планировщик. Напишите /help для списка команд.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Список команд:\n/add <задача> - Добавить задачу\n/list - Показать задачи\n/done <id> - Отметить задачу выполненной\n/delete <id> - Удалить задачу\n/history - Показать историю')

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    task = ' '.join(context.args)
    if task:
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO tasks (user_id, task, status) VALUES (?, ?, ?)', (user_id, task, 'pending'))
        cursor.execute('INSERT INTO history (user_id, task, action) VALUES (?, ?, ?)', (user_id, task, 'added'))
        conn.commit()
        conn.close()
        await update.message.reply_text(f'Задача "{task}" добавлена!')
    else:
        await update.message.reply_text('Пожалуйста, укажите задачу.')

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, task, status FROM tasks WHERE user_id = ? AND status = ?', (user_id, 'pending'))
    tasks = cursor.fetchall()
    conn.close()
    
    if tasks:
        response = 'Ваши задачи:\n'
        for task in tasks:
            response += f'{task[0]}. {task[1]}\n'
    else:
        response = 'У вас нет задач.'
    await update.message.reply_text(response)

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        task_id = int(context.args[0])
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET status = ? WHERE id = ? AND user_id = ?', ('done', task_id, user_id))
        cursor.execute('INSERT INTO history (user_id, task, action) SELECT user_id, task, ? FROM tasks WHERE id = ? AND user_id = ?', ('completed', task_id, user_id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f'Задача {task_id} выполнена!')
    except (IndexError, ValueError):
        await update.message.reply_text('Пожалуйста, укажите ID задачи.')

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        task_id = int(context.args[0])
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO history (user_id, task, action) SELECT user_id, task, ? FROM tasks WHERE id = ? AND user_id = ?', ('deleted', task_id, user_id))
        cursor.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f'Задача {task_id} удалена!')
    except (IndexError, ValueError):
        await update.message.reply_text('Пожалуйста, укажите ID задачи.')

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('SELECT task, action, timestamp FROM history WHERE user_id = ? ORDER BY timestamp DESC', (user_id,))
    history_data = cursor.fetchall()
    conn.close()

    if history_data:
        response = 'История ваших действий:\n'
        for entry in history_data:
            response += f'{entry[2]} - {entry[1]}: {entry[0]}\n'
    else:
        response = 'История пуста.'
    await update.message.reply_text(response)

def main():
    init_db()

    # Создание приложения
    app = Application.builder().token('8073377033:AAH4wLV-E_a1f8CPKREXS5uDAJLDXwcS1hE').build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('add', add))
    app.add_handler(CommandHandler('list', list_tasks))
    app.add_handler(CommandHandler('done', done))
    app.add_handler(CommandHandler('delete', delete))
    app.add_handler(CommandHandler('history', history))

    # Запуск бота
    app.run_polling()

if __name__ == '__main__':
    main()
