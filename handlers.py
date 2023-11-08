from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove, Update,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    CommandHandler, CallbackContext,
    ConversationHandler, MessageHandler,
    filters, Updater, CallbackQueryHandler
)
from config import (
    api_key, sender_email,
    api_secret,
    FAUNA_KEY
)
import cloudinary
from cloudinary.uploader import upload
from faunadb import query as q
from faunadb.client import FaunaClient
from faunadb.errors import NotFound

# configure cloudinary
cloudinary.config(
    cloud_name="dvayislnj",
    api_key=api_key,
    api_secret=api_secret
)

# fauna client config
client = FaunaClient(secret=FAUNA_KEY)

# Define Options
CHOOSING, CLASS_STATE, SME_DETAILS, CHOOSE_PREF, \
    SME_CAT, ADD_PRODUCTS, SHOW_STOCKS, POST_VIEW_PRODUCTS = range(8)
    
def start(update, context: CallbackContext) -> int:
    print("You called")
    bot = context.bot
    chat_id = update.message.chat.id
    bot.send_message(
        chat_id=chat_id,
        text= "Hello Bud Buddy, Welcome to Green Rabbit Smoke Shop,"
        "This is only a test so please feel free to tell me about yourself, "
        "provide your full name, email, and phone number, "
        "separated by comma each e.g: "
        "John Doe, JohnD@gmail.com, +17145555555"
    )
    return CHOOSING
    
# get data generic user data from user and store
def choose(update, context):
    bot = context.bot
    chat_id = update.message.chat.id
    # create new data entry
    data = update.message.text.split(',')
    if len(data) < 3 or len(data) > 3:
        bot.send_message(
            chat_id=chat_id,
            text="Sheesh! Invalid entry, please make sure to input the correct details "
            "as requested in the instructions"
        )
        bot.send_message(
            chat_id=chat_id,
            text="Type /start, to restart bot"
        )
        return ConversationHandler.END
    #TODO: Check if user already exists before creating new user
    new_user = client.query(
        q.create(q.collection('User'), {
            "data":{
                "name":data[0],
                "email":data[1],
                "telephone":data[2],
                "is_smeowner":False,
                "preference": "",
                "chat_id":chat_id
            }
        })
    )
    context.user_data["user-id"] = new_user["ref"].id()
    context.user_data["user-name"] = data[0]
    context.user_data['user-data'] = new_user['data']
    reply_keyboard = [
    [
        InlineKeyboardButton(
            text="SME",
            callback_data="SME"
        ),
        InlineKeyboardButton(
            text="Customer",
            callback_data="Customer"
        )
    ]
  ]
    markup = InlineKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    bot.send_message(
        chat_id=chat_id,
        text="You did it! We collected your information succesfully!..🎉🎉 \n"
        "Which of the following do you identify as ?",
        reply_markup=markup
    )
    return CLASS_STATE
def classer(update, context):
    bot = context.bot
    chat_id = update.callback_query.message.chat.id
    name = context.user_data["user-name"]
    if update.callback_query.data.lower() == "sme":
        # update user as smeowner
        client.query(
            q.update(
                q.ref(q.collection("User"), context.user_data["user-id"]),
                {"data": {"is_smeowner":True}}
            )
        )
        bot.send_message(
            chat_id=chat_id,
            text=f"Great! {name}, please tell me about your business, "
            "provide your BrandName, Brand email, Address, and phone number"
            "in that order, each separated by comma(,) each e.g: "
            "Baked Bar, bakedbar@gmail.com, 420 stoned ave, +17148888888",
            reply_markup=ReplyKeyboardRemove()
        )

        return SME_DETAILS
    categories = [  
        [
            InlineKeyboardButton(
                text="Live Rosin",
                callback_data="Live Rosin"
            ),
            InlineKeyboardButton(
                text="Liquid Diamonds",
                callback_data="Liquid Diamonds"
            )
        ],
        [
            InlineKeyboardButton(
                text="Live Resin",
                callback_data="Live Resin"
            ),
            InlineKeyboardButton(
                text="Shatter",
                callback_data="Shatter"
            )
        ]
    ]
    bot.send_message(
        chat_id=chat_id,
        text="Here's a list of categories available"
        "Choose one that matches your interest",
        reply_markup=InlineKeyboardMarkup(categories)
    )
    return CHOOSE_PREF
# Control
def cancel(update: Update, context: CallbackContext) -> int: 
    update.message.reply_text(
        'Bye! I hope we can talk again some day.',
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

    
    