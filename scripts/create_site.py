#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import os
import sys
import posixpath

import click


class Builder(object):

    def __init__(self, home):
        self.home = home
        self.config = {}
        self.verbose = False

    def set_config(self, key, value):
        self.config[key] = value
        if self.verbose:
            click.echo('  config[%s] = %s' % (key, value), file=sys.stderr)

    def __repr__(self):
        return '<Builder %r>' % self.home


builder_repo = click.make_pass_decorator(Builder)


@click.group()
@click.option('--repo-home', envvar='REPO_HOME', default='.repo',
              metavar='PATH', help='Changes the repository folder location.')
@click.option('--config', nargs=2, multiple=True,
              metavar='KEY VALUE', help='Overrides a config key/value pair.')
@click.option('--verbose', '-v', is_flag=True,
              help='Enables verbose mode.')
@click.version_option('1.0')
@click.pass_context
def bb(ctx, repo_home, config, verbose):
    """
    bb is a command line tool used to create and maintain local and remote
    erp server instances.

    the supported erp systes are

    - odoo\n
    - flectra\n
    - cubicerp

    """
    # Create a Builder object and remember it as as the context object.  From
    # this point onwards other commands can refer to it by using the
    # @builder_repo decorator.
    ctx.obj = Builder(os.path.abspath(repo_home))
    ctx.obj.verbose = verbose
    for key, value in config:
        ctx.obj.set_config(key, value)

@bb.command(short_help='Create or update a site')
@click.option('--force', is_flag=True,
              help='forcibly copy over an existing managed file')
@click.argument('src', nargs=-1, type=click.Path())
@click.argument('dst', type=click.Path())
@builder_repo
def create(repo, src, dst, force):
    """Copies one or multiple files to a new location.  This copies all
    files from SRC to DST.
    """
    for fn in src:
        click.echo('Copy from %s -> %s' % (fn, dst))

@bb.command()
@click.argument('src')
@click.argument('dest', required=False)
@click.option('--shallow/--deep', default=False,
              help='Makes a checkout shallow or deep.  Deep by default.')
@click.option('--rev', '-r', default='HEAD',
              help='Clone a specific revision instead of HEAD.')
@builder_repo
def docker(repo, src, dest, shallow, rev):
    """Creates and maintaines a site that runs in a docker container.

    This will clone the repository at SRC into the folder DEST.  If DEST
    is not provided this will automatically use the last path component
    of SRC and create that folder.
    """
    if dest is None:
        dest = posixpath.split(src)[-1] or '.'
    click.echo('Cloning repo %s to %s' % (src, os.path.abspath(dest)))
    repo.home = dest
    if shallow:
        click.echo('Making shallow checkout')
    click.echo('Checking out revision %s' % rev)


@bb.command()
@click.option('--show', '-s', is_flag=True, help='Lists actual settings')
@click.option('--reset', '-r', is_flag=True, help='Reset local settings')
@click.option(
    '--set', 
    default='all', 
    help="""
    Set local settings.
    By default all settings should be set.
    You can provide a comma separated list of names you wish to set.
    This can be name=value,name2=value2...
    """
)
@builder_repo
def support(repo, show, reset, set):
    """ Provides support commands to 
    maintain the evironment
    """
    from scripts import base_info_handler
    handler = base_info_handler.BaseinfoHandler(reset = reset)
    if show:
        handler.show_base_info()
    if set:
        handler.ask_all_values(set)

@bb.command()
@click.option('--username', prompt=True,
              help='The developer\'s shown username.')
@click.option('--email', prompt='E-Mail',
              help='The developer\'s email address')
@click.password_option(help='The login password.')
@builder_repo
def remote(repo, username, email, password):
    """Sets the user credentials.

    This will override the current user config.
    """
    repo.set_config('username', username)
    repo.set_config('email', email)
    repo.set_config('password', '*' * len(password))
    click.echo('Changed credentials.')


@bb.command()
@click.option('--message', '-m', multiple=True,
              help='The commit message.  If provided multiple times each '
              'argument gets converted into a new line.')
@click.argument('files', nargs=-1, type=click.Path())
@builder_repo
def mail(repo, files, message):
    """Commits outstanding changes.

    Commit changes to the given files into the repository.  You will need to
    "repo push" to push up your changes to other repositories.

    If a list of files is omitted, all changes reported by "repo status"
    will be committed.
    """
    if not message:
        marker = '# Files to be committed:'
        hint = ['', '', marker, '#']
        for file in files:
            hint.append('#   U %s' % file)
        message = click.edit('\n'.join(hint))
        if message is None:
            click.echo('Aborted!')
            return
        msg = message.split(marker)[0].rstrip()
        if not msg:
            click.echo('Aborted! Empty commit message')
            return
    else:
        msg = '\n'.join(message)
    click.echo('Files to be committed: %s' % (files,))
    click.echo('Commit message:\n' + msg)
