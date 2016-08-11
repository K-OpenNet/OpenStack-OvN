# -*- coding: utf-8 -*-
import yaml


class TemplateParser(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TemplateParser, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.tmpl = list()

    def load(self, tmpl_path):
        f = open(tmpl_path, 'r')

        try:
            self.tmpl = yaml.load_all(f.read(-1))
        except yaml.YAMLError, exc:
            if hasattr(exc, 'problem_mark'):
                mark = exc.problem_mark
            print "Template Format isn't compatible to YAML."
            print "Error position: (%s:%s)" % (mark.line + 1, mark.column + 1)
            exit(-1)

        """
        Template Validating Process

        Parser Creation Process
        """

        return self.tmpl

    def validate_tmpl(self, ytmpl):
        for t in ytmpl:
            for k in t.keys():
                if "Box" not in k:
                    exit(-1)

                if "Bridge" in k:
                    pass
        return True


class BridgeInfoParser:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(BridgeInfoParser, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        pass


class TunnelInfoParser:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TunnelInfoParser, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        pass


class FlowInfoParser:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FlowInfoParser, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        pass

if __name__ == "__main__":
    print "in Main"
