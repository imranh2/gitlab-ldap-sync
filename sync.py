import yaml
import os
import requests
#import json
import ldap

# Load the config file
with open("config.yml", 'r') as ymlfile:
    cfg = yaml.safe_load(ymlfile)
    
#print(cfg)
#print(cfg["gitlab"])
#print(cfg["gitlab"]["url"])

if cfg["gitlab"]["token"] == None:
    if not os.environ.get("GITLAB_TOKEN"):
        print("No Gitlab token provided via config.yml or environment variable 'GITLAB_TOKEN'")
        exit(1)
    elif os.environ.get("GITLAB_TOKEN"):
        cfg["gitlab"]["token"] = os.environ.get("GITLAB_TOKEN")

ldap_connect = ldap.initialize(cfg["ldap"]["url"])

# reconsile gitlab admins
# get all gitlab admins
admin_users_response = requests.get(cfg['gitlab']['url'] + '/api/v4/users?admins=true&access_token=' + cfg['gitlab']['token'])
#print(users_response.json())
gitlab_admin_users_json = admin_users_response.json()
#print(gitlab_admin_users_json)

# get all users that are supposed to be admins
ldap_git_admins_result = ldap_connect.search_s(cfg["ldap"]["baseDN"],ldap.SCOPE_SUBTREE,'cn=' + cfg['admingroup'],['memberUid'])
#print(ldap_git_admins_result)
#print(ldap_git_admins_result[0][1]['memberUid'])

# remove anybody that is not supposed to be an admin
for user in gitlab_admin_users_json:
    #print(user['username'])
    #print(user['id'])
    if user['username'] in ldap_git_admins_result[0][1]['memberUid']:
        print(user['username'] + " is in " + cfg["admingroup"])
    # looks like we need to remove this user as an admin
    else:
        print(user['username'] + " is not an admin / in " + cfg["admingroup"])
        # remove user from admin group
        delete_admin_response = requests.put(cfg['gitlab']['url'] + '/api/v4/users/' + str(user['id']) + '?access_token=' + cfg['gitlab']['token'], data={'admin': False})
        print(delete_admin_response.json())

# add anybody that is supposed to be an admin
for user in ldap_git_admins_result[0][1]['memberUid']:
    if user in [x['username'] for x in gitlab_admin_users_json]:
        print(user + "is already an admin")
    else:
        print(user + "is not a gitlab admin")
        # add user to admin group
        lookup_gitlab_user_id = requests.get(cfg['gitlab']['url'] + '/api/v4/users?username=' + user + '&access_token=' + cfg['gitlab']['token'])
        #print(lookup_gitlab_user_id.json())
        #print(lookup_gitlab_user_id.json()[0]['id'])
        add_admin_response = requests.put(cfg['gitlab']['url'] + '/api/v4/users/' + str(lookup_gitlab_user_id.json()[0]['id']) + '?access_token=' + cfg['gitlab']['token'], data={'admin': True})
        print(add_admin_response.json())

# reconsile gitlab groups

# get all gitlab users
users_response = requests.get(cfg['gitlab']['url'] + '/api/v4/users?access_token=' + cfg['gitlab']['token'])
#print(users_response.json())
gitlab_users_json = users_response.json()
#print(gitlab_users_json)

# get all gitlab groups
groups_response = requests.get(cfg['gitlab']['url'] + '/api/v4/groups?all_available=true&access_token=' + cfg['gitlab']['token'])
#print(groups_response.json())
gitlab_groups_json = groups_response.json()
#print(gitlab_groups_json)

for group in cfg['groups']:
    print(group)
    # get all users that are supposed to be in this group
    ldap_git_group_result = ldap_connect.search_s(cfg["ldap"]["baseDN"],ldap.SCOPE_SUBTREE,'cn=' + group['ldap'],['memberUid'])
    #print(ldap_git_group_result)
    #print(ldap_git_group_result[0][1]['memberUid'])
    # get list of people in this gitlab group
    gitlab_group_users_response = requests.get(cfg['gitlab']['url'] + '/api/v4/groups/' + group['gitlab'] + '/members?access_token=' + cfg['gitlab']['token'])
    #print(gitlab_group_users_response.json())
    gitlab_group_users_json = gitlab_group_users_response.json()
    #print(gitlab_group_users_json)

    # remove anybody that is not supposed to be in this group
    for user in gitlab_group_users_json:
        if user['username'] in ldap_git_group_result[0][1]['memberUid']:
            print(user['username'] + " is in " + group['ldap'])
        # looks like we need to remove this user as an admin
        else:
            print(user['username'] + " is not in " + group['ldap'])
            # get gitlab group id for this group
            lookup_gitlab_group_id = requests.get(cfg['gitlab']['url'] + '/api/v4/groups/' + group['gitlab'] + '?access_token=' + cfg['gitlab']['token'])
            #print(lookup_gitlab_group_id.json())
            #print(lookup_gitlab_group_id.json()['id'])
            # remove user from admin group
            delete_group_response = requests.delete(cfg['gitlab']['url'] + '/api/v4/groups/' + str(lookup_gitlab_group_id.json()['id']) + '/members/' + str(user['id']) + '?access_token=' + cfg['gitlab']['token'])
            print(delete_group_response.status_code)

    # add anybody that is supposed to be in this group
    for user in ldap_git_group_result[0][1]['memberUid']:
        if user in [x['username'] for x in gitlab_group_users_json]:
            print(user + " is already in " + group['gitlab'])
        else:
            print(user + " is not in " + group['gitlab'])
            # get gitlab group id for this group
            lookup_gitlab_group_id = requests.get(cfg['gitlab']['url'] + '/api/v4/groups/' + group['gitlab'] + '?access_token=' + cfg['gitlab']['token'])
            #print(lookup_gitlab_group_id.json())
            #print(lookup_gitlab_group_id.json()['id'])
            # get gitlab user id for this user
            lookup_gitlab_user_id = requests.get(cfg['gitlab']['url'] + '/api/v4/users?username=' + user + '&access_token=' + cfg['gitlab']['token'])
            #print(lookup_gitlab_user_id.json())
            #print(lookup_gitlab_user_id.json())
            if lookup_gitlab_user_id.json() != []:
                # add user to gitlab group
                add_group_response = requests.post(cfg['gitlab']['url'] + '/api/v4/groups/' + str(lookup_gitlab_group_id.json()['id']) + '/members?access_token=' + cfg['gitlab']['token'], data={'user_id': lookup_gitlab_user_id.json()[0]['id'], 'access_level': group['perms']})
                print(add_group_response.json())
            else:
                print("user " + user + " does not exist in gitlab")