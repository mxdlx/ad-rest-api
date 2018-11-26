from flask import Flask, jsonify, redirect, request
from ldap.controls import SimplePagedResultsControl
import ldap
import os
import ast
import ConfigParser

app = Flask(__name__)

# Configuration variables
LDAPSERVER = ''
LDAPUSER = ''
LDAPPASS = ''
PAGESIZE = 1000
BASEDN = ''
USER_ATTR_LIST = []
USERS_ATTR_LIST = []
SEARCHFILTER = ""

# Configuration from INI file
def set_config_from_file():
  global LDAPSERVER, LDAPUSER, LDAPPASS, PAGESIZE, BASEDN, USER_ATTR_LIST, USERS_ATTR_LIST, SEARCHFILTER
  if len(USER_ATTR_LIST) > 0:
    USER_ATTR_LIST[:] = []
  if len(USERS_ATTR_LIST) > 0:
    USERS_ATTR_LIST[:] = []
  if os.path.isfile(os.getcwd() + '/' + 'service.conf'):
    config = ConfigParser.ConfigParser()
    config.read('service.conf')
    LDAPSERVER = unicode(config.get('connection', 'ldap_server'))
    LDAPUSER = unicode(config.get('connection', 'ldap_user'))
    LDAPPASS = unicode(config.get('connection', 'ldap_password'))
    PAGESIZE = config.getint('connection', 'ldap_page_size')
    BASEDN = unicode(config.get('connection', 'base_dn'))
    USER_ATTR_LIST.extend([ unicode(x) for x in ast.literal_eval(config.get('user', 'attributes')) ])
    USERS_ATTR_LIST.extend([ unicode(x) for x in ast.literal_eval(config.get('users', 'attributes')) ])
    SEARCHFILTER = config.get('users', 'ldap_search_filter')

# Environment variables override file
def set_config_from_env():
  global LDAPSERVER, LDAPUSER, LDAPPASS, PAGESIZE, BASEDN, USER_ATTR_LIST, USERS_ATTR_LIST, SEARCHFILTER
  if os.getenv('LDAP_SERVER'):
    LDAPSERVER = unicode(os.getenv('LDAP_SERVER'))
  if os.getenv('LDAP_USER'):
    LDAPUSER = unicode(os.getenv('LDAP_USER'))
  if os.getenv('LDAP_PASSWORD'):
    LDAPPASS = unicode(os.getenv('LDAP_PASSWORD'))
  if os.getenv('LDAP_PAGE_SIZE'):
    PAGESIZE = int(os.getenv('LDAP_PAGE_SIZE'))
  if os.getenv('LDAP_BASE_DN'):
    BASEDN = unicode(os.getenv('LDAP_BASE_DN'))
  if os.getenv('USER_ATTR_LIST'):
    if len(USER_ATTR_LIST) > 0:
      USER_ATTR_LIST[:] = []
      USER_ATTR_LIST.extend([ unicode(x) for x in ast.literal_eval(os.getenv('USER_ATTR_LIST')) ])
  if os.getenv('USERS_ATTR_LIST'):
    if len(USERS_ATTR_LIST):
      USERS_ATTR_LIST[:] = []
      USERS_ATTR_LIST.extend([ unicode(x) for x in ast.literal_eval(os.getenv('USERS_ATTR_LIST')) ])
  if os.getenv('LDAP_SEARCH_FILTER'):
    SEARCHFILTER = os.getenv('LDAP_SEARCH_FILTER')

def get_ldap_con():
  try:
    con = ldap.initialize(LDAPSERVER, bytes_mode=False)
    con.set_option(ldap.OPT_REFERRALS, 0)
    con.simple_bind_s(LDAPUSER, LDAPPASS)
  except:
    print("[ERROR] Could not connect to LDAP Server at " + LDAPSERVER)
  return con

def purge_results(sr):
  sr = [ y for (x,y) in sr if x != None ]
  return sr

def get_response_template():
  return {
    'page': 0,
    'quant': 0,
    'last': False,
    'data': None
  }

def search_user(username):
  con = get_ldap_con()
  msgid = con.search_ext(base=BASEDN, scope=ldap.SCOPE_SUBTREE, filterstr='(sAMAccountName=' + username + ')', attrlist=USER_ATTR_LIST)

  _, result_tuple = con.result(msgid=msgid)

  # Data mangle
  search_result = purge_results(result_tuple)
  ret_json = get_response_template()
  ret_json['page'] = 1
  ret_json['quant'] = len(search_result)
  ret_json['last'] = True
  ret_json['data'] = search_result

  return ret_json

def search_users(req_page):
  con = get_ldap_con()
  sc = SimplePagedResultsControl(criticality=True, size=PAGESIZE, cookie='')
  search_results = None
  last_page = False

  i = 0

  while True:
    if i >= req_page:
      break

    msgid = con.search_ext(base=BASEDN, scope=ldap.SCOPE_SUBTREE, filterstr=SEARCHFILTER.decode('utf8'), attrlist=USERS_ATTR_LIST, serverctrls=[sc])
    # msgid is an integer representing LDAP operation id

    _, search_results, _, result_sc = con.result3(msgid)

    # result_data: list of tuples in the form of (dn, attrs),
    # dn is a string, ie: 'dn=alvaro,dc=example,dc=com',
    # attrs is a string key based dictionary.
    # result_sc: servercontrols list.

    pctrls = [ c for c in result_sc if c.controlType == SimplePagedResultsControl.controlType ]
    if not pctrls:
      last_page = True
      i += 1
      break

    cookie = pctrls[0].cookie
    if not cookie:
      last_page = True
      i += 1
      break
    sc.cookie = cookie
    i += 1

  # Data mangle
  # We don't need Full DN or registers with empty DN
  search_results = purge_results(search_results)

  ret_json = get_response_template()
  ret_json['page'] = i
  ret_json['quant'] = len(search_results)
  ret_json['last'] = last_page
  ret_json['data'] = search_results

  return ret_json

@app.route("/users", methods=['GET'])
def getUsuarios():
  set_config_from_file()
  set_config_from_env()
  if not request.args.get('p'):
    return redirect("/users?p=1")
  else:
    return jsonify(search_users(int(request.args.get('p'))))

@app.route("/users/<username>", methods=['GET'])
def getUsuario(username):
  set_config_from_file()
  set_config_from_env()
  return jsonify(search_user(username))

if __name__ == '__main__':
  app.run(debug=False, host='0.0.0.0')
