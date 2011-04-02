'''deploy server.

Usage: deploy.py /deploy/directory

'''

from string import Template
import getopt
import os
import subprocess
import sys
try:
    import pwd
except ImportError:
    pwd = None

class ProcessException(Exception):
    def __init__(self, cmd, retcode):
        self.retcode = retcode
        self.cmd = ' '.join(cmd)
    def __str__(self):
        return "%s returned ERROR: %s" % (self.cmd, self.retcode)


def _popen(cmd, **kwargs):
    print ' '.join(cmd)
    return subprocess.Popen(cmd, **kwargs)

def _pcall(cmd, **kwargs):
    print ' '.join(cmd)
    retcode = subprocess.call(cmd, **kwargs)
    if retcode:
        raise ProcessException(cmd, retcode)
    return retcode

def _getenv(name):
    try:
        var = os.environ[name]
        return var
    except:
        raise Usage("Error: environment variable '%s' not set" % name)

def _template(source, dest, mapping=os.environ):
    """
    Takes source file and writes it to dest using mapping.
    """
    # read the template into a string
    source_file = open(source)
    contents = source_file.read()
    source_file.close()
    # substitute the variables
    template = Template(contents)
    result = template.substitute(mapping)
    # write the template to dest
    dest_file = open(dest, 'w')
    dest_file.write(result)
    dest_file.close()
    
def _update_pgpass(hostname, database, username, password):
    """
    Using the DB_* env vars, updates the pgpass file.
    """
    pgpass_line = "%s:*:%s:%s" % (hostname, database, username)
    pgpass_filename = os.path.expanduser('~postgres/.pgpass')
    try:
        # if exists the .pgpass file, move it then write it out without
        os.rename(pgpass_filename, '%s.tmp' % pgpass_filename)
        pgpass_old = open('%s.tmp' % pgpass_filename, 'r')
        pgpass = open(pgpass_filename, 'w')
        for line in pgpass_old:
            # skip if the first part of the line matches our line
            if line[:len(pgpass_line)] != pgpass_line:
                pgpass.write(line)
        pgpass.close()
    except:
        # file doesn't exist
        pgpass = open(pgpass_filename, 'w')
        pgpass.close()
    # append new line
    pgpass_line = '%s:%s\n' % (pgpass_line, password)
    print "Updating .pgpass - %s" % pgpass_line
    pgpass = open(pgpass_filename, 'a')
    pgpass.write(pgpass_line)
    pgpass.close()
    os.chmod(pgpass_filename, 0600)
    os.chown(pgpass_filename, pwd.getpwnam('postgres')[2], pwd.getpwnam('postgres')[3])


def do_virtualenv(deploy_dir):
    """
    Set up the virtual environment.
    """
    print "Installing virtualenv"
    # easy_install virtualenv
    _pcall(['easy_install', 'virtualenv',])
    env = 'pinax-env'
    print "Setting up virtual environment"
    env_bin_dir = os.path.join(deploy_dir, env, 'bin')
    # virtualenv pinax-env
    _pcall(['virtualenv', env])
    # activate it
    activate_this = os.path.join(env_bin_dir, 'activate_this.py')
    execfile(activate_this, dict(__file__=activate_this))
    # setup path
    os.environ['PATH'] = '%s:%s' % (env_bin_dir, _getenv('PATH'))
    # install requirements: pip install Pinax --no-deps --requirement pinaxdemosocial/requirements/project.txt
    _pcall(['pip', 'install', '--no-deps', '--requirement', 'pinaxdemosocial/requirements/project.txt'])
    
def do_django(deploy_dir):
    """
    This runs the various django commands to setup the media, database, etc
    """
    print "Running django commands"

    # syncdb: python manage.py syncdb --noinput
    _pcall(['python', 'pinaxdemosocial/manage.py', 'syncdb', '--noinput', ])

    # chown the deploy dir to be the apache user
    APACHE_USER = _getenv('APACHE_USER')
    _pcall(['chown', '-R', APACHE_USER, deploy_dir])


def do_database():
    """
    If DB_SETUP is True then it wipes the database.
    
    If BUILD_TYPE is 'staging' then it migrates the db using 
    env vars DB_COPY_*
    
    Env vars used:
     * DB_USER
     * DB_PASS
     * DB_NAME
    """
    DB_USER = _getenv('DB_USER')
    DB_PASS = _getenv('DB_PASS')
    DB_NAME = _getenv('DB_NAME')
    DB_HOST = _getenv('DB_HOST')
    DB_SETUP = eval(_getenv('DB_SETUP'))
    DB_COPY = eval(os.environ.get('DB_COPY','False'))

    # dev only resets db 
    if DB_SETUP:
        print "Setting up the database"
        # update the .pgpass file
        _update_pgpass(DB_HOST, DB_NAME, DB_USER, DB_PASS)
        # drop db: sudo -u postgres dropdb $DB_NAME
        try:
            _pcall(['sudo', '-u', 'postgres', 'dropdb', DB_NAME], stderr=open('/dev/null', 'w'))
        except:
            pass

        # drop db user: sudo -u postgres dropuser $DB_USER
        try:
            _pcall(['sudo', '-u', 'postgres', 'dropuser', DB_USER], stderr=open('/dev/null', 'w'))
        except:
            pass

        # create user: sudo -u postgres psql postgres
        p = _popen(['sudo', '-u', 'postgres', 'psql'], stdin=subprocess.PIPE)
        p.stdin.write("CREATE ROLE %s PASSWORD '%s' NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT LOGIN;\n" % (DB_USER, DB_PASS))
        p.stdin.close()
        p.wait()

        # create db: sudo -u postgres createdb -O $DB_USER $DB_NAME
        _pcall(['sudo', '-u', 'postgres', 'createdb', '-O', DB_USER, DB_NAME])

    if DB_COPY:
        print "Copying database"
        # get the migration db details
        DB_COPY_USER = _getenv('DB_COPY_USER')
        DB_COPY_PASS = _getenv('DB_COPY_PASS')
        DB_COPY_NAME = _getenv('DB_COPY_NAME')
        DB_COPY_HOST = _getenv('DB_COPY_HOST')
        # update the .pgpass file
        _update_pgpass(DB_COPY_HOST, DB_COPY_NAME, DB_COPY_USER, DB_COPY_PASS)
        # dump the database to a tempfile
        import tempfile
        (tmp_fd, tfilename) = tempfile.mkstemp()
        print "Dumping database '%s' to file '%s'" % (DB_COPY_NAME, tfilename)
        tfile = os.fdopen(tmp_fd, 'rw')
        # pg_dump database > tempfile
        p = _popen(['sudo', '-u', 'postgres',
                         'pg_dump', '-v',
                         '-h', DB_COPY_HOST,
                         '-U', DB_COPY_USER,
                         '-O',
                         DB_COPY_NAME],
                         stdin=subprocess.PIPE,
                         stdout=tfile)
        # prompts for password
        p.wait()
        tfile.seek(0)
        # load up dump into new db
        p = _popen(['sudo', '-u', 'postgres',
                              'psql',
                              '-d', DB_NAME,
                              '-h', DB_HOST,
                              '-U', DB_USER,
                              ],
                              stdin=subprocess.PIPE)
        p.stdin.write(tfile.read())
        p.stdin.close()
        p.wait()

def do_settingsfile(deploy_dir):
    """
    Writes the setting file from a template.
    """
    print "Writing out settings file"
    _template(
              os.path.join(deploy_dir, 'pinaxdemosocial', 'settings_template.py'),
              os.path.join(deploy_dir, 'pinaxdemosocial', 'settings_local.py'),
              )

def do_apache(deploy_dir):
    """
    Setups apache
    """
    print "Setting up Apache2"
    # enable required mods
    print "Enabling mod_rewrite"
    _pcall(['a2enmod', 'rewrite'])

    apache_conf = os.path.join('/etc/apache2/sites-available', _getenv('APACHE_CONF'))

    # rewrite config
    print "Writing out Apache2 conf: %s" % apache_conf
    _template(
              os.path.join(deploy_dir, 'deploy/http.conf.template'),
              apache_conf,
              )

    # enable if needed
    _pcall(['a2ensite', _getenv('APACHE_CONF')])

    print "Testing Apache2 config"
    retcode = _pcall(['apache2ctl', 'configtest'])
    if retcode:
        print "Error in Apache2 config"
        # disable site
        _pcall(['a2dissite', _getenv('APACHE_CONF')])
        raise Usage('Error in Apache2 config')

    print "Restarting Apache"
    _pcall(['apache2ctl', 'restart'])

def debug_env():
    import sys
    print "debug env"
    print "PATH=%s" % _getenv('PATH')
    print "sys path:"
    for path in sys.path:
        print path

def process(deploy_dir):
    """
    Deploys the server to the directory.
    """
    # setup the database
    do_database()
    # setup the settings file
    do_settingsfile(deploy_dir)
    # setup virtualenv
    do_virtualenv(deploy_dir)
    # django/pinax setup
    do_django(deploy_dir)
    # apache deployment
    do_apache(deploy_dir)



## main template

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    if argv is None:
        argv = sys.argv
    # parse command line options
    try:
        try:
            opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
        except getopt.error, msg:
            raise Usage(msg)
        type = None
        # process options
        for o, a in opts:
            if o in ("-h", "--help"):
                print __doc__
                return 0
        # process arguments
#        for arg in args:
#            process(arg) # process() is defined elsewhere
        # no args
        # deploy dir is one dir up
        deploy_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        os.environ['DEPLOY_DIR'] = deploy_dir
        process(deploy_dir)
    except Usage, err:
        print >> sys.stderr, err.msg
        print >> sys.stderr, "for help use --help"
        return 2

if __name__ == "__main__":
    sys.exit(main())



