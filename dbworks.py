import mysql.connector
import telegram
import logging
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
mycursor = mydb.cursor()
updater = Updater(token)

def userins(update,context):
    usID = update.message.from_user.id
    usName = update.message.from_user.first_name + "  " + update.message.from_user.last_name
    sql = "INSERT IGNORE INTO users (User_ID, Nickname) VALUES (%s, %s)"
    val = (usID, usName)
    mycursor.execute(sql, val)
    mydb.commit()
    print(mycursor.rowcount, "record(s) has been inserted.")

def insaddress(update,context,address):
    usID = update.message.from_user.id
    if (address != "/cancel"):
        sql = "UPDATE users SET address = %s WHERE User_ID = %s"
        data = (address,usID)
        mycursor.execute(sql,data)
        mydb.commit()
    query = "SELECT address from users WHERE User_ID LIKE %s"
    mycursor.execute(query,("%" + str(usID) + "%",))
    result = mycursor.fetchone()
    curaddress = result[0]
    bot.send_message(usID,"Ваш адрес на данный момент: " + curaddress)

def addtocart(id,good,price,adddate,prod_ID):
    query = "INSERT INTO cart (User_ID,Prod_Name,Prod_Price,Date_of_Add,Prod_ID) VALUES (%s,%s,%s,%s,%s)"
    val = (id,good,price,adddate,prod_ID)
    mycursor.execute(query,val)
    mydb.commit()

def summary(id):
    query = "SELECT SUM(Prod_Price) AS totalsum FROM cart WHERE User_ID LIKE %s AND Date_of_Delete IS NULL"
    mycursor.execute(query,("%" + str(id) + "%",))
    result = mycursor.fetchall()
    for i in result:
        return i[0]
    
def show_price(product):
    query = "SELECT Prod_Price FROM products WHERE Prod_Name LIKE %s"
    mycursor.execute(query,("%" + product + "%",))
    myresult = mycursor.fetchone()
    price = myresult[0]
    return price

def show_ID(product):
    query = "SELECT Prod_ID FROM products WHERE Prod_Name LIKE %s"
    mycursor.execute(query,("%" + product + "%",))
    myresult = mycursor.fetchone()
    id = myresult[0]
    return id

def show_ord(product,id):
    query = "SELECT * from prod_order WHERE Order_ID LIKE %s"
    mycursor.execute(query,("%" + product + "%",))
    myresult = mycursor.fetchall()
    for i in myresult:
        for n in range(0,5):
            if (n == 3):
                bot.send_message(id,i[3])
            if (n == 4):
                bot.send_message(id,"Цена товара: " + str(i[4]) + " руб.")
    
def delete_from_cart(cart_ID):
    query = "UPDATE cart SET Date_of_Delete = %s WHERE  Cart_ID = %s"
    data = (date.today(),cart_ID)
    mycursor.execute(query,data)
    mydb.commit()
