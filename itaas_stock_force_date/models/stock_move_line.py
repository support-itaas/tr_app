# -*- coding: utf-8 -*-
# Copyright (C) 2019-present Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, fields, models
from datetime import datetime, timedelta, date

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _action_done(self):
        params = self._context.get('params')
        # print (params)
        for line in self:
            try:
                if line.picking_id.force_date:
                    params.update({'force_date': line.picking_id.force_date})
                if 'force_date' in params and not params.get('force_date'):
                    print ('This is something, if force_date and exist , it is inventory adjust then nothing todo')
                    params.update({'force_date': datetime.today()})
                if not 'force_date' in params:
                    # print ('This is MO')
                    params.update({'force_date': datetime.today()})
            except:
                continue
        # print ('BEFORE')
        try:
            super(StockMoveLine, self)._action_done()
        except:
            print ('CONITNUE')
        # print ('AFTER')
        # print (self)
        for line in self:
            #########Fix for over receive, there are 2 move line generate but only 1 left so second one will be error but just continue
            try:
                # print ('----1')
                if line.picking_id.force_date:
                    # print('----2')
                    line.write({'date': line.picking_id.force_date})
                    params.update({'force_date': line.date})
                if params and 'force_date' in params:
                    # print('----3')
                    line.write({'date': params.get('force_date')})
            except:
                # print ('-----44')
                continue


