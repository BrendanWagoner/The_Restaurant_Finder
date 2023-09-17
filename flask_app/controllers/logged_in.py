from flask import Flask, render_template, redirect, request, session, flash, jsonify
from flask_app import app
from flask_bcrypt import Bcrypt
from flask_app.models import user, history
import requests, os, re

bcrypt = Bcrypt(app)
CLEANR = re.compile('<.*?>')

@app.route('/')
@app.route('/login')
def login_index():

    return render_template('user/login.html')

@app.route('/register', methods=['POST'])
def register():
    if not user.User.validate_user(request.form):
        return redirect('/')
    
    pw_hash = bcrypt.generate_password_hash(request.form['password'])

    data = {
        'first_name': request.form['first_name'],
        'last_name': request.form['last_name'],
        'email': request.form['email'],
        'password': pw_hash
    }

    user_id = user.User.add_user(data)
    if 'user_id' not in session:
        session['user_id'] = user_id
    session['user_id'] = user_id

    return redirect(f'/{user_id}/search')

@app.route('/login', methods=['POST'])
def login():
    data = {
        'email': request.form['email']
    }
    u = user.User.get_one_by_email(data)

    if not u:
        flash('invalid email/password', 'login_error')
        return redirect('/')
    if not bcrypt.check_password_hash(u.password, request.form['password']):
        flash('invalid email/password', 'login_error')
        return redirect('/')
    session['user_id'] = u.id

    return redirect(f'/{u.id}/search')

@app.route('/logout')
def logout():
    session.clear()

    return redirect('/login')

@app.route('/<int:id>/search')
def user_search_index(id):
    if 'user_id' not in session:
        return redirect('/search')

    favs=user.User.get_favorites_with_users({'id': id}).favorites
    print(favs[0].name)

    return render_template('user/user_search.html', user=user.User.get_one({'id': id}), favs=user.User.get_favorites_with_users({'id': id}).favorites)

@app.route('/<int:id>/search/<address>', methods=['GET'])
def user_api_call_render(id, address):
    print(address)

    if 'user_id' not in session:
        return redirect('/search')

    geocoding_api_results = requests.get(f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={os.environ.get("GEOCODING_API_KEY")}')

    if geocoding_api_results.json()['results']:
        geocoding_results = geocoding_api_results.json()['results'][0]['geometry']['location']
        # print(geocoding_api_results.json())
        lat = geocoding_results['lat']  
        lng = geocoding_results['lng']

        place_api_results = requests.get(f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat}%2C{lng}&radius=1500&type=restaurant&key={os.environ.get("FLASK_APP_API_KEY")}')
        results = place_api_results.json()['results']
        print(results[0])
        return render_template("user/user_restaurant.html", google_response=results, user=user.User.get_one({'id':session['user_id']}))
    else:
        flash('Not a valid address', 'search_error')
        return redirect(f'/{session["user_id"]}/search')
    
@app.route('/<int:id>/search/<address>/add_favorite', methods=['POST'])
def search_add_fav(id, address):
    restaurant_id = history.History.get_one_by_address({'address':address}).id
    user.User.add_favorite({'user_id': id, 'history_id':restaurant_id})

    return redirect(f'{id}/search/{address}')


@app.route('/<int:id>/search/<address>/delete_favorite', methods=['POST'])
def search_delete_fav(id, address):
    restaurant_id = history.History.get_one_by_address({'address':address}).id
    user.User.delete_favorite({'user_id': id, 'history_id':restaurant_id})

    return redirect(f'{id}/search/{address}')

@app.route('/<int:id>/favorite')
def favorite(id):
    if 'user_id' not in session:
        return redirect('/search')


    return render_template('user/user_favorite.html', user=user.User.get_one({'id':id}), history=history.History.get_all({'user_id':id}), favs = user.User.get_favorites_with_users({'id':id}).favorites)

@app.route('/<int:id>/directions/<address>/<string:restaurant_place_id>')
def user_directions_index(id, address, restaurant_place_id):
    print(restaurant_place_id)
    history_api_call = requests.get(f'https://maps.googleapis.com/maps/api/place/details/json?placeid={restaurant_place_id}&key={os.environ.get("FLASK_APP_API_KEY")}')
    print(history_api_call.json())
    history_api_result = history_api_call.json()['result']
    # for dict in history_api_result:
    #     print(dict)
    location = history_api_result['formatted_address'].split(',')[1]

    formatted_address = ''
    split_address = address.split(' ')

    for word in split_address:
        formatted_address += word
        formatted_address += '+'

    if 'price_level' in history_api_result:
        data = {
            'name': history_api_result['name'],
            'origin': address,
            'place_id': history_api_result['place_id'],
            'user_id': id,
            'rating': history_api_result['rating'],
            'price_level': history_api_result['price_level'],
            'location': location
        }
    else:
        data = {
            'name': history_api_result['name'],
            'origin': address,
            'place_id': history_api_result['place_id'],
            'user_id': id,
            'rating': history_api_result['rating'],
            'price_level': 'Not Listed',
            'location': location
        }

    if history.History.get_one_by_place_id({'place_id':restaurant_place_id}) == False:
        history.History.add_restaurant(data)

    address_geocoding_api_results = requests.get(f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={os.environ.get("GEOCODING_API_KEY")}')
    address_place_id = address_geocoding_api_results.json()['results'][0]['place_id']

    directions_api_call = requests.get(f'https://maps.googleapis.com/maps/api/directions/json?destination=place_id:{restaurant_place_id}&origin=place_id:{address_place_id}&key={os.environ.get("FLASK_APP_API_KEY")}')
    directions = ''

    for x in directions_api_call.json()['routes'][0]['legs'][0]['steps']:
        directions += x['html_instructions']
        directions += ' '

    formatted_directions = clean_html(directions)
    return render_template('user/user_directions.html', user=user.User.get_one({'id':id}), origin=formatted_address, key=os.environ.get('FLASK_APP_API_KEY'), directions=formatted_directions, place_id=restaurant_place_id)

@app.route('/<int:id>/<int:restaurant_id>/add_favorite', methods=['POST'])
def add_fav(id, restaurant_id):
    user.User.add_favorite({'user_id': id, 'history_id':restaurant_id})

    return redirect(f'/{id}/favorite')

@app.route('/<int:id>/<int:restaurant_id>/delete_favorite', methods=['POST'])
def delete_fav(id, restaurant_id):
    user.User.delete_favorite({'user_id':id, 'history_id':restaurant_id})

    return redirect(f'/{id}/favorite')

def clean_html(directions):
    clean_text = re.sub(CLEANR, ' ', directions)
    return clean_text