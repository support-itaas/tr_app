# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar
import pytz


class coupon_order(models.Model):
    _inherit = 'wizard.coupon'

    barcode = fields.Char(string='Barcode')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if operator not in ('ilike', 'like', '=', '=like', '=ilike'):
            return super(coupon_order, self).name_search((name, args, operator, limit))
        args = args or []
        print('args:',args)
        print('operator:',operator)

        domain = ['|', ('name', operator, name), ('barcode', operator, name)]
        print('domain:',domain)
        partners = self.env['wizard.coupon'].search(['|',
                                                   ('name', operator, name),
                                                   ('barcode', operator, name)], limit=limit)
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()



class coupon_order(models.Model):
    _name = 'coupon.order'
    _order = 'name desc'
    _inherit = ['mail.thread', 'barcodes.barcode_events_mixin']

    def get_branch_id(self):
        operating_unit_id = self.env['res.users'].operating_unit_default_get(self._uid)
        if operating_unit_id:
            branch_id = self.env['project.project'].search([('operating_branch_id','=',operating_unit_id.id)],limit=1)
            return branch_id
        else:
            return False

    name = fields.Text(readonly=True, required=True, copy=False, default=lambda x: _('New'))
    operating_unit_id = fields.Many2one('operating.unit', 'Operating Unit',
                                        default=lambda self:
                                        self.env['res.users'].
                                        operating_unit_default_get(self._uid),
                                        readonly=True)
    date_order = fields.Date(string="Order Date",required=True,default=datetime.today())
    partner_id = fields.Many2one('res.partner',string='Customer')
    coupon_ids = fields.One2many('coupon.order.line','coupon_order_id',string='Coupon')
    plate_number_id = fields.Many2one('car.details', string='Plate Number')
    branch_id = fields.Many2one('project.project', string="Redeemed Branch", default=get_branch_id)

    state = fields.Selection([('new','Draft'),('validate','Validate'),('cancel','Cancel')],string='State', default='new')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('coupon.order') or _('New')
        return super(coupon_order, self).create(vals)

    def on_barcode_scanned(self, barcode):
        self.ensure_one()
        coupon_id = self.env['wizard.coupon'].search([('barcode', '=', barcode)], limit=1)

        if coupon_id:
            self.coupon_ids.new({
                'coupon_order_id': self.id,
                'coupon_id': coupon_id.id,
            })
        else:
            raise UserError(_("ไม่เจอคูปอง"))


    @api.multi
    def validate(self):
        print('def validate')
        if self.coupon_ids:
            for coupon_line_id in self.coupon_ids:
                if not coupon_line_id.coupon_id.order_branch_id:
                    raise UserError(_("Please check purchase At"))
                else:
                    if coupon_line_id.state == 'redeem':
                        raise UserError(_("คูปองนี้ได้ใช้ไปแล้ว"))
                    else:
                        coupon_line_id.coupon_id.button_redeem(self.plate_number_id,self.branch_id,self.date_order,coupon_line_id.product_id.default_code,coupon_line_id.product_id.barcode)
        else:
            raise UserError(_("ไม่มีรายการคูปอง"))
        self.update({'state': 'validate'})


    @api.multi
    def cancel(self):
        self.update({'state': 'cancel'})

class coupon_order_line(models.Model):
    _name = 'coupon.order.line'
    _rec_name = 'coupon_id'

    coupon_id = fields.Many2one('wizard.coupon', string='Coupon')
    product_id = fields.Many2one('product.product', string='Product',related='coupon_id.product_id')
    package_id = fields.Many2one('product.product', string="Package",related='coupon_id.package_id')
    expiry_date = fields.Date(string="Expiry Date", readonly=True, related='coupon_id.expiry_date')
    state = fields.Selection(string='State',related='coupon_id.state')
    coupon_order_id = fields.Many2one('coupon.order', string='Coupon Order')
    barcode = fields.Char('Barcode',related="coupon_id.barcode")
    purchase_at = fields.Many2one('project.project',related="coupon_id.order_branch_id", string="Purchase At")

    _sql_constraints = [
        ('coupon_unique', 'unique (coupon_id,coupon_order_id)',
         'ไม่สามารถใช้คูปองซ้ำได้ !')]

    # @api.model
    # def create(self, vals):
    #     if vals.get('picking_id'):
    #         picking_id = vals.get('picking_id')
    #         picking_odj = self.env['stock.picking'].search([('id', '=', picking_id)], limit=1)
    #         vals.append({'operating_unit_id':picking_odj.operating_unit_id.id})
    #     res = super(StockMove, self).create(vals)
    #     return res


