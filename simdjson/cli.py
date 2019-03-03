import json

import click

from simdjson import ParsedJson


@click.group()
def cli():
    pass


@cli.command(name='query')
@click.argument('source', type=click.File('rb'))
@click.argument('query')
def query_command(source, query):
    pj = ParsedJson(source.read())
    click.echo(
        json.dumps(
            pj.items(query),
            indent=2,
            sort_keys=True
        )
    )
