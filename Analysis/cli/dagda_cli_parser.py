#

import argparse
import sys
from cli.command.history_cli_parser import HistoryCLIParser
from cli.command.start_cli_parser import StartCLIParser

class DagdaCLIParser:

    # -- Public methods

    # DagdaCLIParser Constructor
    def __init__(self):
        super(DagdaCLIParser, self).__init__()
        self.parser = DagdaGlobalParser(prog='dagda.py', usage=dagda_global_parser_text, add_help=False)
        self.parser.add_argument('command', choices=['history', 'start'])
        self.parser.add_argument('-h', '--help', action=_HelpAction)
        self.parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.9.0')
        # ArgumentParser.parse_known_args(args=None, namespace=None)
        self.args, self.unknown = self.parser.parse_known_args()
        if self.get_command() == 'history':
            self.extra_args = HistoryCLIParser()
        elif self.get_command() == 'start':
            self.extra_args = StartCLIParser()

    # -- Getters

    # Gets command
    def get_command(self):
        return self.args.command

    # Gets extra args
    def get_extra_args(self):
        return self.extra_args


# Overrides Help Action class

class _HelpAction(argparse._HelpAction):

    def __call__(self, parser, namespace, values, option_string=None):
        if sys.argv[1] != 'history' and sys.argv[1] != 'start' :
            parser.print_help()
            parser.exit()


# Custom Parser

class DagdaGlobalParser(argparse.ArgumentParser):

    # Overrides the error method
    def error(self, message):
        self.print_usage()
        exit(2)

    # Overrides the format help method
    def format_help(self):
        return dagda_global_parser_text


# -- Custom message

dagda_global_parser_text = '''usage: dagda.py [--version] [--help] <command> [args]

Dagda Commands:
  agent                 run a remote agent for performing the analysis of known 
                        vulnerabilities, trojans, viruses, malware & other 
                        malicious threats in docker images/containers
  check                 perform the analysis of known vulnerabilities, trojans, 
                        viruses, malware & other malicious threats in docker 
                        images/containers
  docker                list all docker images/containers and all docker daemon
                        events
  history               retrieve the analysis history for the docker images
  monitor               perform the monitoring of anomalous activities in
                        running docker containers
  start                 start the Dagda server
  vuln                  perform operations over your personal CVE, BID, RHBA, 
                        RHSA & ExploitDB database

Optional Arguments:
  -h, --help            show this help message and exit
  -v, --version         show the version message and exit
'''
