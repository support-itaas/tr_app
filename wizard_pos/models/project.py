# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).
from odoo import models, fields, api


class Task(models.Model):
    _inherit = 'project.task'

    order_id = fields.Many2one('pos.order', 'POS Order', readonly=True)
