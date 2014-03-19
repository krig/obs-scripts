obs-scripts
===========

Small tools/scripts I use to work with the openSUSE build service
(build.opensuse.org)

## `obs`

This script is intended to help with the process of building and
testing OBS packages based on a git or mercurial repository. It takes
care of creating a tarball from the repository head, updating the
tarball in the OBS project checkout and building the package locally.

The script as it is makes a lot of assumptions. I'll try to list as
many as I can:

* OBS project checkouts are kept in a directory tree, by default
  `~/build-service/obs/<repository>/<project>`.

* The source code for the projects are kept separately "somewhere
  else".

For each build target on the OBS, a target needs to be defined in the
`obs.conf` file used by the `obs` tool.

### Example usage:

To build packages for the project `crmsh` from `network:ha-clustering:Factory`:

1. Check out `crmsh` from OBS to `~/build-service/obs/network:ha-clustering:Factory/crmsh`:

        cd ~/build-service/obs
        osc co network:ha-clustering:Factory crmsh

2. Check out the `crmsh` source code from mercurial:

        cd ~/src
        hg clone http://hg.savannah.nongnu.org/hgweb/crmsh/

4. Add a target definition to `obs.conf`:

        [crmsh]
        branch=network:ha-clustering:Factory
        repo=openSUSE_Factory

3. Run the `obs` tool from the `crmsh` source directory:

        cd ~/src/crmsh
        obs run crmsh

