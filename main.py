#!/usr/bin/env python3
# coding=utf-8

from entrypoint2 import entrypoint
import json
from infopipe import InfoPipe, Node


@entrypoint
def main(config='config.json'):
    with open(config) as c:
        pipe = InfoPipe(json.load(c))

    pipe.update()
    print(json.loads(pipe.get_output('re', limit=1)))
