import shop_bot
from telegram.ext import (
    CommandHandler,
    CallbackContext,
    ConversationHandler,
    MessageHandler,
    Filters,
    Updater,
    CallbackQueryHandler
)
from config import TOKEN, api_key, api_secret, FAUNA_KEY

updater = Updater(TOKEN, use_context=True)
dispatcher = updater.dispatcher

def main():
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', shop_bot.start)],
        states={
            shop_bot.CHOOSING: [
                MessageHandler(Filters.all, shop_bot.choose)
            ],
            shop_bot.CLASS_STATE: [
                CallbackQueryHandler(shop_bot.classer)
            ],
            shop_bot.SME_DETAILS: [
                MessageHandler(Filters.all, shop_bot.business_details)
            ],
            shop_bot.ADD_PRODUCTS: [
                CallbackQueryHandler(shop_bot.add_product),
                MessageHandler(Filters.all, shop_bot.product_info)
            ],
            shop_bot.SME_CAT: [
                CallbackQueryHandler(shop_bot.business_details_update)
            ],
            shop_bot.CHOOSE_PREF: [
                CallbackQueryHandler(shop_bot.customer_pref)
            ],
            shop_bot.SHOW_STOCKS: [
                CallbackQueryHandler(shop_bot.show_products)
            ],
            shop_bot.POST_VIEW_PRODUCTS: [
                CallbackQueryHandler(shop_bot.post_view_products)
            ]
        },
        fallbacks=[CommandHandler('cancel', shop_bot.cancel)],
        allow_reentry=True
    )
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
