## Handle configured repositores and query for outdated package data
from datetime import date
from functools import cmp_to_key
import re
import os
import yaml

from ponyexpress.database import db
from ponyexpress.api.lib.providers import *

from ponyexpress.models import Package, RepoHistory, Repository, PackageHistory

import collections


class Repositories:
    provider = None

    pattern = None  # store the compiled regex pattern

    def __init__(self):
        pass

    @staticmethod
    def create_repository(repodata):
        # name, uri, label, provider   +   id

        # skip checking for the existance of a repo
        # could be done via URI only at this step
        new_repo = Repository()
        new_repo.name = repodata['name']
        new_repo.label = repodata['label']
        new_repo.uri = repodata['uri']
        new_repo.provider = repodata['provider']

        db.session.add(new_repo)
        db.session.commit()

        # return the new object's id
        return new_repo.id

    @staticmethod
    def update_repository_info(repository, repodata):
        # update all known fields
        if 'name' in repodata:
            repository.name = repodata['name']
        if 'uri' in repodata:
            repository.uri = repodata['uri']
        if 'label' in repodata:
            repository.label = repodata['label']
        if 'provider' in repodata:
            repository.provider = repodata['provider']

        # update the database
        db.session.commit()

    @staticmethod
    def delete_repository(repository):
        # remove the entry
        db.session.delete(repository)
        db.session.commit()

    def select_provider(self, repo):
        if repo.provider == 'apt':
            self.provider = AptRepository(repo.uri)
        else:
            raise NotImplementedError()

    def update_repository(self, repository):
        if self.provider is not None:
            metadata = self.provider.fetch_metadata()
        else:
            raise Exception()

        if metadata is not None:
            for m in metadata.values():
                hist = RepoHistory(repository, m['sha256'], m['package'], m['version'], m['filename'], date.today())

                db.session.add(hist)
            db.session.commit()

            return len(metadata.values())
        else:
            return None

    def get_outdated_packages(self, node_filter, repo_list):
        """Compare packages available on the repository server with those available on a set of nodes"""

        outdated_packages = collections.OrderedDict()

        if not isinstance(repo_list, list):
            return []

        # get packages from selected nodes
        if node_filter != '':
            node_filter_expression = ('%%%s%%' % node_filter)

            packages_history = PackageHistory.query.filter(PackageHistory.nodename.like(node_filter_expression)). \
                group_by(PackageHistory.pkgname).order_by(PackageHistory.pkgname).all()
        else:
            packages_history = PackageHistory.query.group_by(PackageHistory.pkgname).order_by(
                PackageHistory.pkgname).all()

        if repo_list is not []:
            rl = []
            for repo in repo_list:
                rl.append(repo.id)

        if packages_history is not None:
            for package in packages_history:
                if len(rl) > 0:
                    mp = RepoHistory.query.filter(RepoHistory.pkgname == package.pkgname) \
                        .filter(RepoHistory.repo_id.in_(rl)).group_by(RepoHistory.pkgname).all()

                    if mp is not None:
                        upstream_version = {}
                        for p in mp:
                            # compare versions
                            res = self.ver_cmp(package.pkgversion, p.pkgversion)

                            if res < 0:
                                # repository is newer
                                upstream_version[str(p.repository.id)] = p.pkgversion

                        l = len(upstream_version)
                        if l > 0:
                            # sort upstream_version by
                            if l > 1:
                                upstream_version['latest'] = \
                                    sorted(upstream_version.values(), key=cmp_to_key(self.ver_cmp), reverse=True)[0]
                            else:
                                upstream_version['latest'] = list(upstream_version.values())[0]

                            if package.pkgname not in outdated_packages:
                                package.upstream_version = upstream_version
                                outdated_packages[package.pkgname] = package
                else:
                    return []

            return list(outdated_packages.values())
        else:
            return []

    def get_repositories(self, expression):
        #check if expression is an integer or a comma separated list of values

        repo_list = []

        if expression is not None and (isinstance(expression, int) or expression.isdigit()):
            repo_id = int(expression)
            if repo_id > 0:
                repo = Repository.query.filter_by(id=repo_id).first()
                if repo is not None:
                    repo_list.append(repo)
        else:
            # assume expression is a list of repository numeric identifiers
            split = expression.split(',')

            if split is None:
                return []

            expression_list = [s for s in split if s.isdigit()]

            if expression_list is not None and isinstance(expression_list, list):
                repos = Repository.query.filter(Repository.id.in_(expression_list)).all()
                if repos is not None:
                    repo_list = repos

        return repo_list

    def get_repositories_by_label(self, label):
        #check if expression is an integer or a comma separated list of values

        if label is not None and label != '':
            repo_list = Repository.query.filter_by(label=label).all()

            if repo_list is not None:
                return repo_list

        return []

    def get_all_repositories(self):
        #check if expression is an integer or a comma separated list of values

        repo_list = Repository.query.all()

        if repo_list is not None:
            return repo_list

        return []

    def _ver_tuple(self, z):
        """Parse debian/ubuntu style version strings and return a tuple containing only numbers"""

        if self.pattern is None:
            self.pattern = re.compile('/(?<=\d)(?=\D)|(?<=\D)(?=\d)/')

        a = self.pattern.split(z)

        if a is not None and len(a) > 0:
            return tuple([str(x) for x in a[0] if x.isdigit()])

        return None

    def ver_cmp(self, a, b):
        """Compare two version tuples"""

        # TODO: handle different length versions
        va = self._ver_tuple(a)
        vb = self._ver_tuple(b)

        # When the second tuple is longer we assume it's a newer version
        #if len(va) != len(vb):
        #    return -1

        #return va < vb
        if va < vb:
            return -1
        elif va == vb:
            return 0
        elif va > vb:
            return 1

    @staticmethod
    def load_config(filename='', stream=None):
        repoyaml = []

        if str(filename) != '' and stream is None:
            path = os.path.abspath(filename)
            if not os.path.exists(path):
                return None

            stream = open(path, 'r')

        if stream is not None:
            yml = yaml.safe_load_all(stream)

            for repositories in yml:
                for repo in repositories['repositories']:
                    repoyaml.append(repo)

            return repoyaml
        else:
            return None
