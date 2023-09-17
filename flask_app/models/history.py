from flask_app.config.mysqlconnection import connectToMySQL
from flask import flash

class History:

    def __init__(self, data):
        self.id = data['id']
        self.name = data['name']
        self.origin = data['origin']
        self.place_id = data['place_id']
        self.rating = data['rating']
        self.price_level = data['price_level']
        self.location = data['location']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']
        self.user_id = data['user_id']

    @classmethod
    def get_one(cls, data):
        query = 'SELECT * from history WHERE id = %(id)s'

        results = connectToMySQL('restaurant_finder').query_db(query, data)
        return cls(results[0])
    
    @classmethod
    def get_one_by_place_id(cls, data):
        sql = 'SELECT * FROM history WHERE place_id=%(place_id)s;'

        results = connectToMySQL('restaurant_finder').query_db(sql, data)
        print(results)
        if len(results) < 1:
            return False
        return cls(results[0])

    @classmethod
    def get_one_by_address(cls, data):
        sql = 'SELECT * FROM history WHERE address=%(address)s;'

        results = connectToMySQL('restaurant_finder').query_db(sql, data)
        print(results)
        if len(results) < 1:
            return False
        return cls(results[0])


    @classmethod
    def get_fav(cls, data):
        sql = 'select * from favorites where user_id=%(user_id)s and history_id=%(history_id)s;'
        
        return connectToMySQL('restaurant_finder').query_db(sql, data)

    @classmethod
    def get_all(cls, data):
        query = 'SELECT * from history WHERE user_id=%(user_id)s;'

        results = connectToMySQL('restaurant_finder').query_db(query, data)

        restaurants = [cls(restaurant) for restaurant in results]

        return restaurants
    
    @classmethod
    def add_restaurant(cls, data):
        query = '''INSERT INTO history(name, origin, place_id, rating, price_level, location, created_at, updated_at, user_id) 
        VALUES(%(name)s, %(origin)s, %(place_id)s, %(rating)s, %(price_level)s, %(location)s, NOW(), NOW(), %(user_id)s);'''

        results =  connectToMySQL('restaurant_finder').query_db(query, data)
        return results
    
    @classmethod
    def edit(cls, data):
        query = '''UPDATE history
        SET name=%(name)s, place_id=%(place_id)s, origin=%(origin)s, rating=%(rating)s, price_level=%(price_level)s, location=%(location)s, updated_at=NOW()
        WHERE id=%(id)s;'''

        return connectToMySQL('restaurant_finder').query_db(query, data)

    @classmethod
    def delete(cls, data):
        query = 'DELETE FROM history WHERE id=%(id)s'

        return connectToMySQL('restaurant_finder').query_db(query, data)