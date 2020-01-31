#!/usr/bin/env python3
import os
import tempfile
import re
import sys
import shutil
import glob
import sh
import obsscripts


# update rook to a newer version

PACKAGE = "rook"
SRCREPO = "rook/rook"
LATEST_OCTOPUS = "v1.2.2"
LATEST_NAUTILUS = "v1.2.2"

OBS = "https://api.opensuse.org"
IBS = "https://api.suse.de"

OOSC = sh.osc.bake(A=OBS)
IOSC = sh.osc.bake(A=IBS)
BRANCHBASE = obsscripts.obs_branchbase(OBS)

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

PROJECTS_IBS = {
    "Devel:Storage:7.0": {
        "cmd": IOSC,
        "version-tag": LATEST_OCTOPUS
    }
}

#PROJECTS = PROJECTS_IBS
PROJECTS.update(PROJECTS_IBS)

def update_tarball(tgtversion):
    print("Editing update-tarball.sh...")
    txt = open("update-tarball.sh", "r").read()
    f, filename = tempfile.mkstemp('.sh', text=True)
    tf = os.fdopen(f, "w")
    txt = re.sub('ROOK_REV="[^"]+"', 'ROOK_REV="{}"'.format(tgtversion), txt, count=1)
    tf.write(txt)
    tf.close()
    shutil.copyfile(filename, "update-tarball.sh")
    os.remove(filename)


def update_changelog(osc, tgtversion):
    f, filename = tempfile.mkstemp('.txt', text=True)
    tf = os.fdopen(f, "w")
    fetch_changelog(osc, tgtversion, tf)
    tf.close()
    osc.vc("-F", filename)
    os.remove(filename)


def fetch_changelog(osc, tgtversion, tofile):
    """
    Pull changes, write them into tofile
    """
    changes = obsscripts.fetch_github_tag(SRCREPO, tgtversion)
    txt = changes["body"]
    print("Raw changes:\n{}\n".format(txt))
    txt = txt.replace("\r", "")
    txt = re.sub(r', @\w+', '', txt)
    tofile.write("- Update to {}:\n".format(tgtversion))
    for line in txt.splitlines():
        if line.startswith('- ') or line.startswith('* '):
            tofile.write("  * {}\n".format(line[2:]))


def main():
    nupdated = 0
    if os.path.exists("wip"):
        print("In-progress commits detected: wip/ exists. Please resolve manually.")
        sys.exit(1)

    for repo, proj in PROJECTS.items():
        osc = proj["cmd"]

        if "--fetch-changes" in sys.argv:
            f, filename = tempfile.mkstemp('.txt', text=True)
            tf = os.fdopen(f, "w")
            fetch_changelog(osc, proj["version-tag"], tf)
            tf.close()
            print(open(filename).read())
            os.remove(filename)
            sys.exit(0)

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
            try:
                os.mkdir(wip)
            except os.error:
                pass
            os.chdir(wip)
            osc("bco", repo, PACKAGE)
            os.chdir(os.path.join(wip, BRANCHBASE.format(repo), PACKAGE))
            update_changelog(osc, proj["version-tag"])
            update_tarball(proj["version-tag"])
            for toremove in glob.glob('./rook-*.xz'):
                print("Deleting {}...".format(toremove))
                os.remove(toremove)
            print(sh.sh("./update-tarball.sh"))
            print(osc.ar())
            print(osc.commit("-m", "Update to version {}:".format(proj["version-tag"])))
            nupdated = nupdated + 1

        finally:
            os.chdir(curr)

    if nupdated > 0:
        print("{} updated projects now in:\nwip".format(nupdated))


if __name__ == "__main__":
    main()
