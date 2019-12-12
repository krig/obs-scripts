#!/usr/bin/bash
chf="$(pwd)/entry.txt"

doit() {
    if [ -d wip/home:KGronlund:branches:$1 ]; then
        cd wip/home:KGronlund:branches:$1
        osc vc -F $chf
        osc commit -m "$(cat $chf | head -1)"
        cd ../../..
    fi
}

for project in ceph-image rook-ceph-image ceph-csi-image; do
    for repo in filesystems:ceph filesystems:ceph:octopus filesystems:ceph:nautilus Devel:Storage:6.0 Devel:Storage:7.0; do
        doit "$repo/$project"
    done
done

