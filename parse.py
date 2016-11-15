# -*- coding: utf-8 -*-
import yaml
import logging


class TemplateParser(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TemplateParser, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)
        self._log = logging.getLogger(__name__)

    def interpret(self, tmpl_path):
        t = self.load(tmpl_path)
        if not self.validate_tmpl(t):
            self._log.error("Parameters defined in Template isn't compatible to OvN")
        return t

    def load(self, tmpl_path):
        f = open(tmpl_path, 'r')
        t = list()

        try:
            t.append(i for i in yaml.load_all(f.read(-1)))
        except yaml.YAMLError, exc:
            if hasattr(exc, 'problem_mark'):
                mark = exc.problem_mark
            self._log.error("Template Format isn't compatible to YAML.")
            self._log.error("Error position: (%s:%s)", mark.line + 1, mark.column + 1)
            exit(-1)

        f.close()
        return t

    def validate(self, ytmpl):
        for box in ytmpl:
            if "Box" in box.keys():
                self._validate_box(box.gets("Box"))
            else:
                self._log.warning("Box Part is essential for Provisioning")
                self._log.warning("The provisioning for box %s will be skipped", )
                ytmpl.remove(box.gets("Box"))
                continue

            if "Bridges" in box.keys():
                self._validate_box(box.gets("Bridges"))
                pass

        return True

    def _validate_box(self, ybox):
        pass

    def _validate_bridge(self, ybr):
        pass

    def _validate_flow(self, yfl):
        pass


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
