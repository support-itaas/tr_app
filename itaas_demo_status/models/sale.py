# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions(<http://www.technaureus.com/>).

from odoo import models, fields, api ,_
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    validate_uid = fields.Many2one('res.users', string="Authorized Person", copy=False)
    approver_id = fields.Many2one('res.users', 'Sale Order Approver', readonly=True, copy=False)



    state = fields.Selection([
        ('draft', 'Quotation'),
        ('request', 'Quotation Requested'),
        ('validate', 'Validated'),
        ('sent', 'Quotation Sent'),
        ('demo', 'Demo Order'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')

    @api.multi
    def action_request(self):
        if self.state == 'draft':
            self.state = 'request'

    def action_confirm(self):
        self.write({
            'approver_id': self.env.user.id,
        })
        return super(SaleOrder, self).action_confirm()


    @api.multi
    def action_validate(self):
        if self.state == 'request':
            self.state = 'validate'
        # self.write({
        #     'validate_uid': self.env.user.id,
        # })
        # return super(SaleOrder, self).action_validate()


    @api.multi
    def action_sent_demo(self):
        if self.state == 'sent' or self.state == 'validate':
            self.state = 'demo'




