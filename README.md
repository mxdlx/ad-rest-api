# Minimal Active Directory REST API
_Work in progress ahead!_

This is a REST API for Active Directory with pagination enabled thanks to a great blog post by [Matt Fahrner](mailto:matt@mattfahrner.com) which you can find [here](http://mattfahrner.com/2014/03/09/using-paged-controls-with-python-and-ldap/).

### Available Endpoints
At this time there are only a couple:

* `/users`: TL;DR: You can search for all kinds of entries. I know this says users but in reality this endpoint depends on `LDAP_SEARCH_FILTER` and `USERS_ATTR_LIST` (See Environment Variables section). I started coding this to search for users but I also wanted this code to be a little configurable. 
* `/users/<username>`: JSON with user data where username is AD `sAMAccountName` field, retrieved attributes can be configured with `USER_ATTR_LIST`.

_Please note that `USER_ATTR_LIST` and `USERS_ATTR_LIST` are different variables._

### Environment Variables
The API can be configured by setting environment variables:

* `LDAP_SERVER`: LDAP server url in the form of `ldap://<host>:<port>`. I haven't tested against secure LDAP yet. No default value.
* `LDAP_USER`: AD user in the form of `<username>@<domain>`.Once again, username is AD `sAMAccountName` field. No default value.
* `LDAP_PASSWORD`: your AD user password.
* `LDAP_PAGE_SIZE`: AD pagination size, you should configure this depending on your AD settings. Default value is `1000`.
* `LDAP_BASE_DN`: your AD base DN. Example: `dc=example,dc=com`. No default value.
* `LDAP_SEARCH_FILTER`: LDAP filter for search operation.
* `USER_ATTR_LIST`: AD attributes to retrieve for `/user/<username>` endpoint.
* `USERS_ATTR_LIST`: AD attributes to retrieve for `/users` endpoint.

### Configuration File
This service can be configured by placing a `service.conf` file in the working directory (filename is mandatory at this time). This is a INI configuration file with three sections:

* `[connection]`: LDAP server, user, password, page size and base dn settings.
* `[user]`: settings for `/user/<username>` endpoint. Just a list of attributes at this time.
* `[users]`: settings for `/users` endpoint. Specifically a list of attributes and the LDAP filter to be used to search for all users.

**Example**
A `service.conf` file is included as an example:

```bash
# Service configuration, double quotes are needed just for list items
[connection]
# LDAP server hostname or IPv4 address
ldap_server: ldap.example.com
# LDAP user
ldap_user: user
# LDAP user password
ldap_password: secret
# LDAP page size for pagination of results
ldap_page_size: 1000
# Base DN to perform LDAP search
base_dn: cn=example,cn=com

[user]
# List of attributes to be displayed for every /user/<username>
attributes: ["cn", "description", "mail", "proxyAddresses", "userAccountControl"]

[users]
# List of attributes to be displayed for /users
attributes: ["cn", "mail"]
# Search filter to be used to search for all users
ldap_search_filter: (proxyAddresses=*)
```

### Variables Processing
All environment variables override configuration variables in `services.conf`. Also, configuration variables are checked with every request at this moment, this might not be a good idea but it's handy for development, so it's a fake hot-reload of configuration.

### Examples
If you decide to run this from your command line:

```bash
$ git clone https://github.com/mxdlx/ad-rest-api

# pip shouldn't be used with sudo but unless running inside virtualenv it's possible you'll need to install dependencies at a system-wide level
$ sudo pip install -r requirements.txt

# Attribute list MUST keep '["x", "y", "z"]' format
$ FLASK_APP=main.py LDAP_SERVER='ldap://192.168.1.10:389' \
                    LDAP_USER='user@example.com' \ 
                    LDAP_PASSWORD='secret' \
                    LDAP_PAGE_SIZE=1000 \
                    USER_ATTR_LIST='["cn", "mail"]' \
                    USERS_ATTR_LIST='["cn", "mail"]' \
                    LDAP_BASE_DN='dc=example,dc=com' \
                    LDAP_SEARCH_FILTER="(sAMAccountName=*)" flask run
# Try it
$ curl -I http://127.0.0.1:5000/users
```

If you want yo try this with Docker, there's an available automated build:

```bash
$ sudo docker run -d -p 5000:5000 -e LDAP_SERVER=ldap://192.168.1.10:389 \
                                  -e LDAP_USER=user@example.com \
                                  -e LDAP_PASSWORD=secret \
                                  -e LDAP_BASE_DN=dc=example,dc=com \
                                  -e USER_ATTR_LIST='["cn", "mail"]' \
                                  -e USERS_ATTR_LIST='["cn", "mail"]' \
                                  -e LDAP_SEARCH_FILTER="(proxyAddresses=*)" mdlee/ad-rest-api
# Try it
$ curl -I http://127.0.0.1:5000/users
```