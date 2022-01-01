# Gitlab LDAP Sync
Want to sync a Gitlab Group with a LDAP group? Then this will do that.

## Limitations
* No proper error handling
* Not flexible in terms of configuration
* Only does `many->one` in terms of `Gitlab->LDAP` groups
* Only tested on Linux

### Notes
* Should work with both python 2 and 3

# Rough Usage Guide
1. Install deps
2. Edit `config.yml` to your needs
3. Create a Gitlab Token that has `api` and `sudo`
4. Make sure `gitlab.token` is set in `config.yml` *OR* set `GITLAB_TOKEN` envar (`config.yml` takes precedent)
5. Run `python sync.py`

## Via Gitlab CI
There's an included `.gitlab-ci.yml` file that should just work as long as you edit the `$GITLABCI_VARIABLE` to be whatever you set your CI variable to be called