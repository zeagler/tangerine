"""

"""

def verify_database(postgres_connection):
    check_tables(postgres_connection)
    
def check_tables(postgres_connection):
    """
    Check that Tangerine's tables exist, create them if they do not
    
    TODO: Check the column names and values, update tables as needed
    """
    cur = postgres_connection.cursor()
    
    # Check if task table exists, create it if it does not
    cur.execute("select exists(select * from information_schema.tables where table_name='tangerine')")
    if not cur.fetchone()[0]:
        create_task_table(postgres_connection)
    
    # Check if task table exists, create it if it does not
    cur.execute("select exists(select * from information_schema.tables where table_name='jobs')")
    if not cur.fetchone()[0]:
        create_job_table(postgres_connection)

    # Check if the authorized user table exists, create it if it does not
    cur.execute("select exists(select * from information_schema.tables where table_name='authorized_users')")
    if not cur.fetchone()[0]:
        create_user_table(postgres_connection)

    # Check if the shared task queue exists, create it if it does not
    cur.execute("select exists(select * from information_schema.tables where table_name='task_queue')")
    if not cur.fetchone()[0]:
        create_task_queue(postgres_connection)

    # Check if the shared ready queue exists, create it if it does not
    cur.execute("select exists(select * from information_schema.tables where table_name='ready_queue')")
    if not cur.fetchone()[0]:
        create_ready_queue(postgres_connection)

    # Check if the job queue exists, create it if it does not
    cur.execute("select exists(select * from information_schema.tables where table_name='job_queue')")
    if not cur.fetchone()[0]:
        create_job_queue(postgres_connection)

    # Check if the task history table exists, create it if it does not
    cur.execute("select exists(select * from information_schema.tables where table_name='task_history')")
    if not cur.fetchone()[0]:
        create_task_history_table(postgres_connection)

    # Check if the agent table exists, create it if it does not
    cur.execute("select exists(select * from information_schema.tables where table_name='agents')")
    if not cur.fetchone()[0]:
        create_agent_table(postgres_connection)

    # Check if the webhook table exists, create it if it does not
    cur.execute("select exists(select * from information_schema.tables where table_name='hooks')")
    if not cur.fetchone()[0]:
        create_hooks_table(postgres_connection)

    # Check if the settings table exists, create it if it does not
    cur.execute("select exists(select * from information_schema.tables where table_name='settings')")
    if not cur.fetchone()[0]:
        create_settings_table(postgres_connection)

    # Check if the instance configuration table exists, create it if it does not
    cur.execute("select exists(select * from information_schema.tables where table_name='instance_configurations')")
    if not cur.fetchone()[0]:
        create_host_table(postgres_connection)

    postgres_connection.commit()


#
# Create tables
# TODO: functions to modify table columns when needed
# TODO: Change the name to tasks
# TODO: Change the dependencies to use the task id
# TODO: Version all entries with tangerine version it was created in.
#
def create_task_table(postgres_connection):
    """Create the table to track tasks"""
    cur = postgres_connection.cursor()
    cur.execute("""
    CREATE TABLE tangerine (
        id                       serial        PRIMARY KEY,
        name                     varchar(100)  NOT NULL,
        description              varchar       NOT NULL DEFAULT '',
        tags                     varchar[]     NOT NULL DEFAULT '{}',
        state                    varchar(10)   NOT NULL DEFAULT 'queued',
        next_state               varchar(10),
        dependencies             varchar[]     NOT NULL DEFAULT '{}',
        parent_job               integer,
        removed_parent_defaults  varchar[]     NOT NULL DEFAULT '{}',
        command                  varchar       NOT NULL DEFAULT '',
        entrypoint               varchar       NOT NULL DEFAULT '',
        recoverable_exitcodes    integer[]     NOT NULL DEFAULT '{}',
        restartable              boolean       NOT NULL DEFAULT true,
        datavolumes              varchar[]     NOT NULL DEFAULT '{}',
        environment              varchar[][2]  NOT NULL DEFAULT '{}',
        imageuuid                varchar       NOT NULL DEFAULT '',
        cron                     varchar(100)  NOT NULL DEFAULT '',
        next_run_time            integer,
        last_run_time            integer,
        last_success_time        integer,
        last_fail_time           integer,
        creation_time            integer,
        last_modified_time       integer,
        failures                 integer       NOT NULL DEFAULT 0,
        max_failures             integer       NOT NULL DEFAULT 3,
        queued_by                varchar       NOT NULL DEFAULT '',
        created_by               varchar       NOT NULL DEFAULT '',
        warning                  boolean       NOT NULL DEFAULT false,
        warning_message          varchar       NOT NULL DEFAULT '',
        service_id               varchar(10)   NOT NULL DEFAULT '',
        run_id                   integer,
        count                    integer       NOT NULL DEFAULT 0,
        delay                    integer       NOT NULL DEFAULT 0,
        reschedule_delay         integer       NOT NULL DEFAULT 5,
        disabled_time            integer
    );""")
    postgres_connection.commit()

def create_job_table(postgres_connection):
    """
    Create the table to track jobs
    
    A job entry consists of the default configuration for tasks, and a list of tasks
      that the job is responsible for.
    """
    cur = postgres_connection.cursor()
    cur.execute("""
    CREATE TABLE jobs (
        id                       serial        PRIMARY KEY,
        name                     varchar(100)  NOT NULL UNIQUE,
        description              varchar       NOT NULL DEFAULT '',
        tags                     varchar[]     NOT NULL DEFAULT '{}',
        state                    varchar(10)   NOT NULL DEFAULT 'stopped',
        next_state               varchar(10),
        dependencies             varchar[]     NOT NULL DEFAULT '{}',
        parent_job               integer,
        command                  varchar       NOT NULL DEFAULT '',
        entrypoint               varchar       NOT NULL DEFAULT '',
        recoverable_exitcodes    integer[]     NOT NULL DEFAULT '{}',
        restartable              boolean       NOT NULL DEFAULT true,
        datavolumes              varchar[]     NOT NULL DEFAULT '{}',
        environment              varchar[][2]  NOT NULL DEFAULT '{}',
        imageuuid                varchar       NOT NULL,
        cron                     varchar(100)  NOT NULL DEFAULT '',
        next_run_time            integer,
        last_run_time            integer,
        last_success_time        integer,
        last_fail_time           integer,
        creation_time            integer,
        last_modified_time       integer,
        failures                 integer       NOT NULL DEFAULT 0,
        max_failures             integer       NOT NULL DEFAULT 3,
        queued_by                varchar       NOT NULL DEFAULT '',
        created_by               varchar       NOT NULL DEFAULT '',
        warning                  boolean       NOT NULL DEFAULT false,
        warning_message          varchar       NOT NULL DEFAULT '',
        service_id               varchar(10)   NOT NULL DEFAULT '',
        run_id                   integer,
        count                    integer       NOT NULL DEFAULT 0,
        delay                    integer       NOT NULL DEFAULT 0,
        reschedule_delay         integer       NOT NULL DEFAULT 5,
        disabled_time            integer
    );""")
    postgres_connection.commit()

def create_user_table(postgres_connection):
    """Create the table to store authorized users"""
    cur = postgres_connection.cursor()
    cur.execute("""
    CREATE TABLE authorized_users (
        userid    integer       PRIMARY KEY,
        username  varchar(100)  NOT NULL UNIQUE,
        usertype  varchar(10)   NOT NULL DEFAULT 'user'
    );""")
    postgres_connection.commit()

def create_task_queue(postgres_connection):
    """Create the table to be used as a queue for tangerine in HA"""
    cur = postgres_connection.cursor()
    cur.execute("""
    CREATE TABLE task_queue (
        id integer
    );""")
    postgres_connection.commit()

def create_job_queue(postgres_connection):
    """Create the table to be used as a queue for tangerine in HA"""
    cur = postgres_connection.cursor()
    cur.execute("""
    CREATE TABLE job_queue (
        id integer
    );""")
    postgres_connection.commit()

def create_ready_queue(postgres_connection):
    """Create the table to be used as a queue for tangerine in HA"""
    cur = postgres_connection.cursor()
    cur.execute("""
    CREATE TABLE ready_queue (
        id integer
    );""")
    postgres_connection.commit()
    
def create_task_history_table(postgres_connection):
    """Create the table to store task run history"""
    cur = postgres_connection.cursor()
    cur.execute("""
    CREATE TABLE task_history (
        run_id                   serial        PRIMARY KEY,
        task_id                  integer       NOT NULL,
        name                     varchar       NOT NULL,
        description              varchar       NOT NULL DEFAULT '',
        tags                     varchar[]     NOT NULL DEFAULT '{}',
        result_state             varchar(10),
        result_exitcode          integer,
        dependencies             varchar[]     NOT NULL,
        dependencies_str         varchar,
        command                  varchar       NOT NULL,
        entrypoint               varchar       NOT NULL,
        recoverable_exitcodes    integer[]     NOT NULL,
        restartable              boolean       NOT NULL,
        datavolumes              varchar[]     NOT NULL,
        environment              varchar[][2]  NOT NULL,
        imageuuid                varchar       NOT NULL,
        cron                     varchar(100)  NOT NULL,
        queued_by                varchar       NOT NULL DEFAULT 'N/A',
        agent_id                 integer       NOT NULL DEFAULT 0,
        run_start_time           integer,
        run_finish_time          integer,
        run_start_time_str       varchar,
        run_finish_time_str      varchar,
        elapsed_time             varchar,
        max_cpu                  varchar,
        max_memory               varchar,
        max_network_in           varchar,
        max_network_out          varchar,
        max_diskio_in            varchar,
        max_diskio_out           varchar,
        time_scale               varchar[]     NOT NULL DEFAULT '{}',
        cpu_history              varchar[]     NOT NULL DEFAULT '{}',
        memory_history           varchar[]     NOT NULL DEFAULT '{}',
        network_in_history       varchar[]     NOT NULL DEFAULT '{}',
        network_out_history      varchar[]     NOT NULL DEFAULT '{}',
        disk_in_history          varchar[]     NOT NULL DEFAULT '{}',
        disk_out_history         varchar[]     NOT NULL DEFAULT '{}',
        log                      varchar
    );""")
    postgres_connection.commit()

def create_settings_table(postgres_connection):
    """Create the table to store agent history"""
    #
    # TODO add docker registry options
    #
    # TODO any sensitive information needs to be secured:
    #   AES 256 bit encrytion with some secret key.
    #
    cur = postgres_connection.cursor()
    cur.execute("""
    CREATE TABLE settings (
        setting_name             varchar       NOT NULL UNIQUE,
        setting_value            varchar       NOT NULL
    );""")
    
    postgres_connection.commit()

def create_host_table(postgres_connection):
    """Create the table to store instance configurations"""
    cur = postgres_connection.cursor()
    cur.execute("""
    CREATE TABLE instance_configurations (
        id                       serial,
        name                     varchar       NOT NULL UNIQUE,
        AMI                      varchar       NOT NULL,
        keyname                  varchar       NOT NULL,
        security_groups          varchar[],
        instance_type            varchar       NOT NULL,
        block_ebs_size           integer       NOT NULL,
        block_ebs_type           varchar       NOT NULL,
        iam_profile_name         varchar,
        user_data                varchar,
        user_data_base64         varchar,
        subnet_id                varchar[]     NOT NULL,
        spot_instance            boolean       NOT NULL DEFAULT false,
        spot_price               varchar       NOT NULL,
        tags                     varchar[][2],
        default_configuration    boolean       NOT NULL DEFAULT false
    );""")
    postgres_connection.commit()
    
    
def create_agent_table(postgres_connection):
    """Create the table to store agent history"""
    cur = postgres_connection.cursor()
    cur.execute("""
    CREATE TABLE agents (
        agent_id                 serial        PRIMARY KEY,
        host_ip                  varchar       NOT NULL,
        agent_port               varchar,
        instance_id              varchar,
        instance_type            varchar,
        available_memory         varchar,
        agent_creation_time      integer,
        agent_termination_time   integer,
        run                      varchar       DEFAULT '',
        last_action              varchar       DEFAULT '',
        last_action_time         integer,
        state                    varchar       DEFAULT 'active',
        agent_key                varchar
    );""")
    postgres_connection.commit()
    
def create_notifications_table(postgres_connection):
    #TODO
    print("WIP")
      
def create_hooks_table(postgres_connection):
    """Create the table to store hooks"""
    cur = postgres_connection.cursor()
    cur.execute("""
    CREATE TABLE hooks (
        id                       serial        PRIMARY KEY,
        name                     varchar       NOT NULL,
        action                   varchar       NOT NULL,
        targets                  varchar[]     NOT NULL,
        state                    varchar       NOT NULL DEFAULT 'active',
        api_token                varchar       NOT NULL UNIQUE,
        created                  integer,
        last_used                integer
    );""")