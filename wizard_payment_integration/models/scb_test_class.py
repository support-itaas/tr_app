# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

from odoo import api, fields, models, _


class SCBTestClass(models.Model):
    _name = 'scb.test.class'
    _description = 'For SCB data testing'

    post_data = fields.Char(string='Response Data', store=True)
    json_parse_data = fields.Char(string='Json Parse Data', store=True)
