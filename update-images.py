#!/usr/bin/env python3
import os
import tempfile
import re
import sys
import shutil
import json
import sh
import obsscripts

TEMPLATES_DIR = "templates"
MAP_FILE = "map.json"

OBS = "https://api.opensuse.org"
IBS = "https://api.suse.de"

OOSC = sh.osc.bake(A=OBS)
IOSC = sh.osc.bake(A=IBS)
BRANCHBASE = obsscripts.obs_branchbase(OBS)


def update_repo(name, repo, variant, registry, prefix):
    """
    1. generate the kiwi file
    2. pull down kiwi file from server
    3. if same, skip
    4. bco the project/package to a temp location
    5. oosc ar
    6. display diff
    7. prompt for changelog entry (reuse result for other repos for same image)
    8. oosc commit
    """
    if repo.startswith("obs://"):
        osc = OOSC
    else:
        osc = IOSC
    repo = repo[6:]
    print(name, repo, variant)
    curr = os.getcwd()
    wip_dir = os.path.join(curr, "wip")
    tmpl_dir = os.path.join(curr, TEMPLATES_DIR)

    new_kiwi = None
    try:
        rq = osc.api("-X", "GET", "/source/{0}/{1}/{1}.kiwi".format(repo, name))
        curr_kiwi = rq.stdout.decode('utf-8')
        rq = sh.xsltproc(os.path.join(tmpl_dir, name, "{}.xsl".format(name)),
                         os.path.join(tmpl_dir, name, "{}.xml".format(variant)))
        new_kiwi = rq.stdout.decode('utf-8')
        new_kiwi = new_kiwi.replace("{}/".format(registry), "{}{}".format(registry, prefix))
        new_kiwi = new_kiwi.replace("obsrepositories:/ceph/ceph", "obsrepositories:{}ceph/ceph".format(prefix))
        if curr_kiwi == new_kiwi:
            print("Skipping {}/{}: no difference".format(repo, name))
            return
    except sh.ErrorReturnCode as err:
        print(err)
        print("Skipping {}/{}...".format(repo, name))
        return

    try:
        try:
            os.mkdir(wip_dir)
        except os.error:
            pass
        os.chdir(wip_dir)
        osc.bco(repo, name)
        os.chdir(os.path.join(wip_dir, BRANCHBASE.format(repo), name))
        with open("{}.kiwi".format(name), "w") as f:
            f.write(new_kiwi)
        # copy updated template files as well
        for f in os.listdir(os.path.join(tmpl_dir, name)):
            shutil.copyfile(os.path.join(tmpl_dir, name, f),
                            os.path.join(wip_dir, BRANCHBASE.format(repo), name, f))
        osc.ar()
    finally:
        os.chdir(curr)

def main():
    """
    Update all the container images.
    """
    if os.path.exists("wip"):
        print("In-progress commits detected: wip/ exists. Please resolve manually.")
        sys.exit(1)

    cfg = json.load(open(os.path.join(TEMPLATES_DIR, MAP_FILE)))

    for image in cfg["images"]:
        for repo, data in cfg["repositories"].items():
            variant = data["variant"]
            registry = data["registry"]
            prefix = data["name_prefix"]
            update_repo(image, repo, variant, registry, prefix)

if __name__ == "__main__":
    main()
