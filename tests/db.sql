CREATE ROLE odm WITH PASSWORD 'odmtest';
ALTER ROLE odm CREATEDB LOGIN;
CREATE DATABASE odmtests;
GRANT ALL PRIVILEGES ON DATABASE odmtests to odm;
