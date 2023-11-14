import cloudinary,logging
from cloudinary.uploader import upload
from faunadb import query as q
from faunadb.client import FaunaClient
from faunadb.errors import NotFound
from telegram import (
  InlineKeyboardButton,
  InlineKeyboardMarkup,
  ReplyKeyboardRemove,
  Update,
)
from telegram.ext import CallbackContext, ConversationHandler

from config import FAUNA_KEY, api_key, api_secret, dealer_password

# cloudinary config
cloudinary.config(
    cloud_name="dvayislnj",
    api_key=api_key,
    api_secret=api_secret
)

# fauna config
client = FaunaClient(secret=FAUNA_KEY)

# password config
DEALER_PASSWORD = dealer_password

AWAIT_PASSWORD, CHOOSING, CLASS_STATE, SME_DETAILS, CHOOSE_PREF, SME_CAT, ADD_PRODUCTS, SHOW_STOCKS, POST_VIEW_PRODUCTS = range(9)

def start(update, context: CallbackContext) -> int:
  print("You called")
  bot = context.bot
  chat_id = update.message.chat.id
  bot.send_message(
      chat_id=chat_id,
      text= "Hi fellow, Welcome to the Smokers & Dealer's Test Shop ,"
      "Please tell me about yourself, "
      "provide your full name, email, and phone number, "
      "separated by comma each e.g: "
      "John Doe, JohnD@gmail.com, +234567897809"
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
          text="Invalid entry, please make sure to input the details "
          "as requested in the instructions"
      )
      bot.send_message(
          chat_id=chat_id,
          text="Type /start, to restart bot"
      )
      return ConversationHandler.END
  #TODO: Check if user already exists before creating new user
  new_user = client.query(
      q.create(q.collection('Users'), {
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
          InlineKeyboardButton(text="SME", callback_data="SME"),
          InlineKeyboardButton(text="Customer", callback_data="Customer")
      ]
  ]
  markup = InlineKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
  bot.send_message(
      chat_id=chat_id,
      text="Your information has been succesfully collected!..🎉🎉 \n"
      "Are you a Smoker or are you a Dealer?",
      reply_markup=markup
  )
  return CLASS_STATE

def classer(update, context):
  bot = context.bot
  chat_id = update.callback_query.message.chat.id
  name = context.user_data["user-name"]

  # Check if the user chose SME
  if update.callback_query.data.lower() == "sme":
      print('Entered password entry')
      bot.send_message(
          chat_id=chat_id,
          text="Please enter the dealer password, if you do not have one,"
          "please contact Adam:",
          reply_markup=ReplyKeyboardRemove()
      )
      return AWAIT_PASSWORD

  # Handle case for "Customer"
  elif update.callback_query.data.lower() == "customer":
    categories = [  
      [
          InlineKeyboardButton(text="Smokers & Dealers Shop", callback_data="Clothing/Fashion"),
          InlineKeyboardButton(text="Hot Pot - Smokers Acessories", callback_data="Hardware Accessories")
      ],
      [
          InlineKeyboardButton(text="WTF is this Shop", callback_data="Food/Kitchen Ware"),
          InlineKeyboardButton(text="Don't Shop Here 2nd Hand Store", callback_data="ArtnDesign")
      ]
    ]
    bot.send_message(
      chat_id=chat_id,
      text="Here's a list of our available shops:",
      reply_markup=InlineKeyboardMarkup(categories)
    )
    return CHOOSE_PREF
def await_password(update, context):
  print('Entered await password')
  user_input = update.message.text
  if user_input == DEALER_PASSWORD:
      update.message.reply_text(f"Great! Your Password is correct! You must know people!," 
            "please tell me about your business, "
            "provide your Brand Name, Brand email, Address, and phone number"
            "in that order, each separated by comma(,) each e.g: "
            "JDWears, JDWears@gmail.com, 101-Mike Avenue-Ikeja, +234567897809",
            reply_markup=ReplyKeyboardRemove()
      )

      return SME_DETAILS 

# Control
def cancel(update: Update, context: CallbackContext) -> int: 
    update.message.reply_text(
        'Bye! I hope we can talk again some day.',
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def business_details(update, context):
  print ('Entered business details')
  bot = context.bot
  chat_id = update.message.chat.id
  data = update.message.text.split(',')
  if len(data) < 4 or len(data) > 4:
      bot.send_message(
          chat_id=chat_id,
          text="Invalid entry, please make sure to input the details "
          "as requested in the instructions"
      )
      return SME_DETAILS
  context.user_data["sme_dets"] = data
  # categories = [
  #         ['Clothing/Fashion', 'Hardware Accessories'],
  #         ['Food/Kitchen Ware', 'ArtnDesign'],
  #         ['Other']
  # ]
  categories = [  
      [
          InlineKeyboardButton(
              text="Smokers and Dealers Shop",
              callback_data="Clothing/Fashion"
          ),
          InlineKeyboardButton(
              text="Hot Pot - SMokers Accessories",
              callback_data="Hardware Accessories"
          )
      ],
      [
          InlineKeyboardButton(
              text="WTF is This Shop",
              callback_data="Food/Kitchen Ware"
          ),
          InlineKeyboardButton(
              text="Dont Shop Here 2nd Hand Store",
              callback_data="ArtnDesign"
          )
      ]
  ]
  markup = InlineKeyboardMarkup(categories, one_time_keyboard=True)
  bot.send_message(
      chat_id=chat_id,
      text="Pick your shop from the list",
      reply_markup=markup
  )
  return SME_CAT


def business_details_update(update, context):
  print ('Entered business details update')
  bot = context.bot
  chat_id = update.callback_query.message.chat.id
  choice = update.callback_query.data
  # create business
  new_sme = client.query(
      q.create(
          q.collection("Business"),
          {"data":{
              "name":context.user_data["sme_dets"][0],
              "email":context.user_data["sme_dets"][1],
              "address":context.user_data["sme_dets"][2],
              "telephone":context.user_data["sme_dets"][3],
              "category":choice.lower()
          }}
      )
  )
  context.user_data["sme_name"] = context.user_data["sme_dets"][0]
  context.user_data["sme_id"] = new_sme["ref"].id()
  context.user_data["sme_cat"] = choice
  button = [[
      InlineKeyboardButton(
          text="Add a product",
          callback_data=choice.lower()
      )
  ]]
  bot.send_message(
      chat_id=chat_id,
      text="Business account created successfully, "
      "let's add some products shall we!.",
      reply_markup=InlineKeyboardMarkup(button)
  )
  return ADD_PRODUCTS

def add_product(update, context):
  print ('Entered add product')
  bot = context.bot
  chat_id = update.callback_query.message.chat.id
  bot.send_message(
      chat_id=chat_id,
      text="Add the Name, Description, and Price of product, "
      "separated by commas(,) as caption to the product's image."
      "Please make sure to enter price as a NUMBER ONLY without $ or commmas."
  )
  return ADD_PRODUCTS

def product_info(update: Update, context: CallbackContext):
  try:
      bot = context.bot
      chat_id = update.message.chat.id
      photo = bot.getFile(update.message.photo[-1].file_id)
      file_path = 'product_image.jpg'
      photo.download(file_path)

      data = update.message.caption.split(',')
      if len(data) != 3:
          raise ValueError("Caption format is incorrect.")

      # Processing the price to remove non-numeric characters like '$'
      price = data[2].strip()
      price = ''.join(filter(str.isdigit, price)) or '0'
      price = float(price)

      send_photo = upload(file_path, width=200, height=150, crop='thumb')
      if 'secure_url' not in send_photo:
          raise ValueError("Image upload failed.")

      newprod = client.query(
          q.create(
              q.collection("Products"),
              {"data": {
                      "name": data[0].strip(),
                      "description": data[1].strip(),
                      "price": price,
                      "image": send_photo["secure_url"],
                      "sme": context.user_data["sme_name"],
                      "sme_chat_id": chat_id,
                      "category": context.user_data["sme_cat"]
                  }
              }
          )
      )

      client.query(
          q.update(
              q.ref(q.collection("Business"), context.user_data["sme_id"]),
              {"data": {"latest": newprod["ref"].id()}}
          )
      )

      button = [
          [InlineKeyboardButton(text='Add another product', callback_data=context.user_data["sme_name"])],
          [InlineKeyboardButton(text='Finalize Store Setup', callback_data='cancel')]
      ]
      update.message.reply_text("Added product successfully", reply_markup=InlineKeyboardMarkup(button))

      return ADD_PRODUCTS

  except Exception as e:
      logging.error(f"Error in product_info: {e}")
      bot.send_message(chat_id, "An error occurred while processing the product. Please try again.")
      return ADD_PRODUCTS



## CUSTOMER
def customer_pref(update, context):
    bot = context.bot
    chat_id = update.callback_query.message.chat.id
    data = update.callback_query.data
    print(data)
    # get all businesses in category
    try:
        smes_ = client.query(
            q.map_(
                lambda var: q.get(var),
                q.paginate(
                    q.match(
                        q.index("business_by_category"),
                        str(data).lower()
                    )
                )
            )
        )
        print(smes_)
        for sme in smes_["data"]:
            button = [
                [
                    InlineKeyboardButton(
                        text="View Products",
                        callback_data=sme["data"]["name"]
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Return to Shop List",
                        callback_data="pref"+','+sme["data"]["name"]
                    )
                ]
            ]
            if "latest" in sme['data']:
                thumbnail = client.query(q.get(q.ref(q.collection("Products"), sme["data"]["latest"])))
                print(thumbnail)
                bot.send_photo(
                    chat_id=chat_id,
                    photo=thumbnail["data"]["image"],
                    caption=f"{sme['data']['name']}",
                    reply_markup=InlineKeyboardMarkup(button)
                )
            else:
                bot.send_message(
                    chat_id=chat_id,
                    text=f"{sme['data']['name']}",
                    reply_markup=InlineKeyboardMarkup(button)
                )
    except NotFound:
        button = [[
            InlineKeyboardButton(
                text="Select another Category?",
                callback_data="customer"
            )
        ]]
        bot.send_message(
            chat_id=chat_id,
            text="Nothing here yet",
            reply_markup=InlineKeyboardMarkup(button)
        )
        return CLASS_STATE
    return SHOW_STOCKS

def show_products(update, context):
  bot = context.bot
  chat_id = update.callback_query.message.chat.id
  data = update.callback_query.data

  try:
      print(f"Data received in show_products: {data}")

      if "pref" in data:
          data = data.split(',')[1].replace(' ', '')
          print(f"Processing preference data: {data}")

          user_ref = q.match(q.index('users_by_name'), context.user_data['user-data']['name'])
          user = client.query(q.get(user_ref))
          print(f"User data retrieved: {user}")

          # Update preference
          client.query(
              q.update(
                  q.ref(q.collection('Users'), user['ref'].id()),
                  {'data': {'preference': user['data']['preference'] + data + ','}}
              )
          )

          button = [
              [InlineKeyboardButton(text="View more businesses category", callback_data='customer')]
          ]
          bot.send_message(
              chat_id=chat_id,
              text="Updated preference successfully!!",
              reply_markup=InlineKeyboardMarkup(button)
          )
          return CLASS_STATE

      products = client.query(
          q.map_(
              lambda x: q.get(x),
              q.paginate(
                  q.match(q.index("product_by_business"), update.callback_query.data)
              )
          )
      )
      print(f"Products retrieved: {products}")

      for product in products["data"]:
          context.user_data["sme_id"] = product['data']['sme']
          button = [
              [InlineKeyboardButton(text="Send Order", callback_data="order;" + product["ref"].id())],
              [InlineKeyboardButton(text="Contact business owner", callback_data="contact;" + product["data"]["sme"])],

          ]

          bot.send_photo(
              chat_id=chat_id,
              photo=product["data"]["image"],
              caption=f"{product['data']['name']} \nDescription: {product['data']['description']}\nPrice:{product['data']['price']}",
              reply_markup=InlineKeyboardMarkup(button)
          )

      return POST_VIEW_PRODUCTS

  except Exception as e:
      print(f"Error in show_products: {e}")
      # Send a message to the admin or log the error for further investigation

def post_view_products(update, context):
  bot = context.bot
  chat_id = update.callback_query.message.chat.id
  data = update.callback_query.data

  try:
      # Check if data contains the expected separator
      if ';' in data:
          action, product_id = data.split(';')
          print(f"Action: {action}, Product ID: {product_id}")
      else:
          action = data
          print(f"Action: {action}")

      # Handling 'contact' action
      if 'contact' in action:
          # Fetch the SME's details using the product_id
          sme_details = client.query(
              q.get(
                  q.match(
                      q.index("business_by_name"),
                      product_id
                  )
              )
          )['data']

          # Sending the SME's contact information to the customer
          bot.send_message(
              chat_id=chat_id,
              text=f"Business Name: {sme_details['name']}\nPhone: {sme_details['telephone']}\nEmail: {sme_details['email']}"
          )

      # Handling 'order' action
      elif "order" in action:
          # Fetch the product data from the database using the numeric product_id
          product = client.query(
              q.get(
                  q.ref(
                      q.collection("Products"),
                      int(product_id)
                  )
              )
          )["data"]

          # Sending a message to the SME about the new order
          bot.send_message(
              chat_id=product['sme_chat_id'],
              text="Hey, you have a new order!"
          )

          # Sending the product details to the SME
          bot.send_photo(
              chat_id=product['sme_chat_id'],
              caption=f"Name: {product['name']}\nDescription: {product['description']}\nPrice: {product['price']}"
                      f"\nCustomer's Name: {context.user_data['user-name']}",
              photo=product['image']
          )

          # Sending the customer's contact information to the SME
          # Ensure the phone number is in international format
          bot.send_contact(
              chat_id=product['sme_chat_id'],
              phone_number=context.user_data['user-data']['telephone'],
              first_name=context.user_data['user-data']['name']
          )

          # Confirming to the customer that the order was placed
          bot.send_message(
              chat_id=chat_id,
              text="Order placed successfully."
          )

      # Handling other actions
      else:
          # Handle other actions or send an error message
          bot.send_message(
              chat_id=chat_id,
              text="Sorry, I didn't understand that action."
          )

  except Exception as e:
      print(f"Error in post_view_products: {e}")
      # Send an error message to the user
      bot.send_message(
          chat_id=chat_id,
          text="Sorry, there was an error processing your request."
      )
