# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
from odoo import fields, models


class TermsConditions(models.Model):
    _name = 'terms.conditions'
    _description = 'Terms And Conditions'

    name = fields.Char("Name", default='Terms And Conditions', readonly=True)
    terms_conditions = fields.Html('Terms And Conditions', sanitize_attributes=False)
