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
        password="password",
        database="deliveryfoodbotdb",
        autocommit=True
        )
mycursor = mydb.cursor()
updater = Updater(Token)

def userins(update,context):
    usID = update.message.from_user.id
    usName = update.message.from_user.first_name + "  " + update.message.from_user.last_name
    sql = "INSERT IGNORE INTO users (User_ID, Nickname) VALUES (%s, %s)"
    val = (usID, usName)
    mycursor.execute(sql, val)
    mydb.commit()
    print(mycursor.rowcount, "record(s) has been inserted.")
                    
def addtocart(id,good,price,adddate):
    query = "INSERT INTO cart (User_ID,Prod_Name,Prod_Price,Date_of_Add) VALUES (%s,%s,%s,%s)"
    val = (id,good,price,adddate)
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
    
def delete_from_cart(cart_ID):
    query = "UPDATE cart SET Date_of_Delete = %s WHERE  Cart_ID = %s"
    data = (date.today(),cart_ID)
    mycursor.execute(query,data)
    mydb.commit()
