## Handle configured mirrors and post
from datetime import date
import re

from ponyexpress.database import db
from ponyexpress.api.lib.providers import *
from ponyexpress.models.mirror_history import MirrorHistory
from ponyexpress.models.package_history import PackageHistory


class Mirrors:
    provider = None

    pattern = None  # store the compiled regex pattern

    def __init__(self):
        pass

    def update_mirror(self, mirror):

        # TODO: replace with better class selection
        if mirror.provider == 'apt':
            m = AptMirror(mirror.uri)

            metadata = m.fetch_metadata()
        else:
            raise NotImplementedError()

        if metadata is not None:

            try:
                mvals = metadata.itervalues()
            except:
                mvals = metadata.values()

            for m in mvals:
                hist = MirrorHistory(mirror, m['sha256'], m['package'], m['version'], m['filename'], date.today())

                db.session.add(hist)
            db.session.commit()

            # # Process package information and compare with local storage
            # # TODO: how do we handle packages which are present on multiple mirrors?
            # # TODO: select only packages from the current mirror
            # local_packages = PackageHistory.query.all()
            #
            # if local_packages is not None:
            #     # Compare packages installed into our environment with those provided by the mirror
            #     # return a list of packages which contains all packages on the mirror which match a package name
            #     # already present in our env
            #
            #     # We delibarately ignore those packages which are present on the mirror but are, at the time of
            #     # checking, not yet installed into our environment. Once any new package is installed we will track the
            #     # version history on the mirror automatically on the next run
            #
            #     matched_metadata = {}
            #
            #     for p in local_packages:
            #         if p.pkgsha in metadata.keys():
            #             # Create metadata structure with packages present locally and on the mirror
            #             mp = metadata[p.pkgsha]
            #             matched_metadata[p.pkgsha] = mp
            #
            #             # Create the mirror history data
            #             hist = MirrorHistory(mirror.uri, mp['sha256'], mp['name'], mp['version'], mp['filename'],
            #                                  date.today(), mirror.provider)
            #
            #             db.session.add(hist)
            #             db.session.commit()
            #         else:
            #             # We don't know the sha key, check for the package name
            #             for m in metadata.itervalues():
            #                 if m['package'] == p.pkgname:
            #                     # We know the package
            #                     hist = MirrorHistory(mirror.uri, m['sha256'], m['name'], m['version'], m['filename'],
            #                                  date.today(), mirror.provider)
            #
            #                     db.session.add(hist)
            #                     db.session.commit()
            #
            #     return matched_metadata
            #else:
            #    # We have no packages in our package history. This most likely means that pony has not yet recieved
            #    # updates from any client. Thus we do not check any metadata provided by the mirror yet.
            #    # Once pony recieves package data from any client we will compare the data on the next run
            #    return None

    def get_installed_packages(self, metadata):
        """Filter mirror package metadata to include only packages available in the database"""
        pass

    def get_outdated_packages(self, node_filter, mirror):
        """Compare packages available on the mirror with those available on a set of nodes"""

        outdated_packages = []

        # get packages from selected nodes
        node_filter_expression = ('%%%s%%' % node_filter)

        packages_history = PackageHistory.query.filter(PackageHistory.nodename.like(node_filter_expression)).all()

        if packages_history is not None:

            try:
                for package in packages_history:
                    # get packages from selected set of mirrors, filter by label
                    mp = MirrorHistory.query.filter(MirrorHistory.pkgname == package.pkgname,
                                                    MirrorHistory.mirror_id == mirror.id). \
                        order_by(MirrorHistory.pkgversion).first()

                    if mp is not None:
                        # compare versions
                        res = self.ver_cmp(package.pkgversion, mp.pkgversion)

                        if res < 0:
                            # mirror is newer
                            pkg = {'pkg': package, 'version': package.pkgversion, 'upstream': mp.pkgversion}
                            outdated_packages.append(pkg)
                            # elif res == 0:
                            #     # versions match
                            #     pass
                            # elif res > 0:
                            #     # local is newer than mirror
                            #     pass
            except:
                # Catch exceptions and move on to the next object
                next()

            return outdated_packages
        else:
            #
            return []

    def _ver_tuple(self, z):
        """Parse debian/ubuntu style version strings and return a tuple containing only numbers"""

        if self.pattern is None:
            self.pattern = re.compile("([0-9]+)\.([0-9]+)\.?([0-9]*)[\-\+\~]?([0-9]|[\+\-\~a-z0-9]*)[a-z]*([0-9]+)")

        a = self.pattern.findall(z)

        if a is not None and len(a) > 0:
            return tuple([str(x) for x in a[0] if x.isdigit()])

        # TODO: fallback, simply return not-equal!!
        #tup = tuple([str(x) for x in z.split('.')])

        return None

    def ver_cmp(self, a, b):
        """Compare two version tuples"""

        # TODO: handle different length versions
        va = self._ver_tuple(a)
        vb = self._ver_tuple(b)

        if len(va) != len(vb):
            return -1

        return cmp(va, vb)
