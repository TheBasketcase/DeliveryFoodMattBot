import mysql.connector
import logging
import dbworks
import telegram
from datetime import date
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, ForceReply
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters, ConversationHandler
bot=telegram.Bot(token)
mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password=password,
        database="deliveryfoodbotdb",
        autocommit=True
        )
mycursor = mydb.cursor(buffered=True)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

query_prod = "SELECT Prod_Name FROM products"
mycursor.execute(query_prod)
res_prod = mycursor.fetchall()
good = [i[0] for i in res_prod]

logger = logging.getLogger(__name__)
#PREP,ORDERING = range(2)
#shop, cart, history, order = range(4)

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Привет! Тебя приветствует DeliveryFoodMattBot.')
    dbworks.userins(update, context)
    keyboard = [
        [
            InlineKeyboardButton("Перейти в магазин", callback_data=str(shop))],
            [InlineKeyboardButton("Открыть корзину", callback_data=str(cart))],
            [InlineKeyboardButton("Посмотреть историю заказов", callback_data=str(history)),
        ],
    [InlineKeyboardButton("Оформить заказ", callback_data=str(order))],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Главное меню:', reply_markup=reply_markup)
def shop(update: Update, context: CallbackContext)-> int:
    query = update.callback_query
    keyboard=[[InlineKeyboardButton('Бакалея',callback_data='Бакалея')],
                [InlineKeyboardButton('Мясо',callback_data='Мясо')],
                  [InlineKeyboardButton('Рыба',callback_data='Рыба')],
                  [InlineKeyboardButton('Молоко',callback_data='Молоко')],
                  [InlineKeyboardButton('Назад',callback_data='Назад')]]
    reply_markup=InlineKeyboardMarkup(keyboard)
    bot.edit_message_reply_markup(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=reply_markup)

def shopsearch(usermessage,chatid):
    query = "SELECT * FROM products WHERE Prod_Category LIKE %s"
    mycursor.execute(query,("%" + usermessage + "%",))
    for result in mycursor.fetchall():
        for n in range(2,5):
            if (n == 2):
                bot.send_message(chatid,result[n])
            elif (n == 3):
                bot.send_message(chatid,"Цена товара: " + str(result[n])+" руб.")
            else:
                good = result[2]
                keyboard =[[
                    InlineKeyboardButton("Добавить в корзину", callback_data=good)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                bot.send_photo(chatid,result[n],reply_markup=reply_markup)
                
def cart(update: Update, context: CallbackContext)-> int:
    chatid =  update.callback_query.message.chat.id
    query_cart = "SELECT * FROM cart WHERE User_ID LIKE %s AND Date_of_Delete is NULL"
    mycursor.execute(query_cart,("%" + str(chatid) + "%",))
    if mycursor.rowcount:
        for result in mycursor.fetchall():
            for n in range (0,5):
                if (n==2):
                    bot.send_message(chatid,result[n])
                if (n==3):
                    cartid = result[0]
                    keyboard =[[
                        InlineKeyboardButton("Удалить из корзины", callback_data=str(cartid))]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    bot.send_message(chatid,"Цена товара: " + str(result[n]) + " руб.",reply_markup=reply_markup)
    else:
        bot.send_message(chatid,"Ваша корзина на данный момент пуста")
    
def order(update, context):
    chatid =  update.callback_query.message.chat.id
    query = "SELECT cart_ID FROM cart WHERE User_ID LIKE %s AND Date_of_Delete is NULL"
    mycursor.execute(query,("%" + str(chatid) + "%",))
    if mycursor.fetchone():
        query_ord = "INSERT INTO orders (ID_User,Ord_Date,Ord_Price) VALUES (%s,%s,%s)"
        val = (chatid,date.today(),dbworks.summary(chatid))
        mycursor.execute(query_ord,val)
        id = mycursor.lastrowid
        mydb.commit()
        insprodorder(update,context,id)
    else:
        bot.send_message(chatid,"Ваша корзина на данный момент пуста, оформление заказа невозможно")

        
def insprodorder(update, context,ordid):
    chatid =  update.callback_query.message.chat.id
    query = "SELECT Cart_ID FROM cart WHERE User_ID LIKE %s AND Date_of_Delete is NULL"
    mycursor.execute(query,("%" + str(chatid) + "%",))
    total_rows = int(mycursor.rowcount)
    queryprod = "select Prod_Name, Prod_Price, Prod_ID from cart WHERE User_ID LIKE %s AND Date_of_Delete is NULL"
    mycursor.execute(queryprod,("%" + str(chatid) + "%",))
    names, prices,ids = zip(*mycursor.fetchall())
    for i in range(0,total_rows):
        finquery = "INSERT INTO prod_order (Order_ID,Product_Name,Prod_Price,Prod_ID) VALUES (%s,%s,%s,%s)"
        val = (ordid,names[i],prices[i],ids[i])
        mycursor.execute(finquery,val)
        mydb.commit()
    mycursor.execute(query,("%" + str(chatid) + "%",))
    myresult = mycursor.fetchall()
    for i in myresult:
        for n in range(0,1):
            dbworks.delete_from_cart(i[n])
            mydb.commit()
    bot.send_message(chatid,"Ваш заказ был оформлен")
    mydb.commit()
        
    
def history(update: Update, context: CallbackContext):
    chatid =  update.callback_query.message.chat.id
    query = "SELECT * FROM orders WHERE ID_User LIKE %s"
    mycursor.execute(query,("%" + str(chatid) + "%",))
    if mycursor.rowcount:
        for result in mycursor.fetchall():
            for n in range(0,4):
                if (n==2):
                    bot.send_message(chatid,str(result[n]))
                if (n==3):
                    ordid = result[0]
                    keyboard =[[
                    InlineKeyboardButton("Вывести подробности о заказе", callback_data=str(ordid))]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    bot.send_message(chatid,"Цена заказа: " + str(result[n]) + " руб.",reply_markup=reply_markup)
    else:
        bot.send_message(chatid,"На данный момент Вами не было оформлено ни одного заказа")
            
def listcart(update: Update, context: CallbackContext):
    chatid =  update.callback_query.message.chat.id
    query_cart = "SELECT Cart_ID FROM cart WHERE User_ID LIKE %s AND Date_of_Delete is NULL"
    mycursor.execute(query_cart,("%" + str(chatid) + "%",))
    res_cart = mycursor.fetchall()
    cartid = [i[0] for i in res_cart]
    return cartid 

def listord(update: Update, context: CallbackContext):
    chatid =  update.callback_query.message.chat.id
    query_ord = "SELECT Ord_ID FROM orders WHERE ID_User LIKE %s"
    mycursor.execute(query_ord,("%" + str(chatid) + "%",))
    res_ord = mycursor.fetchall()
    ordid = [i[0] for i in res_ord]
    return ordid
    
def button(update: Update, context: CallbackContext) -> int:
    chatid =  update.callback_query.message.chat.id
    cartid = listcart(update,context)
    ordid = listord(update,context)
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    #query.edit_message_text(text=f"Переход: {query.data}")
    choice = query.data
    if choice == str(shop):
        shop(update,context)
    if choice == str(cart):
        cart(update,context)
    if choice == str(order):
        order(update,context)
    if choice == str(history):
        history(update,context)
    if choice == 'Бакалея':
        shopsearch('Бакалея',chatid)
    if choice == 'Мясо':
        shopsearch('Мясо',chatid)
    if choice == 'Рыба':
        shopsearch('Рыба',chatid)
    if choice == 'Молоко':
        shopsearch('Молоко',chatid)
    if choice == 'Назад':
        keyboard = [
        [InlineKeyboardButton("Перейти в магазин", callback_data=str(shop))],
        [InlineKeyboardButton("Открыть корзину", callback_data=str(cart))],
        [InlineKeyboardButton("Посмотреть историю заказов", callback_data=str(history)),
        ],
        [InlineKeyboardButton("Оформить заказ", callback_data=str(order))],
    ]
        reply_markup=InlineKeyboardMarkup(keyboard)
        bot.edit_message_reply_markup(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=reply_markup)
    if choice in good:
        price = dbworks.show_price(choice)
        prod_ID = dbworks.show_ID(choice)
        adddate = date.today()
        dbworks.addtocart(chatid,choice,price,adddate,prod_ID)
        x = str(choice) + ' 1 штука добавлена в корзину'
        bot.send_message(chatid,x)
    if choice in str(cartid):
        dbworks.delete_from_cart(choice)
        bot.send_message(chatid,"Товар был удалён из корзины")
    if choice in str(ordid):
        dbworks.show_ord(choice,chatid)
        

def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Напишите /start, чтобы начать работу с ботом.")


def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(Token)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_handler(CommandHandler('help', help_command))
    #updater.dispatcher.add_handler((MessageHandler(Filters.text, get_text)))
    #updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, updater))
    #conv_handler = ConversationHandler(
      #entry_points=[CommandHandler('start', start)],
      #states={
             #PREP: [CommandHandler('order',order)],
             #ORDERING: [
           #CommandHandler('cancel', cancel),  # has to be before MessageHandler to catch `/cancel` as command, not as `text`
           #MessageHandler(Filters.text, get_text)],
           #},
        #fallbacks=[CommandHandler('cancel', cancel)],
    #)

    #updater.dispatcher.add_handler(conv_handler)
    
    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
