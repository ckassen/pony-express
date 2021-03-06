from ponyexpress.database import db

node_packages = db.Table('node_packages',
                         db.Column('node_name', db.String, db.ForeignKey('nodes.name')),
                         db.Column('package_sha', db.String, db.ForeignKey('packages.sha')),
                         db.Index('idx', 'node_name', 'package_sha')
)


class Node(db.Model):
    __tablename__ = 'nodes'

    name = db.Column(db.String(255), primary_key=True)

    packages = db.relationship('Package', secondary=node_packages,
                               backref=db.backref('nodes', lazy='dynamic'), lazy='dynamic')

    def __init__(self, name=None):
        self.name = name

    def __repr__(self):
        return '<Node %r>' % self.name
