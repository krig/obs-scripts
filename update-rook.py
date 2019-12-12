#!/usr/bin/env python3
import os
import tempfile
import re
import sys
import shutil
import configparser
import sh
from . import common


# update rook to a newer version

PACKAGE = "rook"
SRCREPO = "rook/rook"
LATEST_OCTOPUS = "v1.1.7"
LATEST_NAUTILUS = "v1.1.7"

OBS = "https://api.opensuse.org"
IBS = "https://api.suse.de"

OOSC = sh.osc.bake(A=OBS)
IOSC = sh.osc.bake(A=IBS)
BRANCHBASE = common.obs_branchbase(OBS)

PROJECTS = {
    "filesystems:ceph": {
        "cmd": OOSC,
        "version-tag": LATEST_OCTOPUS
    },
    "filesystems:ceph:octopus": {
        "cmd": OOSC,
        "version-tag": LATEST_OCTOPUS
    },
    "filesystems:ceph:nautilus": {
        "cmd": OOSC,
        "version-tag": LATEST_NAUTILUS
    },
    "filesystems:ceph:master:upstream": {
        "cmd": OOSC,
        "version-tag": LATEST_OCTOPUS
    }
}

def update_tarball(tgtversion):
    print("Editing update-tarball.sh...")
    txt = open("update-tarball.sh").read().decode('utf-8')
    f, filename = tempfile.mkstemp('.sh', text=True)
    tf = os.fdopen(f, "w")
    txt = re.sub('ROOK_REV="[^"]+"', 'ROOK_REV="{}"'.format(tgtversion), txt, count=1)
    tf.write(txt)
    tf.close()
    shutil.copyfile(filename, "update-tarball.sh")
    os.remove(filename)

def update_changelog(osc, tgtversion):
    changes = common.fetch_github_tag(SRCREPO, tgtversion)
    txt = changes["body"]
    txt = txt.replace("\r", "")
    txt = re.sub(r', @\w+', '', txt)
    f, filename = tempfile.mkstemp('.txt', text=True)
    tf = os.fdopen(f, "w")
    tf.write("- Update to {}:".format(tgtversion))
    for line in txt.splitlines():
        if line.startswith('- '):
            tf.write("  *{}".format(line[2:]))
    osc.vc("-F", filename)
    os.remove(filename)

def main():
    nupdated = 0
    if os.path.exists("wip"):
        print("In-progress commits detected: wip/ exists. Please resolve manually.")
        sys.exit(1)

    for repo, proj in PROJECTS.items():
        osc = proj["cmd"]

        try:
            tarball = osc.api("-X", "GET", "/source/{}/{}/update-tarball.sh".format(repo, PACKAGE))
            m = re.search('ROOK_REV="(.+)"', tarball.stdout.decode('utf-8'))
            if m and m.group(1) == proj["version-tag"]:
                continue
        except sh.ErrorReturnCode as err:
            print("Error code {}, skipping {}/{}...".format(err.exit_code, repo, PACKAGE))
            continue

        print("Updating {}/{} to version {}...".format(repo, PACKAGE, proj["version-tag"]))
        curr = os.getcwd()
        try:
            wip = os.path.join(curr, "wip")
            os.mkdir(wip)
            os.chdir(wip)
            osc("bco", repo, PACKAGE)
            os.chdir(os.path.join(wip, BRANCHBASE.format(repo), PACKAGE))
            update_changelog(osc, proj["version-tag"])
            update_tarball(proj["version-tag"])
            sh.rm("-rf", "rook-*.tar.xz")
            print(sh.sh("./update-tarball.sh"))
            print(osc.ar())
            print(osc.commit("-m", "Update to version {}:".format(proj["version-tag"])))
            nupdated = nupdated + 1

        except Exception as err:
            raise err
        finally:
            os.chdir(curr)

    if nupdated > 0:
        print("{} updated projects now in:\nwip".format(nupdated))

if __name__ == "__main__":
    main()
