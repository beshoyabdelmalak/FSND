#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import (
  Flask, 
  render_template, 
  request, Response, 
  flash, 
  redirect, 
  url_for, 
  jsonify
)
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import db, Venue, Artist, Show, app

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
  # get the venues with future shows
  venues = db.session.query(Venue).all()
  
  # create a set of different locations
  locations = set()
  for venue in venues:
    upcoming_shows = 0
    for show in venue.shows:
      if show.start_time <  datetime.now():
        continue

      upcoming_shows +=1

    if not venue.city in locations:
      locations.add(venue.city)
      data.append({
        "city" : venue.city,
        "state" : venue.state,
        "venues" : [{
          "id" : venue.id,
          "name" : venue.name,
          "num_upcoming_shows": upcoming_shows
        }]
      })
    else:
      for item in data:
        if item['city'] == venue.city:
          item['venues'].append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": upcoming_shows
          })

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search = request.form.get('search_term', '')
  look_for = '%{0}%'.format(search)
  result = Venue.query.filter(Venue.name.ilike(look_for)).all()
  response={
    "count": len(result),
    "data": result
  }
  return render_template('pages/search_venues.html', results=response, search_term=search)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  data = {}
  venue = Venue.query.get(venue_id)
  if not venue:
    return render_template('pages/show_venue.html', venue=data)
  # copy all the object to a dict
  data.update(venue.__dict__)

  # handle the genres
  genres = venue.genres.split(',')
  data['genres'] = genres

  # handle past and upcoming shows
  data.update({
    'past_shows' : [],
    'upcoming_shows' : [],
    'past_shows_count' : 0,
    'upcoming_shows_count' : 0
  })

  past = 0
  upcoming = 0
  for show in venue.shows:
    show_details = {
      'artist_id': show.artist_id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': show.start_time
    }
    if show.start_time > datetime.now():
      upcoming += 1
      data['upcoming_shows'].append(show_details)
    else:
      past +=1
      data['past_shows'].append(show_details)
  
  data['past_shows_count'] = past
  data['upcoming_shows_count'] = upcoming
  
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    data = request.form
    name = data['name']
    genres = ','.join(data.getlist('genres'))
    city = data['city']
    state = data['state']
    address = data['address']
    phone = data['phone']
    facebook_link = data['facebook_link']

    venue = Venue(name=name, genres=genres, city=city, state=state, address=address,
      phone=phone, facebook_link=facebook_link)
    
    db.session.add(venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except :
    db.session.rollback()
    flash('An error occurred. Venue ' + data['name'] + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  venue = Venue.query.get(venue_id)
  if not venue:
    flash('Venue was not foud')

  name = venue.name
  try:
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + name + ' was deleted')
  except :
    db.session.rollback()
    flash('An Error Ocuured Venue ' + name + ' could not be deleted')
  finally:
    db.session.close()

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = db.session.query(Artist.id, Artist.name).all()

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search = request.form.get('search_term', '')
  look_for = '%{0}%'.format(search)
  result = Artist.query.filter(Artist.name.ilike(look_for)).all()
  response = {
      "count": len(result),
      "data": result
  }
  return render_template('pages/search_artists.html', results=response, search_term=search)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  data = {}
  artist = Artist.query.get(artist_id)
  if not artist:
    return render_template('pages/show_artist.html', artist=data)
  
  # copy all the object to a dict
  data.update(artist.__dict__)

  # handle the genres
  genres = artist.genres.split(',')
  data['genres'] = genres

  # handle past and upcoming shows
  data.update({
      'past_shows': [],
      'upcoming_shows': [],
      'past_shows_count': 0,
      'upcoming_shows_count': 0
  })

  past = 0
  upcoming = 0
  for show in artist.shows:
    show_details = {
        'venue_id': show.venue_id,
        'venue_name': show.venue.name,
        'venue_image_link': show.venue.image_link,
        'start_time': show.start_time
    }
    if show.start_time > datetime.now():
      upcoming += 1
      data['upcoming_shows'].append(show_details)
    else:
      past += 1
      data['past_shows'].append(show_details)

  data['past_shows_count'] = past
  data['upcoming_shows_count'] = upcoming
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  artist.genres = artist.genres.split(',')
  form = ArtistForm(obj=artist)

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist = Artist.query.get(artist_id)

  try:
    data = request.form
    artist.name = data['name']
    artist.phone = data['phone']
    artist.state = data['state']
    artist.city = data['city']
    artist.genres = ','.join(data.getlist('genres'))
    artist.facebook_link = data['facebook_link']

    db.session.commit()
    flash('The Artist ' + request.form['name'] +
          ' has been successfully updated!')
  except :
    db.session.rollback()
    flash('The Artist ' + request.form['name'] +
          ' could not be updated!')
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  venue.genres = venue.genres.split(',')
  form = VenueForm(obj=venue)

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = Venue.query.get(venue_id)

  try:
    data = request.form
    venue.name = data['name']
    venue.phone = data['phone']
    venue.state = data['state']
    venue.city = data['city']
    venue.address = data['address']
    venue.genres = ','.join(data.getlist('genres'))
    venue.facebook_link = data['facebook_link']

    db.session.commit()
    flash('The Venue ' + request.form['name'] +
          ' has been successfully updated!')
  except:
    db.session.rollback()
    flash('The Venue ' + request.form['name'] +
          ' could not be updated!')
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  try:
    data = request.form
    name = data['name']
    genres = ','.join(data.getlist('genres'))
    city = data['city']
    state = data['state']
    phone = data['phone']
    facebook_link = data['facebook_link']

    artist = Artist(name=name, genres=genres, city=city, state=state,
                  phone=phone, facebook_link=facebook_link)

    db.session.add(artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + data['name'] + ' could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data = []
  upcoming_shows = db.session.query(Show).all()
  for show in upcoming_shows:
    data.append({
      'venue_id' : show.venue_id,
      'venue_name' : show.venue.name,
      'artist_id' : show.artist_id,
      'artist_image_link': show.artist.image_link,
      'start_time' : show.start_time
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    data = request.form
    artist_id = data['artist_id']
    venue_id = data['venue_id']
    start_time = data['start_time']

    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)

    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()

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
