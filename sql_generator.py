from itertools import count
import logging
from logging.handlers import RotatingFileHandler
from functools import lru_cache

# from index_advisor_workload import hypopg_btree, hypopg_btree_table

try:
    from .utils import get_placeholders, has_dollar_placeholder, replace_comma_with_dollar, replace_function_comma
except ImportError:
    from utils import get_placeholders, has_dollar_placeholder, replace_comma_with_dollar, replace_function_comma

counter = count(start=0, step=1)


def get_existing_index_sql(schema, tables):
    tables_string = ','.join(["'%s'" % table for table in tables])
    # Query all table indexes information and primary key information.
    sql = "SELECT c.relname AS tablename, i.relname AS indexname, " \
          "pg_catalog.pg_get_indexdef(i.oid) AS indexdef, p.contype AS pkey from " \
          "pg_index x JOIN pg_class c ON c.oid = x.indrelid JOIN " \
          "pg_class i ON i.oid = x.indexrelid LEFT JOIN pg_namespace n " \
          "ON n.oid = c.relnamespace LEFT JOIN pg_constraint p ON (i.oid = p.conindid " \
          "AND p.contype = 'p') WHERE (c.relkind = ANY (ARRAY['r'::\"char\", " \
          "'m'::\"char\"])) AND (i.relkind = ANY (ARRAY['i'::\"char\", 'I'::\"char\"])) " \
          "AND n.nspname = '%s' AND c.relname in (%s) order by c.relname;" % \
          (schema, tables_string)
    return sql


@lru_cache(maxsize=None)
def get_prepare_sqls(statement):
    if has_dollar_placeholder(statement):
        statement = replace_function_comma(statement)
        statement = replace_comma_with_dollar(statement)
    prepare_id = 'prepare_' + str(next(counter))
    placeholder_size = len(get_placeholders(statement))
    prepare_args = '' if not placeholder_size else '(%s)' % (','.join(['NULL'] * placeholder_size))
    return [f'prepare {prepare_id} as {statement}', f'explain execute {prepare_id}{prepare_args}',
            f'deallocate prepare {prepare_id}']


def get_workload_cost_sqls(statements, indexes, is_multi_node):
    sqls = []
    if indexes:
        # Create hypo-indexes.
        sqls.append('LOAD \'hypopg\';\n')
        for index in indexes:
            sqls.append("SELECT pg_catalog.hypopg_create_index('CREATE INDEX ON %s(%s) %s');" %
                        (index.get_table(), index.get_columns(), index.get_index_type()))
    if is_multi_node:
        sqls.append('set enable_fast_query_shipping = off;')
        sqls.append('set enable_stream_operator = on; ')
    # sqls.append("set explain_perf_mode = 'normal'; ")
    for index, statement in enumerate(statements):
        sqls.extend(get_prepare_sqls(statement))
    return sqls


def get_index_setting_sqls(indexes, is_multi_node):
    sqls = get_hypo_index_head_sqls(is_multi_node)[:]
    if indexes:
        # Create hypo-indexes.
        for index in indexes:
            sqls.append("SELECT hypopg_create_index('CREATE INDEX ON %s(%s) %s');" %
                        (index.get_table(), index.get_columns(), index.get_index_type()))
    return sqls


def get_single_advisor_sql(ori_sql):
    advisor_sql = 'select pg_catalog.gs_index_advise(\''
    for elem in ori_sql:
        if elem == '\'':
            advisor_sql += '\''
        advisor_sql += elem
    advisor_sql += '\');'
    return advisor_sql


@lru_cache(maxsize=None)
def get_hypo_index_head_sqls(is_multi_node):
    # sqls = ['SET enable_hypo_index = on;']
    sqls = []
    if is_multi_node:
        sqls.append('SET enable_fast_query_shipping = off;')
        # sqls.append('SET enable_stream_operator = on;')
    # sqls.append("set explain_perf_mode = 'normal'; ")
    return sqls


def get_index_check_sqls(query, indexes, is_multi_node):
    hypopg_btree = dict()
    hypopg_btree_table = dict()
    sqls = get_hypo_index_head_sqls(is_multi_node)[:]
    if indexes:
        for index in indexes:
            table = index.get_table()
            columns = index.get_columns()
            index_type = index.get_index_type()
            sqls.append("SELECT hypopg_create_index('CREATE INDEX ON %s(%s) %s')" %
                        (table, columns, index_type))
            # print('hypopg_create_index :',columns)
            cols_str='_'.join([x.strip() for x in columns.split(',')])
            key_index=table.split('.')[-1]+'_'+cols_str
            value_index=columns
            value_table=table.split('.')[-1]
            if key_index not in hypopg_btree:
                hypopg_btree[key_index]=value_index
            if key_index not in hypopg_btree_table:
                hypopg_btree_table[key_index]=value_table
    # sqls.append('SELECT hypopg_display_index()')
    # sqls.append("SET explain_perf_mode = 'normal';")
    sqls.extend(get_prepare_sqls(query))
    sqls.append('SELECT hypopg_reset_index()')
    return sqls, hypopg_btree, hypopg_btree_table


def get_table_info_sql(table, schema):
    return f"select reltuples, relispartition from pg_class where relname ilike '{table}' and " \
           f"relnamespace = (select oid from pg_namespace where nspname = '{schema}');"


def get_column_info_sql(table, schema):
    return f"select n_distinct, attname from pg_stats where tablename ilike '{table}' " \
           f"and schemaname = '{schema}';"


def get_schema_size_sql(schema):
    return f"""
            SELECT SUM(pg_total_relation_size(quote_ident(table_name)))
            FROM information_schema.tables
            WHERE table_schema = '{schema}';
        """


def get_table_size_sql(table):
    return f"""SELECT pg_total_relation_size(quote_ident('{table}')) AS total_storage_size;"""
