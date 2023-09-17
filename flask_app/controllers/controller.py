from flask import Flask, render_template, redirect, request, session, flash, jsonify
from flask_app import app
from flask_bcrypt import Bcrypt
from flask_app.models import user
import requests, os, re

bcrypt = Bcrypt(app)
CLEANR = re.compile('<.*?>')

# @app.route('/<int:id>/searching', methods=['POST'])
# def api_call(id):

#     print("key:", os.environ.get("FLASK_APP_API_KEY"))
#     r = requests.get(f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=-33.8670522%2C151.1957362&radius=1500&type=restaurant&key={os.environ.get("FLASK_APP_API_KEY")}')
#     google_response = r.json()
#     return jsonify(google_response)

@app.route('/search')
def search_index():

    return render_template('search.html')

@app.route('/search/<address>', methods=['GET'])
def api_call_render(address):
    geocoding_api_results = requests.get(f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={os.environ.get("GEOCODING_API_KEY")}')

    if geocoding_api_results.json()['results']:
        geocoding_results = geocoding_api_results.json()['results'][0]['geometry']['location']
        # print(geocoding_api_results.json())
        lat = geocoding_results['lat']  
        lng = geocoding_results['lng']

        place_api_results = requests.get(f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat}%2C{lng}&radius=1500&type=restaurant&key={os.environ.get("FLASK_APP_API_KEY")}')
        results = place_api_results.json()['results']
        print(results[1])
        return render_template("restaurant.html", google_response=results)
    else:
        flash('Not a valid addresss, try again', 'search_error')
        return redirect('/search')

@app.route('/directions/<address>/<string:restaurant_place_id>')
def directions_index(address, restaurant_place_id):
    formatted_address = ''
    split_address = address.split(' ')

    for word in split_address:
        formatted_address += word
        formatted_address += '+'

    address_geocoding_api_results = requests.get(f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={os.environ.get("GEOCODING_API_KEY")}')
    address_place_id = address_geocoding_api_results.json()['results'][0]['place_id']

    directions_api_call = requests.get(f'https://maps.googleapis.com/maps/api/directions/json?destination=place_id:{restaurant_place_id}&origin=place_id:{address_place_id}&key={os.environ.get("FLASK_APP_API_KEY")}')
    directions = ''

    for x in directions_api_call.json()['routes'][0]['legs'][0]['steps']:
        directions += x['html_instructions']
        directions += ' '

    formatted_directions = clean_html(directions)
    return render_template('directions.html', origin=formatted_address, key=os.environ.get('FLASK_APP_API_KEY'), directions=formatted_directions, place_id=restaurant_place_id)

def clean_html(directions):
    clean_text = re.sub(CLEANR, ' ', directions)
    return clean_text
