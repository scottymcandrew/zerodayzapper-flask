#zerodayzapper.wsgi
import sys
sys.path.insert(0, '/var/www/html/zerodayzapper')

from zerodayzapper import app as application
