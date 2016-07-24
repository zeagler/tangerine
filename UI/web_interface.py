"""
This module serves as the web interface for Tangerine. The webpage
  is served at the default port 8080. Access control is provided
  through GitHub oauth.
"""
import os
import urllib2
import json
import cherrypy
from hashlib import sha256
from settings import Web as options

from mako.template import Template
from mako.lookup import TemplateLookup
lookup = TemplateLookup(directories=['UI/static'])

class Statuspage(object):
    """Render for the web application"""

    @cherrypy.expose
    def index(self, code=None):
        # Redirect HTTP to HTTPS
        if cherrypy.request.scheme == "http":
            redirect_url = cherrypy.request.base
            redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
            redirect_url = redirect_url.replace("http:", "https:")
            raise cherrypy.HTTPRedirect(redirect_url)

        # if this session is already authorized give the user the main page
        if cherrypy.session.get("authorized", None):
            # if this doesn't match the original request force a new session
            agent = cherrypy.request.headers['User-Agent']
            
            if cherrypy.session["_ident"] == sha256(agent).hexdigest():
                tmpl = lookup.get_template("index.html.mako")
                return tmpl.render(tasks = postgres.get_tasks())
            
            # Kill the current session
            else:
                cherrypy.session.clear()
                cherrypy.session.delete()
                cherrypy.lib.sessions.expire()
                raise cherrypy.HTTPRedirect("/")

        # if the `code` parameter was POSTed, try to authenticate the user
        elif code:
            # First check that the code is valid
            # Query GitHub for an access token for the code
            git_auth = "https://github.com/login/oauth/access_token?" + \
                       "client_id=" + options['GITHUB_OAUTH_ID'] + \
                       "&client_secret=" + options['GITHUB_OAUTH_SECRET'] + \
                       "&code=" + code
            
            req = urllib2.Request(git_auth)
            res = urllib2.urlopen(req)
            
            # split the response into a dict
            response = {}
            for param in res.read().split("&"):
                response[param.split("=")[0]] = param.split("=")[1]
            
            # Second, get the GitHub acccount information
            # if the code resulted in a valid access token
            if "access_token" in response.keys():
                # Get the user information
                get_info = "https://api.github.com/user?access_token=" + response['access_token']
                req = urllib2.Request(get_info)
                res = urllib2.urlopen(req)
                
                # Parse the resulting JSON
                data = json.load(res)
                
                # if the user is in the authorized user list
                user_data = postgres.get_user(data['id'])
                if user_data:
                    if user_data[1] == data['login']:
                        # Modify the user session to indicated authorization

                        # store a SHA of the inital request information
                        # if this doesn't match force a new session
                        agent = cherrypy.request.headers['User-Agent']
                        # remote_ip = cherrypy.request.remote.ip
                        cherrypy.session["_ident"] = sha256(agent).hexdigest()

                        # Regenerate the session ID on successful login
                        cherrypy.session.regenerate()
                        
                        # Store user information in the session
                        cherrypy.session["authorized"] = "true"
                        cherrypy.session["userid"] = user_data[0]
                        cherrypy.session["username"] = user_data[1]
                        cherrypy.session["usertype"] = user_data[2]
                        
                        # Send the authorized user to the main page
                        raise cherrypy.HTTPRedirect("/")
                    
                    else:
                        return "Login failed. User '" + data['login'] + "' is not authorized"
                        
                # The user is not authorized
                else:
                    return "Login failed. User '" + data['login'] + "' is not authorized"

            # The code was not valid or not sent by GitHub
            else:
                return "Login failed"

            return "There was an error: " + str(response)

        else:
            raise cherrypy.HTTPRedirect("login")

    @cherrypy.expose
    def login(self):
        # Redirect HTTP to HTTPS
        if cherrypy.request.scheme == "http":
            redirect_url = cherrypy.request.base
            redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
            redirect_url = redirect_url.replace("http:", "https:")
            raise cherrypy.HTTPRedirect(redirect_url)

        # if the session is already authorized send the user to the main page
        if cherrypy.session.get("authorized", None):
            raise cherrypy.HTTPRedirect("/")
          
        # Regenerate the session ID before logging in
        cherrypy.session.regenerate()
        tmpl = lookup.get_template("login.html.mako")
        return tmpl.render(client_id = options['GITHUB_OAUTH_ID'])

    @cherrypy.expose
    def update(self, name=None, column=None, value=None):
        # Redirect HTTP to HTTPS
        if cherrypy.request.scheme == "http":
            redirect_url = cherrypy.request.base
            redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
            redirect_url = redirect_url.replace("http:", "https:")
            raise cherrypy.HTTPRedirect(redirect_url)
          
        # if the session isn't authorized send the user to the login
        if not cherrypy.session.get("authorized", None):
            raise cherrypy.HTTPRedirect("/")
        
        if postgres.update_task(name, column, value):
            return "True"
        else:
            return "False"
   
    @cherrypy.expose
    def add_task(self, name=None, state=None, dep=None, image=None, command=None, entrypoint=None,
                cron=None, restartable=None, exitcodes=None, max_failures=None, delay=None, faildelay=None,
                environment=None, datavolumes=None):
        # Redirect HTTP to HTTPS
        if cherrypy.request.scheme == "http":
            redirect_url = cherrypy.request.base
            redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
            redirect_url = redirect_url.replace("http:", "https:")
            raise cherrypy.HTTPRedirect(redirect_url)
          
        # if the session isn't authorized send the user to the login
        if not cherrypy.session.get("authorized", None):
            raise cherrypy.HTTPRedirect("/")
        
        if not name: return "False"
        if not (state == "queued" or state == "success" or state == "stopped"): return "False"
        if not image: return "False"
      
        postgres.add_task(
                name = name,
                state = state,
                dep = dep,
                image = image,
                command = command,
                entrypoint = entrypoint,
                cron = cron,
                restartable = restartable,
                exitcodes = exitcodes,
                max_failures = max_failures,
                delay = delay,
                faildelay = faildelay,
                environment = environment,
                datavolumes = datavolumes
               )
        return "True"


def secureheaders():
    headers = cherrypy.response.headers
    headers['X-Frame-Options'] = 'DENY'
    headers['X-XSS-Protection'] = '1; mode=block'
    headers['Content-Security-Policy'] = "default-src='self'"
    headers['Strict-Transport-Security'] = 'max-age=31536000' # one year

def start_web_interface(pg):
    """
    Start the server
    
    Arguments:
        pg: The postgres class instance used in the main program
    """
    global postgres
    postgres = pg
    
    # Define the static path for template rendering
    # Enable this if Nginx proxy is not being used
    #conf = {
    #    '/static': {'tools.staticdir.on': True, 'tools.staticdir.dir': os.path.abspath(os.getcwd()) + '/UI/static'},
    #    '/favicon.ico': {'tools.staticfile.on': True, 'tools.staticfile.filename': os.path.abspath(os.getcwd()) + '/UI/static/favicon.ico'}
    #}
    
    # Set the global config.
    cherrypy.tools.secureheaders = cherrypy.Tool('before_finalize', secureheaders, priority=60)
    cherrypy.config.update({
                            'environment': 'production',
                            'tools.sessions.on': True,
                            'tools.sessions.timeout': 45,
                            'tools.sessions.secure': True,
                            'tools.sessions.httponly': True,
                            'tools.secureheaders.on': True,
                            'server.socket_host': '0.0.0.0',
                            'server.socket_port': 443,
                            'server.ssl_module': 'builtin',
                            'server.ssl_certificate': options['SSL_CERTIFICATE'],
                            'server.ssl_private_key': options['SSL_PRIVATE_KEY'],
                            'server.ssl_certificate_chain': options['SSL_CERTIFICATE_CHAIN'],
                           })
    
    #cherrypy.tree.mount(Statuspage(), config=conf) # for static files without Nginx
    cherrypy.tree.mount(Statuspage())

    # Make 2nd server to redirect HTTP to HTTPS
    http_server = cherrypy._cpserver.Server()
    http_server.socket_host = '0.0.0.0'
    http_server.socket_port=80
    http_server.subscribe()

    print "Staring Web Server"
    cherrypy.engine.start()
    cherrypy.engine.block()
    
if __name__ == '__main__':
    from postgres_functions import Postgres
    postgres = Postgres()
    status = start_web_interface(postgres)
    exit(status)