from ponyexpress.database import db
from ponyexpress.models.package import Package
from ponyexpress.models.node import Node


def process_node_info(request_json):
    node = Node.query.filter_by(name=request_json['node']).first()

    if not node:
        # Add node
        node = Node(request_json['node'])
        db.session.add(node)

        #add the packages
        for package in request_json['packages']:
            if 'sha' in package.keys():
                # Package sha must be uniqe, so fetch the first object
                p = Package.query.filter_by(sha=package['sha']).first()
                if p:
                    node.packages.append(p)
                else:
                    new_package = Package(package['sha'], package['name'], package['version'])

                    # Set extended attributes as well
                    new_package.uri = package['uri']
                    new_package.architecture = package['architecture']
                    new_package.provider = package['provider']
                    new_package.summary = package['summary']

                    node.packages.append(new_package)

                    db.session.add(new_package)
                db.session.commit()
    else:
        #prepare sha dict
        pp = {}

        for p in request_json['packages']:
            if 'sha' in p.keys():
                sha = p['sha']
                pp[sha] = p

        # Verify package version
        for package in node.packages:
            if package.sha in pp.keys():
                # we already know the sha, so same package
                if package.version == pp.version:
                    pass
                else:
                    # same sha, but different version??
                    pass
            else:
                # New package version
                new_package = Package(pp['sha'], pp['name'], pp['version'])

                # Set extended attributes as well
                new_package.uri = pp['uri']
                new_package.architecture = pp['architecture']
                new_package.provider = pp['provider']
                new_package.summary = pp['summary']

                #replace the old package
                package = new_package
                db.session.add(new_package)
        db.session.commit()


