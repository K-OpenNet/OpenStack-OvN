# -*- coding: utf-8 -*-
import logging


class BridgeManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(BridgeManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)
        self._log = logging.getLogger(__name__)
