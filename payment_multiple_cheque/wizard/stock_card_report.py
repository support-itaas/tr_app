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


#this is for tax report section
class stock_card_report(models.TransientModel):
    _name = 'stock.card.report'
    
    date_from = fields.Date(string='Date From',required=True)
    date_to = fields.Date(string='Date To',required=True)
    location_id = fields.Many2one('stock.location', string='Location')
    category_id = fields.Many2one('product.category', string='Category')
    product_id = fields.Many2one('product.product', string='Product')
    company_id = fields.Many2one('res.company', string='Company')

    @api.model
    def default_get(self, fields):
        res = super(stock_card_report,self).default_get(fields)
        curr_date = datetime.now()
        from_date = datetime(curr_date.year,1,1).date() or False
        to_date = datetime(curr_date.year,curr_date.month,curr_date.day).date() or False
        # disable_excel_tax_report = self.env.user.company_id.disable_excel_tax_report
        company_id = self.env.user.company_id.id
        res.update({'date_from': str(from_date), 'date_to': str(to_date),'company_id':company_id})
        return res

    def print_report_pdf(self, data):
        data = {}
        data['form'] = self.read(['date_from', 'date_to', 'location_id', 'category_id', 'product_id','company_id'])[0]

        if not data['form']['product_id']:
            raise UserError(_('Stock Report with Cost need to select product one by one'))

        # return self.env['report'].get_action(self, 'stock_extended.product_stock_report_id', data=data)

        return self.env.ref('stock_extended.action_product_stock_report_id').report_action(self, data=data, config=False)

    def print_report_pdf_simple(self, data):
        data = {}
        data['form'] = \
            self.read(['date_from', 'date_to', 'location_id', 'category_id', 'product_id', 'company_id'])[0]

        # return self.env['report'].get_action(self, 'stock_extended.product_report_id', data=data)
        return self.env.ref('stock_extended.action_stock_report_simple').report_action(self, data=data,config=False)
        # def print_report_pdf(self, cr, uid, ids, context=None):
    #     print "print_report_pdf"
    #     if context is None:
    #         context = {}
    #
    #     data = self.read(cr, uid, ids, context=context)[0]
    #     datas = {
    #         'ids': context.get('active_ids', []),
    #         'model': 'product.product',
    #         'form': data
    #     }
    #
    #     datas['form']['ids'] = datas['ids']
    #     datas['form']['model'] = datas['model']
    #     # print "print_report_pdf-datas"
    #     # print datas
    #     return self.pool['report'].get_action(cr, uid, [], 'stock_extended.product_stock_report_id', data=datas,
    #                                           context=context)
