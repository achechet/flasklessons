import sqlite3
import time
import math

class FDataBase:
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()
        
    def getMenu(self):
        sql = '''SELECT * FROM mainmenu'''
        try:
            self.__cur.execute(sql)
            res = self.__cur.fetchall()
            if res: return res
        except:
            print("Ошибка чтения из БД")
        return[]
    
    def addPost(self, title, text, url):
        try:
            self.__cur.execute("SELECT COUNT() as 'count' FROM posts WHERE url LIKE '{url}'")
            res = self.__cur.fetchone()
            if res['count'] > 0:
                print("Статья с таким именем уже существует")
                return False
            
            tm = math.floor(time.time())
            self.__cur.execute("INSERT INTO posts VALUES(NULL, ?, ?, ?, ?)", (title, url, text, tm))
            self.__db.commit()            
        except sqlite3.Error as e:
            print("Ошибка добавления статьи в БД" + ' ' + str(e))  
            return False      
    
        return True
    
    def getPost(self, postId):
        try:
            self.__cur.execute(f"SELECT title, text FROM posts WHERE id = {postId} LIMIT 1")
            res = self.__cur.fetchone()
            if res:
                return res
        except sqlite3.Error as e:
            print("Ошибка получения стастьи из БД" + ' ' + str(e))
        
        return (False, False)       
    
    def getPostAnonce(self):
        try:
            self.__cur.execute(f"SELECT id, title, text, url FROM posts ORDER BY time DESC")
            res = self.__cur.fetchall()
            if res: return res            
        except sqlite3.Error as e:
            print("Ошибка получения стсьи из БД " +str(e))
        
        return []
    
    