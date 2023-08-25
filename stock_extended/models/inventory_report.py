# -*- coding: utf-8 -*-

from odoo import api, fields, models

class report_stock_history_report(models.AbstractModel):
    _name = 'report.stock_extended.report_stockhistory_id'

    @api.model
    def get_report_values(self, docids, data=None):

        company_id = self.env.user.company_id
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        return {
            'doc_ids': docids,
            'doc_model': 'account.invoice',
            'docs': docs,
            'company_id': company_id,
            'data': data,

        }
        # return self.env['report'].render('stock_extended.report_stockhistory_id', docargs)



class stock_record_yearly(models.Model):
    _name = 'stock.record.yearly'

    product_id = fields.Many2one('product.product',string='Product')
    qty = fields.Float(string='Quantity')
    unit_price = fields.Float(string='Unit Price')
    value = fields.Float(string='Value')
    lot = fields.Char('Lot')
    location = fields.Many2one('stock.location',string='Location')
    account_id = fields.Many2one('account.account',string='Account')
    date = fields.Date(string='Date')





    
