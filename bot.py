
import jdatetime
import json
import os
from datetime import datetime
import schedule
import time
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import asyncio

BOT_TOKEN = "7931926992:AAEIZ-5VNf2g5CSwcl4bG0tDzdSrFDbsJxY"
GROUP_ID = -1002584767303  # Replace with your group ID (negative number)


DATA_FILE = 'tea_list.json'

menu_for_days = {
    "Monday": "زرشک پلو",
    "Tuesday": "قرمه سبزی",
    "Wednesday": "جوجه کباب",
    "Thursday": " ",
    "Friday": " ",
    "Saturday": "کوبیده",
    "Sunday": "قیمه"
}


def load_tea_data():
    if not os.path.exists(DATA_FILE):
        return {"members": [], "last_index": -1}
    try:
        with open(DATA_FILE, 'r') as f:
            content = f.read().strip()
            if not content:
                return {"members": [], "last_index": -1}
            return json.loads(content)
    except json.JSONDecodeError:
        return {"members": [], "last_index": -1}
    

def save_tea_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)


def load_lunch_responses():
    if not os.path.exists('lunch_responses.json'):
        return {}

    try:
        with open('lunch_responses.json', 'r') as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        return {}



def save_lunch_responses(responses):
    with open('lunch_responses.json', 'w') as f:
        json.dump(responses, f)


# Get today's date as a string (format: YYYY-MM-DD)
# def get_today_date():
#     return datetime.now().strftime('%Y-%m-%d')


def get_today_date():
    # Get today's date in Gregorian
    today = datetime.now()

    # Convert to Jalali (Persian) date
    jalali_date = jdatetime.date.fromgregorian(date=today)

    # Format as 'YYYY-MM-DD' or any format you like
    return jalali_date.strftime('%Y-%m-%d')  # Example: '1404-03-12'



def get_today_menu():
    # Get today's day of the week
    today_day = datetime.now().strftime('%A')  # Returns day name (e.g., "Monday")
    
    # Return the menu for today
    return menu_for_days.get(today_day, " ")  # Default to "Kebab" if day not found



async def addme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_tea_data()
    user = update.effective_user

    if any(m['id'] == user.id for m in data['members']):
        await update.message.reply_text("✅ شما در لیست هستید!")
    else:
        data['members'].append({"id": user.id, "name": user.first_name})
        save_tea_data(data)
        await update.message.reply_text("☕ به لیست چای بدمان اضافه شدید!")


async def list_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_tea_data()
    if not data['members']:
        await update.message.reply_text("کسی در لیست نیست!")
    else:
        msg = "🫖 لیست چای بدمان:\n"
        for i, member in enumerate(data['members']):
            msg += f"{i + 1}. {member['name']}\n"
        await update.message.reply_text(msg)


# async def announce_tea_duty(application):
#     data = load_tea_data()
#     if not data['members']:
#         return  # no one in list

#     index = (data['last_index'] + 1) % len(data['members'])
#     member = data['members'][index]
#     data['last_index'] = index
#     save_tea_data(data)

#     user_id = member['id']
#     user_name = member['name']

#     text = f"🍵 امروز نوبت <a href='tg://user?id={user_id}'>{user_name}</a> برامون چای بدمه!"
#     await application.bot.send_message(
#         chat_id=GROUP_ID,
#         text=text,
#         parse_mode='HTML'
#     )


async def announce_tea_duty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_tea_data()
    if not data['members']:
        return  # No one in the list

    # Get the next person in the rotation
    index = (data['last_index'] + 1) % len(data['members'])
    member = data['members'][index]
    data['last_index'] = index
    save_tea_data(data)

    user_id = member['id']
    user_name = member['name']

    # Ask if they can make tea
    text = f"🍵 امروز نوبت <a href='tg://user?id={user_id}'>{user_name}</a> برامون چای بدمه! آیا می‌خواهید چای درست کنید؟"
    keyboard = [
        [InlineKeyboardButton("بله", callback_data='yes')],
        [InlineKeyboardButton("خیر", callback_data='no')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)


    await update.message.reply_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )



async def handle_tea_duty_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    response = query.data  # 'yes' or 'no'
    print(f"Received response: {response}")
    data = load_tea_data()

    # Find the current person whose turn it is
    current_turn = data['members'][data['last_index']]

    # If the response is 'no', move the turn to the next person
    if response == 'no':
        # Rotate the list to the next member
        print("no")
        data['last_index'] = (data['last_index'] + 1) % len(data['members'])
        save_tea_data(data)

        next_member = data['members'][data['last_index']]

        # Acknowledge the response
        await query.answer()

        # Re-send the message with buttons for the next person
        keyboard = [
            [InlineKeyboardButton("بله", callback_data='yes')],
            [InlineKeyboardButton("خیر", callback_data='no')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🍵 امروز نوبت <a href='tg://user?id={next_member['id']}'>{next_member['name']}</a> برامون چای بدمه! آیا می‌خواهید چای درست کنید؟",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        # If the person agrees to make tea
        await query.answer()

        # Edit the message to thank the user
        await query.edit_message_text(f"💚 {user_name} چای درست خواهد کرد. ممنون از شما!")



async def handle_lunch_vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user_name = query.from_user.first_name  # User's first name
    vote = query.data  # 'yes' or 'no'
    today_date = get_today_date()

    # Load current lunch responses
    lunch_responses = load_lunch_responses()

    # Initialize the date entry if it doesn't exist
    if today_date not in lunch_responses:
        lunch_responses[today_date] = {"yes": [], "no": []}

    # If the user has already voted, we need to remove their previous vote
    # Remove user from the 'yes' list if they are there
    lunch_responses[today_date]["yes"] = [user for user in lunch_responses[today_date]["yes"] if user["id"] != user_id]

    # Remove user from the 'no' list if they are there
    lunch_responses[today_date]["no"] = [user for user in lunch_responses[today_date]["no"] if user["id"] != user_id]

    # Add the new vote for the user
    if vote == 'yes':
        lunch_responses[today_date]["yes"].append({"id": user_id, "name": user_name})
    else:
        lunch_responses[today_date]["no"].append({"id": user_id, "name": user_name})

    save_lunch_responses(lunch_responses)

    # Acknowledge the button press without replying
    await query.answer()



async def summarize_lunch_responses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lunch_responses = load_lunch_responses()
    today_date = get_today_date()

    # Check if we have data for today
    if today_date not in lunch_responses:
        await update.message.reply_text("برای امروز لیست ناهاری نیست.")
        return

    yes_members = lunch_responses[today_date]["yes"]
    no_members = lunch_responses[today_date]["no"]

    yes_count = len(yes_members)
    no_count = len(no_members)

    summary = f"🍽️ **لیست ناهارخوران {today_date}** 🍽️\n\n" \
              f"✅ ناهارخوران: {yes_count}\n" \
              f"❌ ناهارنخوران: {no_count}\n\n"

    # Generate clickable links for 'Yes' voters
    if yes_count > 0:
        summary += "کسانی که هستند:\n"
        for member in yes_members:
            summary += f"<a href='tg://user?id={member['id']}'>{member['name']}</a>\n"
        summary += "\n"

    # Generate clickable links for 'No' voters
    if no_count > 0:
        summary += "کسانی که همراهی نمیکنند:\n"
        for member in no_members:
            summary += f"<a href='tg://user?id={member['id']}'>{member['name']}</a>\n"
        summary += "\n"

    # Send the summary to the group
    await update.message.reply_text(summary, parse_mode='HTML')



async def send_vote_in_group(application):
    today_menu = get_today_menu()
    keyboard = [
        [InlineKeyboardButton("بله", callback_data='yes')],
        [InlineKeyboardButton("خیر", callback_data='no')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the vote message to the group with mentions at the bottom
    await application.bot.send_message(
        chat_id=GROUP_ID,  # Replace with your group ID
        text=f"🍽️ امروز ناهار *{today_menu}* داریم. کنارمون هستی؟\n\n",
        reply_markup=reply_markup,
        parse_mode='HTML'  # Use HTML to render the links
    )


def schedule_daily_lunch_question(application):
    # Send vote question only once a day at 10:30 AM
    schedule.every().day.at("14:37").do(lambda: asyncio.run(send_vote_in_group(application)))

    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(20)

    thread = threading.Thread(target=run_scheduler)
    thread.daemon = True
    thread.start()




def schedule_daily_announcement(application):
    schedule.every().day.at("16:57").do(lambda: asyncio.run(announce_tea_duty(application)))

    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1)

    thread = threading.Thread(target=run_scheduler)
    thread.daemon = True
    thread.start()



if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("addme", addme))
    app.add_handler(CommandHandler("tealist", list_members))
    app.add_handler(CallbackQueryHandler(handle_lunch_vote))
    app.add_handler(CallbackQueryHandler(handle_tea_duty_response)) 
    app.add_handler(CommandHandler("summarize", summarize_lunch_responses))
    app.add_handler(CommandHandler("teamaker", announce_tea_duty))

    schedule_daily_lunch_question(app)
    
    print("Patvaz Bot is running...")
    app.run_polling()