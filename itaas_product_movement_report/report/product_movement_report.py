# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.IT)

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import pytz
from datetime import datetime, timedelta, date, time


class ProductMovementReport(models.AbstractModel):
    _name = "report.itaas_product_movement_report.product_movement_report_id"
    _description = "Product Movement Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        print('_get_report_values:')
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))

        str2d = fields.Date.from_string
        str2dt = fields.Datetime.from_string
        date_from = str2d(docs.date_from)
        date_to = str2d(docs.date_to)
        date_time_from = docs.convert_usertz_to_utc(datetime.combine(str2dt(docs.date_from), time.min))
        date_time_to = docs.convert_usertz_to_utc(datetime.combine(str2dt(docs.date_to), time.max))
        location_ids = docs._get_location()
        # product_ids = docs._get_stock_move_product(location_ids)
        product_ids = self.env['product.product'].browse(31125)
        print('product_ids ',product_ids)
        if docs.location_id:
            warehouse = False
        else:
            warehouse = docs.warehouse_id
        stock_move_results = docs._get_stock_move_results(date_from, date_to, warehouse, location_ids, product_ids)
        print('stock_move_results:',len(stock_move_results))
        print('docs:',docs)
        docargs = {
            'doc_ids': docids,
            'data': data['form'],
            'docs': docs,
            'date_from': str2dt(docs.date_from).strftime("%d/%m/%Y"),
            'date_to': str2dt(docs.date_to).strftime("%d/%m/%Y"),
            'date_time_to': date_time_to,
            'date_time_from': date_time_from,
            'product_ids': product_ids,
            'stock_move_results': stock_move_results,
        }
        return docargs
