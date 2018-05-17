# -*- encoding: utf-8 -*-
__author__ = 'nobita'


class biterm_info:
    def __init__(self, w1, w2, z=-1):
        self.w_i = w1
        self.w_j = w2
        self.z = z # topic assignment


    def set_topic_assign(self, z):
        self.z = z


    def reset_topic_assign(self):
        self.z = -1