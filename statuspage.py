"""
This module serves as a status page for the Tangerine database. The webpage
  is served at the default port 8080.
"""
import web

class Statuspage(object):
    """Render for the main page"""
    def GET(self):
        return render.index(tasks = postgres.tasks)

def start_statuspage(pg):
    """
    Start the server
    
    Arguments:
        pg: The postgres class instance used in the main program
    """
    global postgres, render, app, urls
    
    postgres = pg
    
    urls = ('/', 'Statuspage')
    app = web.application(urls, globals())
    render = web.template.render('static/')
    
    app.run()