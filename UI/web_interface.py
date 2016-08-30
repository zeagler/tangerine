"""
This module serves as the web interface for Tangerine. The webpage
  is served at the default port 8080. Access control is provided
  through GitHub oauth.
"""
import os
import urllib2
import json
import cherrypy
from cherrypy.lib.static import serve_file
from hashlib import sha256
from settings import Web as options
from API import API
from time import time

from mako.template import Template
from mako.lookup import TemplateLookup
lookup = TemplateLookup(directories=['UI/static'])

class Statuspage(object):
    """Render for the web application"""

    @cherrypy.expose
    def index(self):
        """Main page for Tangerine's web UI"""
        tmpl = lookup.get_template("index.html.mako")
        if options[USE_AUTH]:
            return tmpl.render(
                                username = cherrypy.session['username'],
                                userimageurl = cherrypy.session['userimageurl'],
                                usertype = cherrypy.session['usertype']
                              )
        else:
            return tmpl.render(
                                username = cherrypy.session.get("username", "dev"),
                                userimageurl = cherrypy.session.get("userimageurl", "dev"),
                                usertype = cherrypy.session.get("usertype", "dev")
                              )

    @cherrypy.expose
    def login(self, code=None):
        # if the session is already authorized send the user to the main page
        if cherrypy.session.get("authorized", None):
            raise cherrypy.HTTPRedirect("/")

        # if the `code` parameter was POSTed, try to authenticate the user
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
                        
                        # Set the expiration time
                        cherrypy.session['expires'] = int(time()) + 1800 # 30 minutes from now

                        # Regenerate the session ID on successful login
                        cherrypy.session.regenerate()
                        
                        # Store user information in the session
                        cherrypy.session["authorized"] = "true"
                        cherrypy.session["userid"] = user_data.userid
                        cherrypy.session["username"] = user_data.username
                        cherrypy.session["usertype"] = user_data.usertype
                        cherrypy.session["userimageurl"] = data['avatar_url']
                        
                        # Send the authorized user to the main page or previous request
                        cherrypy.session["login_msg"] = None
                        redirect = cherrypy.session.get("redirect", "/")
                        raise cherrypy.HTTPRedirect(redirect)
                    
                    else:
                        cherrypy.session["login_msg"] = "Login failed."
                        return "Login failed. User '" + data['login'] + "' is not authorized"
                        
                # The user is not authorized
                else:
                    cherrypy.session["login_msg"] = "Login failed."
                    return "Login failed. User '" + data['login'] + "' is not authorized"

            # The code was not valid or not sent by GitHub
            else:
                cherrypy.session["login_msg"] = "Login failed."
                return "Login failed"

            cherrypy.session["login_msg"] = "Login failed."
            return "There was an error: " + str(response)
        
        # Regenerate the session ID before logging in
        cherrypy.session.regenerate()
        tmpl = lookup.get_template("login.html.mako")
        return tmpl.render(
                            client_id = options['GITHUB_OAUTH_ID'],
                            msg = cherrypy.session.get("login_msg", None)
                           )

    @cherrypy.expose
    def history(self):
        tmpl = lookup.get_template("history.html.mako")
        if options[USE_AUTH]:
            return tmpl.render(
                                username = cherrypy.session['username'],
                                userimageurl = cherrypy.session['userimageurl'],
                                usertype = cherrypy.session['usertype']
                              )
        else:
            return tmpl.render(
                                username = cherrypy.session.get("username", "dev"),
                                userimageurl = cherrypy.session.get("userimageurl", "dev"),
                                usertype = cherrypy.session.get("usertype", "dev")
                              )
              
    @cherrypy.expose
    def get_runs(self, _=None):
        return API.get_runs()
              
    @cherrypy.expose
    def get_log(self, log_name, lines=200, full_log=False):
        if not log_name:
            if full_log:
                return None
            else:
                return '{"error": "log_name must be present"}'
          
        if full_log:
            try:
                return serve_file("/logs/" + log_name, "application/x-download", "attachment")
            except Exception:
                return None
            
        return API.get_log(log_name=log_name, lines=lines)

    @cherrypy.expose
    def logout(self):
        # Kill the current session
        cherrypy.session.clear()
        cherrypy.session.delete()
        cherrypy.lib.sessions.expire()
        cherrypy.session["login_msg"] = "Logged out"
        raise cherrypy.HTTPRedirect("/login")
    
    @cherrypy.expose
    def update_task_form(self, id=None, clone=False):
        tmpl = lookup.get_template("update_task.html.mako")
        return tmpl.render(task = API.get_task_object(id), clone=clone)
      
    @cherrypy.expose
    def new_task_form(self, id=None):
        tmpl = lookup.get_template("new_task.html.mako")
        return tmpl.render()
      
    @cherrypy.expose
    def add_task_form(self):
        tmpl = lookup.get_template("new_task.html.mako")
        return tmpl.render()

    @cherrypy.expose
    def display_task(self, id=None):
        tmpl = lookup.get_template("display_task.html.mako")
        return tmpl.render(task = API.get_task_object(id))

    @cherrypy.expose
    def display_run(self, id=None):
        tmpl = lookup.get_template("display_run.html.mako")
        run = API.get_run_object(id)
        log = API.get_log(run.log)
        return tmpl.render(run = run, log = log)
    
    # TODO: Give dvl, env, prt better names
    @cherrypy.expose
    def add_task(self, id=None, name=None, state=None, dep=None, image=None, cmd=None,
                etp=None, cron=None, rsrt=None, rec=None, mxf=None, idl=None,
                daf=None, env=None, dvl=None, prt=None, desc=None):
        """ """
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
        return API.get_task(id)
      
    @cherrypy.expose
    def get_tasks(self):
        if cherrypy.session.get("login_msg", None) == "AJAX not authorized":
            return '{"redirect": "/login"}'
          
        return API.get_tasks()

    @cherrypy.expose
    def get_users(self, username=None, userid=None, usertype=None):
        # Check if the user is an admin
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
        return API.disable_task(id)
      
    @cherrypy.expose
    def stop_task(self, id):
        return API.stop_task(id)
      
    @cherrypy.expose
    def queue_task(self, id, username):
        return API.queue_task(id, username)
      
def secureheaders():
    headers = cherrypy.response.headers
    headers['X-Frame-Options'] = 'DENY'
    headers['X-XSS-Protection'] = '1; mode=block'
    headers['Content-Security-Policy'] = "default-src='self'"
    headers['Strict-Transport-Security'] = 'max-age=31536000' # one year

def redirect_to_ssl():
    """ """
    redirect_url = cherrypy.request.base
    redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
    redirect_url = redirect_url.replace("http:", "https:")
    raise cherrypy.HTTPRedirect(redirect_url)
          
def authenticate():
    """
    If the session isn't authorized this will send the user to the login page
    If the user agent for the session has changed this will invalidate the session
    """
    
    path = cherrypy.request.path_info
    
    # Don't redirect if the user is going to the login page
    if (path == "/login"):
        return

    # Check if the session is authorized
    if not cherrypy.session.get("authorized", None):
        # Recurring AJAX requests should send back a redirect signal
        if (path == "/get_tasks"):
            cherrypy.session["login_msg"] = "AJAX not authorized"
            return
      
        # Record the request to return the user to upon authentication
        if path in ["/history", "/add_task"]:
            cherrypy.session["redirect"] = cherrypy.request.wsgi_environ['REQUEST_URI']
        else:
            cherrypy.session["redirect"] = "/"
         
        # Redirect the user to the login page
        cherrypy.session["login_msg"] = "Session not authorized"
        raise cherrypy.HTTPRedirect("login")
   
    # if this doesn't match the original request force a new session
    useragent = cherrypy.request.headers['User-Agent']
    
    if not cherrypy.session["_ident"] == sha256(useragent).hexdigest():
        cherrypy.session.clear()
        cherrypy.session.delete()
        cherrypy.lib.sessions.expire()
        cherrypy.session["login_msg"] = "User Agent has changed"
        raise cherrypy.HTTPRedirect("login")
      
    # Check if the session has expired, if is not extend the session
    now = int(time())
    if cherrypy.session['expires'] >= now:
        # Don't extend the session for recurring AJAX requests
        if not path == "/get_tasks":
            cherrypy.session['expires'] = now + 1800 # 30 minutes from now
    else:
        # destroy the session if it is expired
        cherrypy.session.clear()
        cherrypy.session.delete()
        cherrypy.lib.sessions.expire()
        cherrypy.session["login_msg"] = "Session Expired"
        raise cherrypy.HTTPRedirect("login")
        
    
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
    
    if options['USE_AUTH']:
        use_auth = True
    else:
        use_auth = False
    
    # Set the global config.
    cherrypy.tools.authenticate = cherrypy.Tool('before_handler', authenticate)
    cherrypy.tools.secureheaders = cherrypy.Tool('before_finalize', secureheaders, priority=60)
    cherrypy.config.update({
                            #'environment': 'production',
                            'tools.authenticate.on': use_auth,
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