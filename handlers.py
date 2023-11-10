from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    CommandHandler,
    CallbackContext,
    ConversationHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler
)
from config import api_key, api_secret, FAUNA_KEY
import cloudinary
from cloudinary.uploader import upload
from faunadb import query as q
from faunadb.client import FaunaClient
from faunadb.errors import NotFound

cloudinary.config(
    cloud_name="dvayilsnj",
    api_key=api_key,
    api_secret=api_secret
)

client = FaunaClient(secret=FAUNA_KEY)

CHOOSING, CLASS_STATE, SME_DETAILS, CHOOSE_PREF, SME_CAT, ADD_PRODUCTS, SHOW_STOCKS, POST_VIEW_PRODUCTS = range(8)

def start(update, context: CallbackContext) -> int:
    print("Received /start command")
    bot = context.bot
    chat_id = update.message.chat.id
    bot.send_message(
        chat_id=chat_id,
        text="Hi there, welcome to the Green Rabbit Test Shop! "
             "Please tell me about yourself. "
             "Give me your Full Name, Email, and Phone Number, "
             "separated by a coma (,) e.g.: "
             "Tony Bologna, email@aol.com, 555-555-5555"
    )
    return CHOOSING

def choose(update, context):
    bot = context.bot
    chat_id = update.message.chat.id
    data = update.message.text.split(',')
    if len(data) != 3:
        bot.send_message(
            chat_id=chat_id,
            text="Invalid entry. Please give me your Full Name, Email, and Phone Number, "
                 "separated by a coma (,) e.g.: "
                 "Tony Bologna, email@aol.com, 555-555-5555"
        )
        bot.send_message(
            chat_id=chat_id,
            text="Please try again or type /start to restart the bot"
        )
        return ConversationHandler.END

    new_user = client.query(
        q.create(q.collection('Users'), {
            'data': {
                'name': data[0],
                'email': data[1],
                'phone': data[2],
                'is_smeowner': False,
                'preference': "",
                'chat_id': chat_id
            }
        })
    )
    context.user_data["user-id"] = new_user["ref"].id()
    context.user_data["user-name"] = data[0]
    context.user_data['user-data'] = new_user['data']
    reply_keyboard = [
        [
            InlineKeyboardButton(
                text="Dealer",
                callback_data='SME'
            ),
            InlineKeyboardButton(
                text="Smoker",
                callback_data='Customer'
            )
        ]
    ]
    markup = InlineKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    bot.send_message(
        chat_id=chat_id,
        text="We have your info and we are selling it to the dark web! \n"
             "Please select if you're a Dealer or a Smoker",
        reply_markup=markup
    )
    return CLASS_STATE

def classer(update, context):
    bot = context.bot
    chat_id = update.callback_query.message.chat.id
    name = context.user_data['user-name']

    if update.callback_query.data.lower() == 'sme':
        client.query(
            q.update(
                q.ref(q.collection('Users'), context.user_data['user-id']),
                {"data": {"is_smeowner": True}}
            )
        )
        bot.send_message(
            chat_id=chat_id,
            text=f"Great Job MFing {name}! now tell me your Business details, "
                 "provide your Brand Name, Company Email, Address, and phone number "
                 "in that order, separated by a comma (,) just like before e.g.: "
                 "Phil McCrakin, bakedbar@aol.com, 420 High Street, 555-555-5555 ",
            reply_markup=ReplyKeyboardRemove()
        )
        return SME_DETAILS
    else:
        categories = [
            [
                InlineKeyboardButton(
                    text="Green Stuff",
                    callback_data='Green Stuff'
                ),
                InlineKeyboardButton(
                    text="White Stuff",
                    callback_data='White Stuff'
                )
            ],
            [
                InlineKeyboardButton(
                    text="Black Stuff",
                    callback_data='Black Stuff'
                ),
                InlineKeyboardButton(
                    text="NSFW Content",
                    callback_data='NSFW Content'
                )
            ]
        ]
        bot.send_message(
            chat_id=chat_id,
            text="Here is a list of deadly sins we have available "
                 "Pick your poison ",
            reply_markup=InlineKeyboardMarkup(categories)
        )
        return CHOOSE_PREF

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Bye MFer! Do not let the door hit you on the way out! ",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def business_details(update, context):
    bot = context.bot
    chat_id = update.message.chat.id
    data = update.message.text.split(',')

    if len(data) < 4 or len(data) > 4:
        bot.send_message(
            chat_id=chat_id,
            text="Invalid Entry! Please try again or type /start to restart the bot"
        )
        return SME_DETAILS

    context.user_data["sme_deets"] = data
    categories = [
        [
            InlineKeyboardButton(
                text="Green Stuuf",
                callback_data='Green Stuff'
            ),
            InlineKeyboardButton(
                text="White Stuff",
                callback_data='White Stuff'
            )
        ],
        [
            InlineKeyboardButton(
                text="Black Stuff",
                callback_data='Black Stuff'
            ),
            InlineKeyboardButton(
                text="NSFW Content",
                callback_data='NSFW Content'
            )
        ]
    ]
    markup = InlineKeyboardMarkup(categories, one_time_keyboard=True)
    bot.send_message(
        chat_id=chat_id,
        text="Pick a category from the list. What's your specialty?",
        reply_markup=markup
    )
    return SME_CAT

def business_details_update(update, context):
  print("Inside business_details_update function")
  bot = context.bot
  chat_id = update.callback_query.message.chat.id
  choice = update.callback_query.data

  new_sme = client.query(
      q.create(
          q.collection('Business'),
          {"data": {
              "name": context.user_data['sme_deets'][0],
              "email": context.user_data['sme_deets'][1],
              "address": context.user_data['sme_deets'][2],
              "telephone": context.user_data['sme_deets'][3],
              "category": choice.lower()
          }}
      )
  )
  context.user_data['sme_name'] = context.user_data['sme_deets'][0]
  context.user_data['sme_id'] = new_sme["ref"].id()
  context.user_data['sme_cat'] = choice
  button = [[
      InlineKeyboardButton(
          text="Add a product",
          callback_data=choice.lower()
      )
  ]]
  bot.send_message(
      chat_id=chat_id,
      text="New Dealer account successfully created! "
           "Let's add your Party Favors (products) shall we?",
      reply_markup=InlineKeyboardMarkup(button)
  )
  return ADD_PRODUCTS

def add_product(update, context):
  bot = context.bot
  chat_id = update.callback_query.message.chat.id
  bot.send_message(
      chat_id=chat_id,
      text="Add the Name, Description, and Price of your Party Favors, "
           "Make sure each one is separated by a comma (,) "
  )
  return ADD_PRODUCTS

def product_info(update, context: CallbackContext):
    # Assuming the user might not always attach a photo
    if not update.message.photo:
        # Handle the case where no photo is attached
        update.message.reply_text("No photo attached. The product will be added without an image.")
        # Proceed with processing the product information
    else:
        bot = context.bot
        photo = bot.getFile(update.message.photo[-1].file_id)
        file_ = open('product_image', 'wb')
        photo.download(out=file_)

        data = update.message.caption.split(',')

        send_photo = upload('product_image', width=200, height=150, crop='thumb')

        newprod = client.query(
            q.create(
                q.collection('Product'),
                {"data": {
                    "name": data[0],
                    "description": data[1],
                    "price": float(data[2]),
                    "image": send_photo['secure_url'],
                    'sme': context.user_data['sme_name'],
                    'sme_chat_id': update.message.chat.id,
                    'category': context.user_data["sme_cat"]
                }}
            )
        )
        client.query(
            q.update(
                q.ref(q.collection('Business'), context.user_data['sme_id']),
                {"data": {"latest": newprod['ref'].id()}}
            )
        )
        button = [
            [InlineKeyboardButton(
                text="Add More Products",
                callback_data=context.user_data['sme_name']
            )]
        ]
        update.message.reply_text(
            "Product Added Successfully",
            reply_markup=InlineKeyboardMarkup(button)
        )
        return ADD_PRODUCTS

def customer_pref(update, context):
    bot = context.bot
    chat_id = update.callback_query.message.chat.id
    data = update.callback_query.data
    print(data)

    try:
        smes_ = client.query(
            q.map_(
                lambda var: q.get(var),
                q.paginate(
                    q.match(
                        q.index('business_by_category'),
                        str(data).lower()
                    )
                )
            )
        )
        print(smes_)
        for sme in smes_["data"]:
            button = [
                [InlineKeyboardButton(
                    text='View Product',
                    callback_data=sme['data']["name"]
                )],
                [InlineKeyboardButton(
                    text="Select for Updates",
                    callback_data='pref' + ',' + sme['data']["name"]
                )]
            ]
            if "latest" in sme["data"].keys():
                thumbnail = client.query(q.ref(q.collection("Product"), sme["data"]["latest"]))
                print(thumbnail)
                bot.send_photo(
                    chat_id=chat_id,
                    photo=thumbnail["data"]["image"],
                    caption=f"{sme['data']['image']}",
                    reply_markup=InlineKeyboardMarkup(button)
                )
            else:
                bot.send_message(
                    chat_id=chat_id,
                    text=f"{sme['data']['name']}",
                    reply_markup=InlineKeyboardMarkup(button)
                )
    except NotFound:
        button = [
            [InlineKeyboardButton(
                text="Select another Category?",
                callback_data='customer'
            )]
        ]
        bot.send_message(
            chat_id=chat_id,
            text="Sorry MFer! Nothing here yet",
            reply_markup=InlineKeyboardMarkup(button)
        )
        return CLASS_STATE
    return SHOW_STOCKS

def show_products(update, context):
    bot = context.bot
    chat_id = update.callback_query.message.chat.id
    data = update.callback_query.data
    if "pref" in data:
        print(data)
        user = client.query(
            q.get(
              q.ref(
                q.match(q.index('user_by_name'), context.user_data['user-data']['name'])
            )
          )    
        )

        client.query(
            q.update(
                q.ref(q.collection('User'), user['ref'].id()),
                {'data': {'preference': user['data']['preference'] + data + ','}}
            )
        )
        button = [
            [InlineKeyboardButton(
                text="View more Business Categories",
                callback_data='customer'
            )]
        ]
        bot.send_message(
            chat_id=chat_id,
            text="Updated Preference Successfully!",
            reply_markup=InlineKeyboardMarkup(button)
        )
        return CLASS_STATE
    products = client.query(
        q.map_(
            lambda x: q.get(x),
            q.paginate(
                q.match(
                    q.index('product_by_business'),
                    update.callback_query.data  # Assuming data is the dealer's name
                )
            )
        )
    )
    if len(products) <= 0:
        bot.send_message(
            chat_id=chat_id,
            text="Nothing to see here, User is lazy and has not added products"
        )
        return CLASS_STATE
    for product in products['data']:
        context.user_data['sme_id'] = product['data']['sme']
        button = [
            [InlineKeyboardButton(
                text="Send Order",
                callback_data='order' + product['ref'].id()
            )],
            [InlineKeyboardButton(
                text="Contact Dealer",
                callback_data='contact;' + product['data']['sme']
            )]
        ]
        bot.send_photo(
            chat_id=chat_id,
            photo=product['data']['image'],
            caption=f"{product['data']['name']} \nDescription: {product['data']['description']}\nPrice:{product['data']['price']}",
            reply_markup=InlineKeyboardMarkup(button)
        )
    return POST_VIEW_PRODUCTS
def post_view_products(update, context: CallbackContext) -> None:
  bot = context.bot
  chat_id = update.callback_query.message.chat.id
  data = update.callback_query.data

  try:
      # Check if the split operation produces at least two elements
      data_elements = data.split(';')
      if len(data_elements) > 1:
          product_ref = q.ref(q.collection('Product'), data_elements[1])

          # Check if the "Product" collection exists before querying
          if q.exists(q.collection('Product')):
              product_data = client.query(q.get(product_ref))["data"]

              if "order" in data:
                  bot.send_message(
                      chat_id=product_data["sme_chat_id"],
                      text="Hey MFer! You have a new order!!"
                  )
                  bot.send_photo(
                      chat_id=product_data["sme_chat_id"],
                      caption=f"{product_data['name']} \n\nDescription: {product_data['description']}\n\nPrice: {product_data['price']}"
                              f"\n\n Customer's Name: {context.user_data['user-name']}",
                      photo=product_data['image']
                  )
              elif 'contact' in data:
                  sme_data = client.query(
                      q.get(
                          q.match(
                              q.index('business_by_name'),
                              product_data['sme']
                          )
                      )
                  )['data']
                  bot.send_message(
                      chat_id=chat_id,
                      text=f"Name: {sme_data['name']}\n\nTelephone: {sme_data['telephone']}\n\nEmail: {sme_data['email']}"
                  )
          else:
              bot.send_message(chat_id=chat_id, text="Product collection does not exist.")
      else:
          bot.send_message(chat_id=chat_id, text="There are no product here yet.")
  except Exception as e:
      # Handle any other exceptions that might occur during the execution
      bot.send_message(chat_id=chat_id, text=f"An error occurred: {str(e)}")
