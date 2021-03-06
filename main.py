import logging

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import RequestHandler, WSGIApplication, template, blobstore_handlers
from os.path import join, dirname

from models import StarTrip, Location, SpaceShip


class HomeHandler(RequestHandler):
    """ Load latest trips and all locations, for filtering """
    def get(self):
        logging.info("In HomeHandler")
        locations = Location.get_all()
        trips, params = StarTrip.query_from_request(self.request)
        template_values = {'trips': trips, 'locations': locations}
        template_values.update(params)
        html = render('home.html', template_values)
        self.response.write(html)

    def post(self):
        self.get()


class StarTripHandler(RequestHandler):
    def get(self, trip_id=None):
        """ Display an existing star trip or create a new one """
        if trip_id:
            star_trip = StarTrip.get_by_id(int(trip_id))
            if not star_trip:
                self.response.out.write("Trip Not found")
                self.error(404)
                return
            html = render('star_trip.html', {'trip': star_trip})
        else:
            locations = Location.get_all()
            html = render('star_trip_form.html', {'locations': locations})
        self.response.write(html)

    def post(self, trip_id=None):
        """ Create a new trip """
        try:
            StarTrip.save_from_request(self.request)
        except Exception as e:
            self.error(403)
            self.response.out.write(e)
            return
        self.redirect('/')


class LocationHandler(RequestHandler):
    def get(self):
        """ Display a location creation form """
        html = render('location.html')
        self.response.write(html)

    def post(self):
        """ Create a new location (or override existing) """
        try:
            Location.save_from_request(self.request)
        except Exception as e:
            self.error(403)
            self.response.out.write(e)
            return
        self.redirect('/')


class SpaceShipHandler(blobstore_handlers.BlobstoreUploadHandler):
    def get(self):
        """ Display a SpaceShip creation form """
        upload_url = blobstore.create_upload_url('/create_spaceship')
        html = render('spaceship.html', {'upload_url': upload_url})
        self.response.write(html)

    def post(self):
        """ Create a new spaceship (or override existing) """
        try:
            upload = self.get_uploads()[0]
            SpaceShip.save_from_request(self.request, upload)
        except Exception as e:
            self.error(403)
            logging.exception(e)
            self.response.out.write(e)
            return
        self.redirect('/spaceships')


class SpaceShipsHandler(blobstore_handlers.BlobstoreUploadHandler):
    def get(self):
        """ Display a SpaceShip creation form """
        ships = SpaceShip.query().fetch()
        html = render('spaceships.html', {'ships': ships})
        self.response.write(html)


app = WSGIApplication([
    ('/spaceships', SpaceShipsHandler),
    ('/create_spaceship', SpaceShipHandler),
    ('/create_location', LocationHandler),
    (r'/star_trip/?(?P<trip_id>[\w-]*)', StarTripHandler),
    ('/.*', HomeHandler),
], debug=True)


def render(tmpl_file, values={}):
    path = join(dirname(__file__), 'templates', tmpl_file)
    return template.render(path, values)
