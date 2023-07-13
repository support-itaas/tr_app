# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CarSettings(models.Model):
    _name = 'car.settings'

    name = fields.Char(string='Name')
    point_equal_amount = fields.Integer(string='1 Point Equal Amount')
    wallet_ratio = fields.Float(string="Wallet Ratio")
    source_branch_ratio = fields.Float(string="Source Branch Ratio")
    destination_branch_ratio = fields.Float(string="Destination Branch Ratio")
    actual_revenue_id = fields.Many2one('account.account', string='Actual Revenue',
                                        domain=[('internal_type', '=', 'other')])
    wallet_expense_account_id = fields.Many2one('account.account', string='Wallet Expense Account',
                                                domain=[('internal_type', '=', 'other')],company_dependent=True)

    android = fields.Char(string='ANDROID')
    ios = fields.Char(string='IOS')

    server_token = fields.Char(string='Server Token')

    @api.model
    def create(self, vals):
        car_settings = self.env['car.settings'].search([])
        if len(car_settings) == 1:
            raise UserError(_('You cannot create another record'))
        return super(CarSettings, self).create(vals)

    @api.multi
    def unlink(self):
        for car in self:
            if car:
                raise UserError(_('You cannot delete this record'))
        return super(CarSettings, self).unlink()

    # def get_app_version(self, OPERATING_SYSTEM):
    #     print('self', )
    #     version = ''
    #     # about_app = self.env['about.app'].search([])
    #     # about_app = self.env['car.settings'].search([])
    #     # print('about_app', about_app)
    #     # for app in about_app:
    #     if OPERATING_SYSTEM == 'ANDROID':
    #         version = self.android
    #         print('version android', version)
    #     elif OPERATING_SYSTEM == 'IOS':
    #         version = self.ios
    #         print('version ios', version)
    #
    #     return [{
    #         'version': version
    #     }]
