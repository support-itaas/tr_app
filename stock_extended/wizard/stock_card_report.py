# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import models, fields, api, _
from datetime import datetime
#from StringIO import StringIO
#import xlwt
#import base64
from odoo.exceptions import UserError
from odoo.tools import misc
from decimal import *


class stock_card_report(models.TransientModel):
    _name = 'stock.card.report'
    
    date_from = fields.Date(string='Date From',required=True)
    date_to = fields.Date(string='Date To',required=True)
    location_id = fields.Many2one('stock.location', string='Location')
    category_id = fields.Many2one('product.category', string='Category')
    product_id = fields.Many2one('product.product', string='Product')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    # Restrict Location
    restrict_locations = fields.Many2many('stock.location', string='Restrict Location')

    @api.model
    def default_get(self, fields):
        res = super(stock_card_report,self).default_get(fields)
        curr_date = datetime.now()
        from_date = datetime(curr_date.year,1,1).date() or False
        to_date = datetime(curr_date.year,curr_date.month,curr_date.day).date() or False
        # disable_excel_tax_report = self.env.user.company_id.disable_excel_tax_report
        company_id = self.env.user.company_id.id
        if self.env.user.restrict_locations:
            restrict_locations = self.env.user.stock_location_ids.filtered(lambda x: x.usage == 'internal').ids
        else:
            restrict_locations = self.env['stock.location'].search([('usage', '=', 'internal')]).ids
        res.update({'date_from': str(from_date),
                    'date_to': str(to_date),
                    'company_id':company_id,
                    'restrict_locations':restrict_locations})
        return res

    def print_report_pdf(self, data):
        data = {}
        data['form'] = self.read(['date_from', 'date_to', 'location_id', 'category_id', 'product_id','company_id'])[0]

        return self.env.ref('stock_extended.action_product_stock_report_id').report_action(self, data=data, config=False)

    def print_report_pdf_simple(self, data):
        data = {}
        data['form'] = self.read(['date_from', 'date_to', 'location_id', 'category_id', 'product_id', 'company_id'])[0]

        return self.env.ref('stock_extended.action_stock_report_simple').report_action(self, data=data,config=False)


class stock_inventory_export(models.TransientModel):
    _name = 'stock.inventory.export'

    report_file = fields.Binary('File')
    name = fields.Char(string='File Name', size=32)

    @api.multi
    def action_back_export(self):
        if self._context is None:
            self._context = {}
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.card.report',
            'target': 'new',
        }