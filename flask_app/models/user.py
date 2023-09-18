from flask_app.config.mysqlconnection import connectToMySQL
from flask import flash
from flask_app.models import history
import re



EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

class User:

    def __init__(self, data):
        self.id = data['id']
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        self.email = data['email']
        self.password = data['password']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']
        self.favorites = []

    @classmethod
    def get_one(cls, data):
        query = 'SELECT * from users WHERE id = %(id)s'

        results = connectToMySQL('restaurant_finder').query_db(query, data)
        return cls(results[0])

    @classmethod
    def get_one_by_email(cls, data):
        sql = 'SELECT * FROM users WHERE email=%(email)s;'

        results = connectToMySQL('restaurant_finder').query_db(sql, data)
        if len(results) < 1:
            return False
        return cls(results[0])

    @classmethod
    def get_one_by_place_id(cls, data):
        sql = 'select * from history where place_id=%(place_id)s;'

        results = connectToMySQL('restaurant_finder').query_db(sql, data)
        if len(results) < 1:
            return False
        return cls(results[0])

    @classmethod
    def get_all(cls):
        query = 'SELECT * FROM users;'

        results = connectToMySQL('restaurant_finder').query_db(query)

        users = [cls(person) for person in results]

        return users
        
    @classmethod
    def add_user(cls, data):
        query = '''INSERT INTO users(first_name, last_name, password, email, created_at, updated_at) 
        VALUES(%(first_name)s, %(last_name)s, %(password)s, %(email)s, NOW(), NOW());'''

        results =  connectToMySQL('restaurant_finder').query_db(query, data)
        return results

    @classmethod
    def edit(cls, data):
        query = '''UPDATE users
        SET first_name=%(first_name)s, price_level=%(price_level)s, rating=%(rating)s, location=%(location)s,  updated_at=NOW()
        WHERE id=%(id)s;'''

        return connectToMySQL('restaurant_finder').query_db(query, data)
        

    @classmethod
    def delete(cls, data):
        query = 'DELETE FROM users WHERE id=%(id)s'

        return connectToMySQL('restaurant_finder').query_db(query, data)
        
    @classmethod
    def add_favorite(cls, data):
        sql = 'INSERT INTO favorites(user_id, history_id) VALUES(%(user_id)s, %(history_id)s);'

        results = connectToMySQL('restaurant_finder').query_db(sql, data)

        return results
    
    @classmethod
    def delete_favorite(cls, data):
        sql = 'DELETE FROM favorites WHERE user_id=%(user_id)s and history_id=%(history_id)s;'

        return connectToMySQL('restaurant_finder').query_db(sql, data)

    @classmethod
    def get_fav(cls, data):
        sql = 'select * from favorites where user_id=%(user_id)s and history_id=%(history_id)s;'
        
        return connectToMySQL('restaurant_finder').query_db(sql, data)

    @classmethod
    def get_favorites_with_users(cls, data):
        sql = '''SELECT * FROM users LEFT JOIN favorites ON 
        favorites.user_id = users.id LEFT JOIN history ON 
        favorites.history_id = history.id WHERE users.id = %(id)s;'''

        results = connectToMySQL('restaurant_finder').query_db(sql, data)
        fav = cls(results[0])

        for row in results:
            restaurant_data = {
                "id": row['history.id'], 
                "name": row['name'],
                "origin": row['origin'],
                "place_id": row['place_id'],
                "price_level": row['price_level'],
                "rating": row['rating'],
                "location": row['location'],
                "created_at": row['history.created_at'],
                "updated_at": row['updated_at'],
                "user_id": row['user_id']
            }
            fav.favorites.append(history.History(restaurant_data))
        
        return fav

    @staticmethod
    def validate_user(user):
        is_valid = True
        if len(user['first_name']) < 2:
            flash('First name must be at least 2 characters long', 'registration_error')
            is_valid = False
        if len(user['last_name']) < 2:
            flash('Last name must be at least 2 characters long', 'registration_error')
            is_valid = False
        if not EMAIL_REGEX.match(user['email']):
            flash('Please enter a valid email', 'error')
            is_valid = False
        if len(user['password']) < 8:
            flash('Password must be at least 8 characters long', 'registration_error')
            is_valid = False
        if User.special_character_count(user['password']) < 1:
            flash('Password needs at least one uppercase character', 'registration_error')
            is_valid = False
        if User.digit_count(user['password']) < 1:
            flash('Password needs at least one number', 'registration_error')
            is_valid = False
        if user['confirm'] != user['password']:
            flash('confirmation password and password did not match', 'registration_error')
            is_valid = False
        if User.get_one_by_email({'email':user['email']}) != False:
            flash('email already in use')
            is_valid = False

        return is_valid
    
    @staticmethod
    def special_character_count(string):
        counter = 0
        for char in string:
            if char.isupper():
                counter +=1
        
        return counter
    
    @staticmethod
    def digit_count(string):
        counter = 0
        for char in string:
            if char.isdigit():
                counter += 1

        return counter