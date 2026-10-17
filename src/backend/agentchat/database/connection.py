from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from sqlalchemy import DefaultClause, MetaData, create_engine, event, text
from sqlalchemy.engine import URL, Engine, make_url
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool


@dataclass(frozen=True)
class DatabaseURLs:
    sync: URL
    async_: URL

    @property
    def dialect(self) -> str:
        return self.sync.get_backend_name()


def resolve_database_urls(config: dict, base_dir: Path | None = None) -> DatabaseURLs:
    """由一个 URL 派生同步、异步连接，同时兼容旧的 endpoint 配置。"""
    endpoint = config.get("url") or config.get("endpoint")
    if not endpoint:
        raise ValueError("Configure database.url or mysql.endpoint before importing the database")
    url = make_url(endpoint)
    dialect = url.get_backend_name()
    if dialect == "mysql":
        if not url.database:
            raise ValueError("The MySQL URL must include a database name")
        return DatabaseURLs(url.set(drivername="mysql+pymysql"), url.set(drivername="mysql+aiomysql"))
    if dialect != "sqlite":
        raise ValueError("Only sqlite and mysql database URLs are supported")
    if url.host or url.username or url.password or url.port:
        raise ValueError("SQLite URLs must specify a local file or :memory:, not server credentials")
    if not url.database or url.database == ":memory:":
        # 使用同一个共享内存库，保证同步与异步连接可以互相读取数据。
        url = url.set(
            database="file:agentchat_" + uuid4().hex,
            query={
                "mode": "memory",
                "cache": "shared",
                "uri": "true",
            },
        )
    elif str(url.query.get("uri", "false")).lower() != "true":
        path = Path(url.database).expanduser()
        if not path.is_absolute():
            # 文件移动后仍以 src/backend 为相对路径基准。
            path = (base_dir or Path(__file__).resolve().parents[2]) / path
        url = url.set(database=path.resolve().as_posix())
    return DatabaseURLs(url.set(drivername="sqlite+pysqlite"), url.set(drivername="sqlite+aiosqlite"))


def prepare_sqlite_file(url: URL) -> None:
    if url.get_backend_name() == "sqlite" and str(url.query.get("uri", "false")).lower() != "true":
        Path(url.database).parent.mkdir(parents=True, exist_ok=True)


def engine_options(url: URL) -> dict:
    if url.get_backend_name() == "mysql":
        return {
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "connect_args": {
                "charset": "utf8mb4",
                "use_unicode": True,
                "init_command": "SET SESSION time_zone = '+08:00'",
            },
        }
    options = {
        "pool_pre_ping": True,
        "connect_args": {
            "check_same_thread": False,
            "timeout": 30,
        },
    }
    if url.query.get("mode") == "memory":
        options["poolclass"] = StaticPool
    return options


def configure_sqlite_engine(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    @event.listens_for(engine, "connect")
    def sqlite_connection_settings(connection, _record):
        cursor = connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=30000")
            if engine.url.query.get("mode") != "memory":
                cursor.execute("PRAGMA journal_mode=WAL")
        finally:
            cursor.close()


def create_sync_database_engine(url: URL) -> Engine:
    prepare_sqlite_file(url)
    engine = create_engine(url, **engine_options(url))
    configure_sqlite_engine(engine)
    return engine


def create_database_engines(urls: DatabaseURLs):
    engine = create_sync_database_engine(urls.sync)
    async_engine = create_async_engine(urls.async_, **engine_options(urls.async_))
    configure_sqlite_engine(async_engine.sync_engine)
    return engine, async_engine


def configure_sqlite_timestamps(metadata: MetaData) -> None:
    """让 SQLite 的默认时间与原 MySQL 会话的东八区时间保持一致。"""
    for table in metadata.tables.values():
        for column in table.columns:
            if column.server_default is not None and str(column.server_default.arg).upper() == "CURRENT_TIMESTAMP":
                column.server_default = DefaultClause(text("(datetime('now', '+8 hours'))"))
            if column.onupdate is not None and str(column.onupdate.arg).upper() == "CURRENT_TIMESTAMP":
                column.onupdate.arg = text("datetime('now', '+8 hours')")


def ensure_database(url: URL) -> None:
    if url.get_backend_name() == "sqlite":
        prepare_sqlite_file(url)
        return
    # URL.set(database=None) 不会清除原库名，需重新构造不包含库名的服务器连接。
    server_url = URL.create(url.drivername, username=url.username, password=url.password,
                            host=url.host, port=url.port, query=dict(url.query))
    bootstrap = create_engine(server_url, isolation_level="AUTOCOMMIT", **engine_options(url))
    try:
        database = bootstrap.dialect.identifier_preparer.quote_identifier(url.database)
        with bootstrap.connect() as connection:
            connection.execute(text("CREATE DATABASE IF NOT EXISTS " + database +
                                    " DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    finally:
        bootstrap.dispose()
