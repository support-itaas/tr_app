# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

from odoo import api, fields, models, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    signal = fields.Char(string='Signal')

    signal_ids = fields.One2many('service.signal.line', 'service_id', string='Signal')


class ServiceSignalLine(models.Model):
    _name = 'service.signal.line'

    service_id = fields.Many2one('product.product')
    branch_id = fields.Many2one('project.project', string='Branch', domain="[('is_branch', '=', True)]")
    signal = fields.Char(string='Signal')
    duration = fields.Float(string='Duration')
