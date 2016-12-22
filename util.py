import logging
import yaml
import subprocess
import shlex


class Utils:
    def __init__(self):
        self.logger = None
        self.initialize_logger()

    def initialize_logger(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        fm = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(fm)
        self.logger.addHandler(ch)

    def yaml_parser(self, __file):
        """ Parse the data from YAML template. """
        with open(__file, 'r') as stream:
            try:
                file_str = stream.read()
                yaml.load(file_str)
            except yaml.YAMLError, exc:
                if hasattr(exc, 'problem_mark'):
                    mark = exc.problem_mark
                    self.logger.error(("YAML Format Error: " + __file
                                       + " (Position: line %s, column %s)" %
                                       (mark.line + 1, mark.column + 1)))
                    return None
        self.logger.info("Parse YAML from the file " + __file)
        return yaml.load(file_str)

    def shell_command(self, __cmd):
        self.logger.debug("Shell command: " + __cmd.__str__())
        if isinstance(__cmd, basestring):
            subproc = subprocess.Popen(shlex.split(__cmd),
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       shell=True)
        elif isinstance(__cmd, dict):
            subproc = subprocess.Popen(__cmd, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, shell=True)
        (cmdout, cmderr) = subproc.communicate()
        return subproc.returncode, cmdout, cmderr