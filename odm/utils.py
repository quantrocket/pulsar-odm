import os
from inspect import isclass
from copy import copy

import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError, ProgrammingError


def get_columns(mixed):
    """
    Return a collection of all Column objects for given SQLAlchemy
    object.
    The type of the collection depends on the type of the object to return the
    columns from.
    ::
        get_columns(User)
        get_columns(User())
        get_columns(User.__table__)
        get_columns(User.__mapper__)
        get_columns(sa.orm.aliased(User))
        get_columns(sa.orm.alised(User.__table__))

    :param mixed:
        SA Table object, SA Mapper, SA declarative class, SA declarative class
        instance or an alias of any of these objects
    """
    if isinstance(mixed, sa.Table):
        return mixed.c
    if isinstance(mixed, sa.orm.util.AliasedClass):
        return sa.inspect(mixed).mapper.columns
    if isinstance(mixed, sa.sql.selectable.Alias):
        return mixed.c
    if isinstance(mixed, sa.orm.Mapper):
        return mixed.columns
    if not isclass(mixed):
        mixed = mixed.__class__
    return sa.inspect(mixed).columns


def database_operation(engine, oper, *args):
    operation = _database_operation(engine, oper)
    return operation(engine, *args)


def _database_operation(engine, oper):
    dialect = engine.dialect
    method_name = 'database_%s' % oper
    if hasattr(dialect, method_name):
        return getattr(dialect, method_name)
    else:
        scripts = engine_scripts[method_name]
        if hasattr(scripts, dialect.name):
            return getattr(scripts, dialect.name)
        else:
            return scripts.default


class CreateDatabase:

    def sqlite(self, engine, database):
        pass

    def default(self, engine, database):
        conn = engine.connect()
        # the connection will still be inside a transaction,
        # so we have to end the open transaction with a commit
        conn.execute("commit")
        conn.execute('create database %s' % database)
        conn.close()


class DropDatabase:

    def sqlite(self, engine, database):
        try:
            os.remove(database)
        except FileNotFoundError:
            pass

    def default(self, engine, database):
        conn = engine.connect()
        conn.execute("commit")
        conn.execute('drop database %s' % database)
        conn.close()


class AllDatabase:

    def sqlite(self, engine):
        database = engine.url.database
        if os.path.isfile(database):
            return [database]
        else:
            return []

    def default(self, engine):
        insp = inspect(engine)
        return insp.get_schema_names()


class ExistDatabase:

    def default(self, engine, database):
        """Check if a database exists.

        :param url: A SQLAlchemy engine URL.

        Performs backend-specific testing to quickly determine if a database
        exists on the server. ::

            database_exists('postgres://postgres@localhost/name')  #=> False
            create_database('postgres://postgres@localhost/name')
            database_exists('postgres://postgres@localhost/name')  #=> True

        Supports checking against a constructed URL as well. ::

            engine = create_engine('postgres://postgres@localhost/name')
            database_exists(engine.url)  #=> False
            create_database(engine.url)
            database_exists(engine.url)  #=> True

        """
        url = copy(engine.url)
        if url.drivername.startswith('postgresql'):
            url.database = 'template1'
        else:
            url.database = None

        engine = sa.create_engine(url)

        if engine.dialect.name == 'postgresql':
            text = "SELECT 1 FROM pg_database WHERE datname='%s'" % database
            return bool(engine.execute(text).scalar())

        elif engine.dialect.name == 'mysql':
            text = ("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA "
                    "WHERE SCHEMA_NAME = '%s'" % database)
            return bool(engine.execute(text).scalar())

        elif engine.dialect.name == 'sqlite':
            if database:
                return database == ':memory:' or os.path.exists(database)
            else:
                # The default SQLAlchemy database is in memory,
                # and :memory is not required, thus we should
                # support that use-case
                return True

        else:
            text = 'SELECT 1'
            try:
                url.database = database
                engine = sa.create_engine(url)
                engine.execute(text)
                return True

            except (ProgrammingError, OperationalError):
                return False


engine_scripts = {'database_exists': ExistDatabase(),
                  'database_create': CreateDatabase(),
                  'database_drop': DropDatabase(),
                  'database_all': AllDatabase()}
