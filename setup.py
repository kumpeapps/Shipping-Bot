"""Install missing modules"""
import pip


def import_or_install(module, package = None):
    """install module if unable to import"""
    if package is None:
        package = module
    try:
        __import__(module)
    except ImportError:
        pip.main(['install', package])


import_or_install("bs4", "beautifulsoup4")
import_or_install("imap-tools")
import_or_install("mysql.connector")
import_or_install("pymysql")
import_or_install("requests")
import_or_install("infisical-api")