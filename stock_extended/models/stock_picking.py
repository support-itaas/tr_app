# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar
import pytz
from odoo.tools import ustr, DEFAULT_SERVER_DATE_FORMAT


def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

def strToDatetime(strdate):
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    # print strdate
    return datetime.strptime(strdate, DATETIME_FORMAT)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_reverse = fields.Boolean(string='Is Reverse',copy=False)
    invoice_reference = fields.Many2one('account.invoice',string='Invoice Reference',copy=False)
    reverse_reference = fields.Char(string='Reverse Reference',related='invoice_reference.name',copy=False)
    operating_unit_id = fields.Many2one('operating.unit', 'Operating Unit',copy=False)

    #-------------------------------------------------------------------------------
    pr_id = fields.Many2one('purchase.request', 'PR Reference', copy=False)

    @api.multi
    def do_new_transfer(self):
        for picking in self:
            if picking.is_reverse and not picking.reverse_reference:
                raise UserError(_('Please define reverse reference'))

        return super(StockPicking,self).do_new_transfer()

    @api.multi
    def _getlot_name(self, so_id=False, product_id=False):
        #print 'get lot'
        result = []
        before_date = ''
        use_date = ''
        end_life_date = ''
        life_date = ''
        lot_name = ''
        # print ':: '+str(so_id)+' = '+str(product_id)
        obj_stock_move = self.env['stock.move'].search(
            [('origin', '=', so_id), ('quant_ids.product_id', '=', product_id.id)], limit=1)
        # print obj_stock_move

        if obj_stock_move.quant_ids:
            for lot in obj_stock_move.quant_ids:
                # print lot
                # print lot.product_id
                # print lot.product_id.name
                # print lot.lot_id.name
                #print lot.lot_id.start_lot_date
                if int(product_id.id) == int(lot.product_id.id):
                    lot_name = lot.lot_id.name
                    #   obj_stock_move.quant_ids.lot_id.name
                    if lot.lot_id.start_lot_date:
                        before_date = lot.lot_id.start_lot_date.split(' ')
                        if len(before_date) > 0:
                            use_date = before_date[0]
                        else:
                            use_date = '-'
                    elif not lot.lot_id.start_lot_date:
                        before_date = lot.lot_id.create_date.split(' ')
                        if len(before_date) > 0:
                            use_date = before_date[0]

                    if lot.lot_id.life_date:
                        end_life_date = lot.lot_id.life_date.split(' ')
                        if len(end_life_date) > 0:
                            life_date = end_life_date[0]
                        else:
                            life_date = '-'

                    else:
                        life_date = '0000-00-00'
                startdate = use_date.split('-')
                startdates = str(startdate[2]) + '-' + str(startdate[1]) + '-' + str(startdate[0])
                expdate = life_date.split('-')
                expdates = str(expdate[2]) + '-' + str(expdate[1]) + '-' + str(expdate[0])

        result = {'lot_name': lot_name,
                  'before_date': startdates,
                  'end_life_date': expdates,
                  }

        #print result
        return result


    @api.multi
    def action_done(self):
        res = super(StockPicking,self).action_done()
        if self.picking_type_id.real_sequence_id:
            if self.force_date:
                sequence_date = strToDatetime(self.force_date).date()
                # print ('sequence_date',sequence_date)
                new_sequence = self.picking_type_id.real_sequence_id.with_context(ir_sequence_date=str(sequence_date),
                                                                                  ir_sequence_date_range=str(sequence_date)).next_by_id()
            else:
                new_sequence = self.picking_type_id.real_sequence_id.next_by_id()

            self.write({'name':new_sequence})
            self.move_lines.write({'reference':new_sequence})
            self.move_line_ids.write({'reference': new_sequence})
            if self.move_lines:
                for move in self.move_lines.filtered(lambda x: x.account_move_ids):
                    move.account_move_ids[0].ref = new_sequence
                    move.account_move_ids[0].line_ids.write({'ref':new_sequence})

        return res


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.multi
    def _create_returns(self):
        # Prevent copy of the carrier and carrier price when generating return picking
        # (we have no integration of returns for now)
        new_picking, pick_type_id = super(StockReturnPicking, self)._create_returns()
        picking = self.env['stock.picking'].browse(new_picking)
        picking.write({'carrier_id': False,
                       'is_reverse': True,
                       'carrier_price': 0.0})
        return new_picking, pick_type_id


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    is_show_on_dashboard = fields.Boolean('Show On Dashboard', default=True)
    real_sequence_id = fields.Many2one('ir.sequence', string='Real Sequence')

