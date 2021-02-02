#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy.dialects.postgresql import ARRAY
import sys


#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app,db)

# TODO: connect to a local postgresql database --- DONE

#----------------------------------------------------------------------------#
# 2nd Import for Models.
#----------------------------------------------------------------------------#

from models import *

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = []
  
  # step taken to query all venues
  venues = Venue.query.all()

  # step implemented to avoid duplicate venues
  fulllocations = set()

  for venue in venues:
    # then we convert to tuples and add city & state data
    fulllocations.add((venue.city, venue.state))

  # check each unique city & state, then add venue data
  for fulllocation in fulllocations:
    data.append({
        "city": fulllocation[0],
        "state": fulllocation[1],
        "venues": []
    })

  for venue in venues:

    upcoming_shows = 0

    shows = Show.query.filter_by(venue_id=venue.id).all()
    
    #check for show start time to established if it is an upcoming or past show
    for show in shows:
      if show.start_time > datetime.now():
          upcoming_shows += 1

    #join show data to the proper venue based on city/state
    for venue_location in data:
      if venue.state == venue_location['state'] and venue.city == venue_location['city']:
        venue_location['venues'].append({
            "id": venue.id,
            "name": venue.name,
            "upcoming_shows": upcoming_shows
        })
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee" --- DONE
  search_term = request.form.get('search_term', '')

  #implemeting search using % for partial search
  venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()

  response = {
    "count": len(venues),
    "data": []
  }

  #get teh results to show them
  for venue in venues:
    response['data'].append({
        "id": venue.id,
        "name": venue.name
      })

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id --- DONE
  venue = Venue.query.get(venue_id)
  
  past_shows_venue = []
  upcoming_shows_venue = []

  query_upcoming_shows_venue = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
  query_past_shows_venue = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()

  for show in query_past_shows_venue:
    past_shows_venue.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": format_datetime(str(show.start_time))
    })

  for show in query_upcoming_shows_venue:
    upcoming_shows_venue.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": format_datetime(str(show.start_time))    
    })

  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows_venue,
    "upcoming_shows": upcoming_shows_venue,
    "past_shows_count": len(past_shows_venue),
    "upcoming_shows_count": len(upcoming_shows_venue)
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead --- DONE
  error = False
  try:
      venue = Venue(name=request.form.get('name'),
      city=request.form.get('city'),
      state=request.form.get('state'),
      address=request.form.get('address'),
      phone=request.form.get('phone'),
      image_link=request.form.get('image_link'),
      genres=request.form.getlist('genres'),
      facebook_link=request.form.get('facebook_link'),
      website = request.form.get('website'),
      seeking_talent = True if 'seeking_talent' in request.form else False,
      seeking_description = request.form.get('seeking_description'))
      db.session.add(venue)
      db.session.commit()
  except:
      db.session.rollback()
      error = True
  finally:
      db.session.close()
  # TODO: modify data to be the data object returned from db insertion --- DONE
  # TODO: on unsuccessful db insert, flash an error instead. --- DONE
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  if error:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
      print(sys.exc_info())
  else:
    # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')


@app.route('/venues/<int:venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using --- DONE
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue was not deleted.')
    print(sys.exc_info())
    return redirect(url_for('venues'))
  else:
    # on successful db insert, flash success
    flash('Venue deleted')
    return render_template('pages/home.html')
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage --- DONE
  

 

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database --- DONE
    
  # query all artists
  data = Artist.query.all()

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band". --- DONE
  search_term = request.form.get('search_term', '')

  #implemeting search using % for partial search
  artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

  response = {
    "count": len(artists),
    "data": []
  }

  for artist in artists:
    response['data'].append({
        "id": artist.id,
        "name": artist.name
      })

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id --- DONE
  artist = Artist.query.get(artist_id)
    
  past_shows_artist = []
  upcoming_shows_artist = []

  query_upcoming_shows_artist = Show.query.filter_by(artist_id=artist_id).join(Venue, Show.venue_id == Venue.id).filter(Show.start_time>datetime.now()).all()
  query_past_shows_artist = Show.query.filter_by(artist_id=artist_id).join(Venue, Show.venue_id == Venue.id).filter(Show.start_time<datetime.now()).all()

  for show in query_past_shows_artist:
    past_shows_artist.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": format_datetime(str(show.start_time))
    })  

  for show in query_upcoming_shows_artist:
    upcoming_shows_artist.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": format_datetime(str(show.start_time))
    })

  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows_artist,
    "upcoming_shows": upcoming_shows_artist,
    "past_shows_count": len(past_shows_artist),
    "upcoming_shows_count": len(upcoming_shows_artist)
  }
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  
  artist = Artist.query.get(artist_id)
 
  artist_data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
  }
  # TODO: populate form with fields from artist with ID <artist_id> --- DONE
  return render_template('forms/edit_artist.html', form=form, artist=artist_data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing --- DONE
  # artist record with ID <artist_id> using the new attributes
  error = False
  artist = Artist.query.get(artist_id)
  try:
    #Updated edit_artist.html file to get with default/current values, in order to avoid lost of data when updating
      artist.name = request.form['name']
      artist.city = request.form['city']
      artist.state = request.form['state']
      artist.phone = request.form['phone']
      artist.genres = request.form.getlist('genres')
      artist.image_link = request.form['image_link']
      artist.facebook_link = request.form['facebook_link']
      artist.website = request.form['website']
      artist.seeking_venue = True if 'seeking_venue' in request.form else False 
      artist.seeking_description = request.form['seeking_description']
      db.session.commit()
  except:
      db.session.rollback()
      error = True
  finally:
      db.session.close()
  # TODO: modify data to be the data object returned from db insertion --- DONE
  # TODO: on unsuccessful db insert, flash an error instead. --- DONE
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  if error:
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
      print(sys.exc_info())
  else:
    # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully updated!')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  

  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link
  }

  # TODO: populate form with values from venue with ID <venue_id> --- DONE
  return render_template('forms/edit_venue.html', form=form, venue=data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing --- DONE
  # venue record with ID <venue_id> using the new attributes
  error = False
  venue = Venue.query.get(venue_id)
  try:
    #Updated edit_venue.html file to get with default/current values, in order to avoid lost of data when updating
      venue.name = request.form['name']
      venue.city = request.form['city']
      venue.state = request.form['state']
      venue.address = request.form['address']
      venue.phone = request.form['phone']
      venue.genres = request.form.getlist('genres')
      venue.image_link = request.form['image_link']
      venue.facebook_link = request.form['facebook_link']
      venue.website = request.form['website']
      venue.seeking_talent = True if 'seeking_talent' in request.form else False 
      venue.seeking_description = request.form['seeking_description']
      db.session.commit()
  except:
      db.session.rollback()
      error = True
  finally:
      db.session.close()
  # TODO: modify data to be the data object returned from db insertion --- DONE
  # TODO: on unsuccessful db insert, flash an error instead. --- DONE
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  if error:
      flash('An error occurred. Venue ' + request.form['name']  + ' could not be updated.')
      print(sys.exc_info())
  else:
    # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully updated!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Artist record in the db, instead --- DONE
  error = False
  try:
      artist = Artist(name=request.form.get('name'),
      city=request.form.get('city'),
      state=request.form.get('state'),
      phone=request.form.get('phone'),
      genres=request.form.getlist('genres'),
      facebook_link=request.form.get('facebook_link'),
      image_link=request.form.get('image_link'),
      website = request.form.get('website'),
      seeking_venue = True if 'seeking_venue' in request.form else False,
      seeking_description = request.form.get('seeking_description'))
      db.session.add(artist)
      db.session.commit()
  except:
      db.session.rollback()
      error = True
  finally:
      db.session.close()
  # TODO: modify data to be the data object returned from db insertion --- DONE
  # TODO: on unsuccessful db insert, flash an error instead. --- DONE
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  if error:
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
      print(sys.exc_info())
  else:
    # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data. --- DONE
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  shows = Show.query.join(Artist).join(Venue).all()
  data = []

  for show in shows:
    data.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": format_datetime(str(show.start_time))
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead --- DONE
  error = False
  try:
    show = Show(artist_id=request.form.get('artist_id'),
    venue_id=request.form.get('venue_id'),
    start_time=request.form.get('start_time'))
    db.session.add(show)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()
  if error:
  # TODO: on unsuccessful db insert, flash an error instead. --- DONE
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    print(sys.exc_info())
    flash('An error occurred. Show could not be listed.')
  else:
  # on successful db insert, flash success
    flash('Show was successfully listed!')

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
