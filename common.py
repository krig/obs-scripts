#!/usr/bin/python3
import json
import urllib.request
import urllib.error
from functools import lru_cache
import getpass
import os
import configparser

GITHUB_RELEASE_TAG = "https://api.github.com/repos/{srcrepo}/releases/tags/{tag}"


def query_json(url):
    """
    Return JSON from URL
    """
    with urllib.request.urlopen(url) as response:
        return json.load(response)


@lru_cache(maxsize=32)
def fetch_github_tag(repo, tag):
    """
    Fetch tag data from github
    """
    print("Fetching tag data for {}#{} from github...".format(repo, tag))
    return query_json(GITHUB_RELEASE_TAG.format(srcrepo=repo, tag=tag))


def oscrc_username(api):
    """
    Read OBS username from oscrc
    """
    locations = (os.path.expanduser("~/.config/osc/oscrc"),
                 os.path.expanduser("~/.oscrc"))
    for loc in locations:
        if os.path.isfile(loc):
            cfg = configparser.ConfigParser()
            cfg.read(loc)
            return cfg[api]["user"]
    return getpass.getuser()


def obs_branchbase(api):
    """
    Return format string for basename of
    OBS branches
    """
    return "home:%s:branches:{}" % (oscrc_username(api))
