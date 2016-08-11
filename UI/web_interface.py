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
from API import API

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
                return tmpl.render(
                                   username = cherrypy.session['username'],
                                   userimageurl = cherrypy.session['userimageurl'],
                                   usertype = cherrypy.session['usertype']
                                  )
            
            # Kill the current session
            else:
                cherrypy.session.clear()
                cherrypy.session.delete()
                cherrypy.lib.sessions.expire()
                raise cherrypy.HTTPRedirect("/")

        # if the `code` parameter was POSTed, try to authenticate the user
        #elif code:
        if code:
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
                userdata = API.get_users(userid=str(data['id']))
                if userdata:    
                    user_data = userdata[0]
                    if user_data.username == data['login']:
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
                        cherrypy.session["userid"] = user_data.userid
                        cherrypy.session["username"] = user_data.username
                        cherrypy.session["usertype"] = user_data.usertype
                        cherrypy.session["userimageurl"] = data['avatar_url']
                        
                        # Send the authorized user to the main page or previous request
                        redirect = cherrypy.session.get("redirect", "/")
                        if redirect == "/get_tasks":
                            redirect = "/"
                        raise cherrypy.HTTPRedirect(redirect)
                    
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
    def history(self):
        # Redirect HTTP to HTTPS
        if cherrypy.request.scheme == "http":
            redirect_url = cherrypy.request.base
            redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
            redirect_url = redirect_url.replace("http:", "https:")
            raise cherrypy.HTTPRedirect(redirect_url)

        # if the session is not authorized send the user to the login page
        if not cherrypy.session.get("authorized", None):
            cherrypy.session["redirect"] = cherrypy.request.wsgi_environ['REQUEST_URI']
            raise cherrypy.HTTPRedirect("/")
        
        else:
            agent = cherrypy.request.headers['User-Agent']
            
            # if this doesn't match the original request force a new session
            if cherrypy.session["_ident"] == sha256(agent).hexdigest():
                tmpl = lookup.get_template("history.html.mako")
                return tmpl.render(
                                    username = cherrypy.session['username'],
                                    userimageurl = cherrypy.session['userimageurl'],
                                    usertype = cherrypy.session['usertype']
                                  )
            
            # Kill the current session
            else:
                cherrypy.session.clear()
                cherrypy.session.delete()
                cherrypy.lib.sessions.expire()
                raise cherrypy.HTTPRedirect("/")
              
    @cherrypy.expose
    def get_runs(self, _=None):
        # Redirect HTTP to HTTPS
        if cherrypy.request.scheme == "http":
            redirect_url = cherrypy.request.base
            redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
            redirect_url = redirect_url.replace("http:", "https:")
            raise cherrypy.HTTPRedirect(redirect_url)

        # if the session is not authorized send the user to the login page
        if not cherrypy.session.get("authorized", None):
            raise cherrypy.HTTPRedirect("/")
        
        else:
            agent = cherrypy.request.headers['User-Agent']
            
            # if this doesn't match the original request force a new session
            if cherrypy.session["_ident"] == sha256(agent).hexdigest():
                return API.get_runs()
            
            # Kill the current session
            else:
                cherrypy.session.clear()
                cherrypy.session.delete()
                cherrypy.lib.sessions.expire()
                raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def logout(self):
        # Redirect HTTP to HTTPS
        if cherrypy.request.scheme == "http":
            redirect_url = cherrypy.request.base
            redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
            redirect_url = redirect_url.replace("http:", "https:")
            raise cherrypy.HTTPRedirect(redirect_url)

        # Kill the current session
        cherrypy.session.clear()
        cherrypy.session.delete()
        cherrypy.lib.sessions.expire()
        raise cherrypy.HTTPRedirect("/")
    
    @cherrypy.expose
    def update_task_form(self, id=None, clone=False):
        # Redirect HTTP to HTTPS
        if cherrypy.request.scheme == "http":
            redirect_url = cherrypy.request.base
            redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
            redirect_url = redirect_url.replace("http:", "https:")
            raise cherrypy.HTTPRedirect(redirect_url)
          
        # if the session isn't authorized send the user to the login
        if not cherrypy.session.get("authorized", None):
            cherrypy.session["redirect"] = cherrypy.request.wsgi_environ['REQUEST_URI']
            raise cherrypy.HTTPRedirect("/")
        
        tmpl = lookup.get_template("update_task.html.mako")
        return tmpl.render(task = API.get_task_object(id), clone=clone)
      
    @cherrypy.expose
    def new_task_form(self, id=None):
        # Redirect HTTP to HTTPS
        if cherrypy.request.scheme == "http":
            redirect_url = cherrypy.request.base
            redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
            redirect_url = redirect_url.replace("http:", "https:")
            raise cherrypy.HTTPRedirect(redirect_url)
          
        # if the session isn't authorized send the user to the login
        if not cherrypy.session.get("authorized", None):
            cherrypy.session["redirect"] = cherrypy.request.wsgi_environ['REQUEST_URI']
            raise cherrypy.HTTPRedirect("/")
        
        tmpl = lookup.get_template("new_task.html.mako")
        return tmpl.render()
      
    @cherrypy.expose
    def add_task_form(self):
        # Redirect HTTP to HTTPS
        if cherrypy.request.scheme == "http":
            redirect_url = cherrypy.request.base
            redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
            redirect_url = redirect_url.replace("http:", "https:")
            raise cherrypy.HTTPRedirect(redirect_url)
          
        # if the session isn't authorized send the user to the login
        if not cherrypy.session.get("authorized", None):
            cherrypy.session["redirect"] = cherrypy.request.wsgi_environ['REQUEST_URI']
            raise cherrypy.HTTPRedirect("/")
        
        tmpl = lookup.get_template("new_task.html.mako")
        return tmpl.render()

    @cherrypy.expose
    def display_task(self, id=None):
        # Redirect HTTP to HTTPS
        if cherrypy.request.scheme == "http":
            redirect_url = cherrypy.request.base
            redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
            redirect_url = redirect_url.replace("http:", "https:")
            raise cherrypy.HTTPRedirect(redirect_url)
          
        # if the session isn't authorized send the user to the login
        if not cherrypy.session.get("authorized", None):
            cherrypy.session["redirect"] = cherrypy.request.wsgi_environ['REQUEST_URI']
            raise cherrypy.HTTPRedirect("/")
        
        tmpl = lookup.get_template("display_task.html.mako")
        return tmpl.render(task = API.get_task_object(id))

    @cherrypy.expose
    def display_run(self, id=None):
        # Redirect HTTP to HTTPS
        if cherrypy.request.scheme == "http":
            redirect_url = cherrypy.request.base
            redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
            redirect_url = redirect_url.replace("http:", "https:")
            raise cherrypy.HTTPRedirect(redirect_url)
          
        # if the session isn't authorized send the user to the login
        if not cherrypy.session.get("authorized", None):
            cherrypy.session["redirect"] = cherrypy.request.wsgi_environ['REQUEST_URI']
            raise cherrypy.HTTPRedirect("/")
        
        tmpl = lookup.get_template("display_run.html.mako")
        return tmpl.render(run = API.get_run_object(id))
    
    # TODO: Give dvl, env, prt better names
    @cherrypy.expose
    def add_task(self, id=None, name=None, state=None, dep=None, image=None, cmd=None,
                etp=None, cron=None, rsrt=None, rec=None, mxf=None, idl=None,
                daf=None, env=None, dvl=None, prt=None, desc=None):
      
        # Redirect HTTP to HTTPS
        if cherrypy.request.scheme == "http":
            redirect_url = cherrypy.request.base
            redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
            redirect_url = redirect_url.replace("http:", "https:")
            raise cherrypy.HTTPRedirect(redirect_url)
          
        # if the session isn't authorized send the user to the login
        if not cherrypy.session.get("authorized", None):
            cherrypy.session["redirect"] = cherrypy.request.wsgi_environ['REQUEST_URI']
            raise cherrypy.HTTPRedirect("/")
        
        if id:
            return API.update_task(id=id, name=name, state=state, dep=dep, image=image, cmd=cmd, etp=etp,
                                  cron=cron, rsrt=rsrt, rec=rec, mxf=mxf, idl=idl, daf=daf,
                                  env=env, dvl=dvl, prt=prt, desc=desc)
        else:
            return API.add_task(name=name, state=state, dep=dep, image=image, cmd=cmd, etp=etp,
                                cron=cron, rsrt=rsrt, rec=rec, mxf=mxf, idl=idl, daf=daf,
                                env=env, dvl=dvl, prt=prt, desc=desc)

    @cherrypy.expose
    def get_task(self, id=None):
        # Redirect HTTP to HTTPS
        if cherrypy.request.scheme == "http":
            redirect_url = cherrypy.request.base
            redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
            redirect_url = redirect_url.replace("http:", "https:")
            raise cherrypy.HTTPRedirect(redirect_url)
          
        # if the session isn't authorized send the user to the login
        if not cherrypy.session.get("authorized", None):
            cherrypy.session["redirect"] = cherrypy.request.wsgi_environ['REQUEST_URI']
            raise cherrypy.HTTPRedirect("/")
        
        return API.get_task(id)
      
    @cherrypy.expose
    def get_tasks(self):
        # Redirect HTTP to HTTPS
        if cherrypy.request.scheme == "http":
            redirect_url = cherrypy.request.base
            redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
            redirect_url = redirect_url.replace("http:", "https:")
            raise cherrypy.HTTPRedirect(redirect_url)
          
        # if the session isn't authorized send the user to the login
        if not cherrypy.session.get("authorized", None):
            # don't redirect to this page on login
            # cherrypy.session["redirect"] = cherrypy.request.wsgi_environ['REQUEST_URI']
            raise cherrypy.HTTPRedirect("/")
        
        return API.get_tasks()

    @cherrypy.expose
    def get_users(self, username=None, userid=None, usertype=None):
        # Redirect HTTP to HTTPS
        if cherrypy.request.scheme == "http":
            redirect_url = cherrypy.request.base
            redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
            redirect_url = redirect_url.replace("http:", "https:")
            raise cherrypy.HTTPRedirect(redirect_url)
          
        # if the session isn't authorized send the user to the login
        if not cherrypy.session.get("authorized", None):
            cherrypy.session["redirect"] = cherrypy.request.wsgi_environ['REQUEST_URI']
            raise cherrypy.HTTPRedirect("/")
          
        if cherrypy.session.get("usertype", "user") == "admin":
            users = API.get_users(username, userid, usertype)
            if users:
                return [user.json for user in users]
            else:
                return json.dumps({"error": "No user matches the request"})
        else:
            return json.dumps({"error": "User not authorized for this request"})

    @cherrypy.expose
    def disable_task(self, id):
        # Redirect HTTP to HTTPS
        if cherrypy.request.scheme == "http":
            redirect_url = cherrypy.request.base
            redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
            redirect_url = redirect_url.replace("http:", "https:")
            raise cherrypy.HTTPRedirect(redirect_url)
          
        # if the session isn't authorized send the user to the login
        if not cherrypy.session.get("authorized", None):
            cherrypy.session["redirect"] = cherrypy.request.wsgi_environ['REQUEST_URI']
            raise cherrypy.HTTPRedirect("/")
        
        return API.disable_task(id)
      
    @cherrypy.expose
    def stop_task(self, id):
        # Redirect HTTP to HTTPS
        if cherrypy.request.scheme == "http":
            redirect_url = cherrypy.request.base
            redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
            redirect_url = redirect_url.replace("http:", "https:")
            raise cherrypy.HTTPRedirect(redirect_url)
          
        # if the session isn't authorized send the user to the login
        if not cherrypy.session.get("authorized", None):
            cherrypy.session["redirect"] = cherrypy.request.wsgi_environ['REQUEST_URI']
            raise cherrypy.HTTPRedirect("/")
        
        return API.stop_task(id)
      
    @cherrypy.expose
    def queue_task(self, id):
        # Redirect HTTP to HTTPS
        if cherrypy.request.scheme == "http":
            redirect_url = cherrypy.request.base
            redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
            redirect_url = redirect_url.replace("http:", "https:")
            raise cherrypy.HTTPRedirect(redirect_url)
          
        # if the session isn't authorized send the user to the login
        if not cherrypy.session.get("authorized", None):
            cherrypy.session["redirect"] = cherrypy.request.wsgi_environ['REQUEST_URI']
            raise cherrypy.HTTPRedirect("/")
        
        return API.queue_task(id)
      
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
    global API
    API = API(pg)
    
    # Define the static path for template rendering
    # Enable this if Nginx proxy is not being used
    #conf = {
    #    '/static': {'tools.staticdir.on': True, 'tools.staticdir.dir': os.path.abspath(os.getcwd()) + '/UI/static'},
    #    '/favicon.ico': {'tools.staticfile.on': True, 'tools.staticfile.filename': os.path.abspath(os.getcwd()) + '/UI/static/favicon.ico'}
    #}
    
    # Set the global config.
    cherrypy.tools.secureheaders = cherrypy.Tool('before_finalize', secureheaders, priority=60)
    cherrypy.config.update({
                            #'environment': 'production',
                            'tools.sessions.on': True,
                            'engine.autoreload.on': False,
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