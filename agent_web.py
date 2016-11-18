"""
This module serves as the web interface for Tangerine. The webpage
  is served at the default port 8080. Access control is provided
  through GitHub oauth.
"""
import cherrypy
from settings import settings

from mako.template import Template
from mako.lookup import TemplateLookup
lookup = TemplateLookup(directories=['static'])

class Agent_Server(object):
    """Render for the web application"""
    
    def __init__(self, agent_key):
        setattr(self, "agent_key", agent_key)

    @cherrypy.expose
    def index(self, agent_key=""):
        # Redirect HTTP to HTTPS
        if cherrypy.request.scheme == "http":
            redirect_url = cherrypy.request.base
            redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
            redirect_url = redirect_url.replace("http:", "https:")
            raise cherrypy.HTTPRedirect(redirect_url)

        if agent_key == self.agent_key:
            return ""
        else:
            return "Not authorized"

    @cherrypy.expose
    def ping(self, agent_key=""):
        # Redirect HTTP to HTTPS
        if cherrypy.request.scheme == "http":
            redirect_url = cherrypy.request.base
            redirect_url = redirect_url.replace(":" + str(cherrypy.request.local.port), "")
            redirect_url = redirect_url.replace("http:", "https:")
            raise cherrypy.HTTPRedirect(redirect_url)

        if agent_key == self.agent_key:
            return "pong"
        else:
            return "Not authorized"

def secureheaders():
    headers = cherrypy.response.headers
    headers['X-Frame-Options'] = 'DENY'
    headers['X-XSS-Protection'] = '1; mode=block'
    headers['Content-Security-Policy'] = "default-src='self'"
    headers['Strict-Transport-Security'] = 'max-age=31536000' # one year

def start_agent_web(agent_key):
    """
    Start the server
    
    Arguments:
        agent_key: 
    """
    
    # Set the global config.
    cherrypy.tools.secureheaders = cherrypy.Tool('before_finalize', secureheaders, priority=60)
    cherrypy.config.update({
                            'environment': 'production',
                            'tools.secureheaders.on': True,
                            'server.socket_host': '0.0.0.0',
                            'server.socket_port': 443,
                            'server.ssl_module': 'builtin',
                            'server.ssl_certificate': settings['web_ssl_cert_path'],
                            'server.ssl_private_key': settings['web_ssl_key_path'],
                            'server.ssl_certificate_chain': settings['web_ssl_chain_path'],
                           })
    
    cherrypy.tree.mount(Agent_Server(agent_key))

    # Make 2nd server to redirect HTTP to HTTPS
    http_server = cherrypy._cpserver.Server()
    http_server.socket_host = '0.0.0.0'
    http_server.socket_port=80
    http_server.subscribe()
    
    print("Staring Web Server")
    cherrypy.engine.start()
    cherrypy.engine.block()