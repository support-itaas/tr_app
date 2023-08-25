# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
import datetime
from datetime import date, timedelta

from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

import math
import re

from dateutil.relativedelta import relativedelta

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

def ean_checksum(eancode):
    """returns the checksum of an ean string of length 13, returns -1 if
    the string has the wrong length"""
    if len(eancode) != 13:
        return -1
    oddsum = 0
    evensum = 0
    eanvalue = eancode
    reversevalue = eanvalue[::-1]
    finalean = reversevalue[1:]

    for i in range(len(finalean)):
        if i % 2 == 0:
            oddsum += int(finalean[i])
        else:
            evensum += int(finalean[i])
    total = (oddsum * 3) + evensum

    check = int(10 - math.ceil(total % 10.0)) % 10
    return check


def check_ean(eancode):
    """returns True if eancode is a valid ean13 string, or null"""
    if not eancode:
        return True
    if len(eancode) != 13:
        return False
    try:
        int(eancode)
    except:
        return False
    return ean_checksum(eancode) == int(eancode[-1])


def generate_ean(ean):
    """Creates and returns a valid ean13 from an invalid one"""
    if not ean:
        return "0000000000000"
    ean = re.sub("[A-Za-z]", "0", ean)
    ean = re.sub("[^0-9]", "", ean)
    ean = ean[:13]
    if len(ean) < 13:
        ean = ean + '0' * (13 - len(ean))
    return ean[:-1] + str(ean_checksum(ean))


class WizardCoupon(models.Model):
    _inherit = 'wizard.coupon'

    type = fields.Selection([('e-coupon','E-Coupon'),('paper','Paper')],default='e-coupon')
    production_id = fields.Many2one('wizard.coupon.production', string='Production')

    count_type_paper = fields.Float(string='Coupon Paper', compute='_compute_check_type')
    count_type_e_coupon = fields.Float(string='E-coupon', compute='_compute_check_type')

    @api.one
    @api.depends('type')
    def _compute_check_type(self):
        for obj in self:
            if obj.type == 'e-coupon':
                obj.count_type_paper = 0.00
                obj.count_type_e_coupon = 1.00
            elif obj.type == 'paper':
                obj.count_type_paper = 1.00
                obj.count_type_e_coupon = 0.00
            else:
                obj.count_type_paper = 0.00
                obj.count_type_e_coupon = 0.00


class WizardCouponProduction(models.Model):
    _name = 'wizard.coupon.production'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Coupon Production'

    name = fields.Text(readonly=True, required=True, copy=False, default=lambda x: _('New'),string='หมายเลขการผลิต')
    operating_unit_id = fields.Many2one('operating.unit','Branch')
    branch_id = fields.Many2one('project.project', string="Order Branch")
    date_order = fields.Date(string="Order Date")
    state = fields.Selection([('draft', 'Draft'), ('validate', 'Validate'), ('cancel', 'Cancel'),('done', 'Done')], string='state',
                             default='draft')
    note = fields.Char(string='Note')
    partner_id = fields.Many2one('res.partner', string='Partner')

    #
    package_line = fields.One2many('wizard.coupon.package.line','production_id',string='Package Line')
    coupon_line = fields.One2many('wizard.coupon.line', 'production_id', string='Coupon Line')
    coupon_ids = fields.One2many('wizard.coupon','production_id', string='Coupon')
    #


    def get_project_id_from_ou(self):
        if self.operating_unit_id:
            project_id = self.env['project.project'].sudo().search([('operating_branch_id','=',self.operating_unit_id.id)],limit=1)
            if project_id:
                return project_id.id
            else:
                raise UserError(_('ตรวจสอบว่าใส่ชื่อสาขาถูกต้องหรือไม่'))
            # print (self.operating_unit_id)
            # print (project_id)
            # if project_id:
            #     print ('CHECK')
            #     self.sudo().write({'project_id': project_id.sudo()})
            #     print ('CHEK-2')

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('wizard.coupon.production') or _('New')
        res = super(WizardCouponProduction, self).create(vals)

        return res

    @api.multi
    def button_validate(self):
        if not self.package_line:
            raise UserError(_('ต้องมีรายการแพกเกจอย่างน้อย 1 รายการ'))
        for package_line_id in self.package_line:
            if package_line_id.package_id.is_pack:
                for line in package_line_id.package_id.product_pack_id:
                    start_date = strToDate(self.date_order) if self.date_order else date.today()
                    coupon_val = {
                        'coupon_id': line.product_id.id,
                        'package_id': package_line_id.package_id.id,
                        'quantity': line.product_quantity * package_line_id.quantity,
                        'expire_date': start_date + timedelta(days=package_line_id.day_to_expire),
                        'package_line_id':package_line_id.id,
                        'production_id': self.id,
                    }
                    self.env['wizard.coupon.line'].create(coupon_val)

        self.write({'state': 'validate'})

    @api.multi
    def button_generate(self):
        for order in self:
            #generate per pack
            count_package = 0
            for package_line_id in order.package_line:
                #genreate per quantity require per package
                for x in range(package_line_id.quantity):
                    #generate per coupon in the package
                    count_package += 1
                    val_pack_id = {
                        'name': str(order.name) + str(count_package),
                        'branch_id': order.get_project_id_from_ou(),
                        'production_id': order.id,
                        'package_id': package_line_id.package_id.id
                    }
                    pack_id = self.env['wizard.coupon.pack'].create(val_pack_id)
                    for product_pack_line in package_line_id.package_id.product_pack_id:
                        # generate per coupon quantity per coupon
                        for count in range(int(product_pack_line.product_quantity)):
                            coupon_id = self.env['wizard.coupon'].create({
                                'package_id': package_line_id.package_id.id,
                                'partner_id': self.partner_id.id,
                                'product_id': product_pack_line.product_id.id,
                                'order_branch_id': order.get_project_id_from_ou(),
                                'production_id': self.id,
                                'type': 'paper',
                                'coupon_running': pack_id.name,
                                # 'expiry_date': date.today() + timedelta(days=package_line_id.day_to_expire),
                            })
                            barcode = generate_ean(str(coupon_id.id))
                            coupon_id.update({'barcode': barcode})
                            start_date = strToDate(self.date_order) if self.date_order else date.today()
                            coupon_id.update({'expiry_date': start_date + timedelta(days=package_line_id.day_to_expire)})

        self.write({'state': 'done'})

    @api.multi
    def button_cancel(self):
        self.ensure_one()
        date_order = self.date_order
        date_order_month = strToDate(date_order) + relativedelta(days=5)
        # print ("DATE--")
        # print (date_order)
        # print (date_order_month)
        coupon_ids = self.env['wizard.coupon'].search([('redeem_date','>=',str(date_order)),('redeem_date','<=',str(date_order_month))])
        for coupon in coupon_ids:
            # print ('ALL COUPON')
            # print (coupon.name)
            move_ids = self.env['stock.move'].sudo().search([('name','=',coupon.name)],limit=5)
            for move_id in move_ids:
                if move_id and strToDate(move_id.date) != strToDate(coupon.redeem_date):
                    # print ('Update MOVE DATE')
                    # print (coupon.name)
                    # print (move_id.date)
                    # print (coupon.redeem_date)
                    move_id.sudo().update({'date':coupon.redeem_date})

            task_id = self.env['project.task'].sudo().search([('coupon_id','=',coupon.id),('date_deadline','!=',coupon.redeem_date)],limit=1)
            if task_id:
                task_id.sudo().update({'date_deadline': coupon.redeem_date})

        # for coupon_id in self.coupon_ids:
        #     coupon_line_id = self.coupon_line.filtered(lambda x: x.package_id == coupon_id.package_id and x.coupon_id == coupon_id.product_id)
        #     coupon_id.update({'expiry_date': coupon_line_id[0].expire_date})

        # if self.coupon_line:
        #     self.coupon_line.unlink()
        # self.write({'state':'cancel'})


class WizardCouponPackageLine(models.Model):
    _name = 'wizard.coupon.package.line'

    package_id = fields.Many2one('product.product', string="Package")
    day_to_expire = fields.Integer(string='Days to Expire')
    quantity = fields.Integer(string='Quantity')
    production_id = fields.Many2one('wizard.coupon.production', string='Production')


class WizardCouponLine(models.Model):
    _name = 'wizard.coupon.line'

    coupon_id = fields.Many2one('product.product', string="Coupon")
    package_id = fields.Many2one('product.product', string="Package")
    quantity = fields.Integer(string='Quantity')
    expire_date = fields.Date(string='Expire Date')
    package_line_id = fields.Many2one('wizard.coupon.package.line', string='Package Line')
    production_id = fields.Many2one('wizard.coupon.production',string='Production')


class WizardCouponPack(models.Model):
    _name = 'wizard.coupon.pack'

    name = fields.Char(string='Pack ID')
    package_id = fields.Many2one('product.product', string="Package")
    branch_id = fields.Many2one('project.project', string="Branch")
    production_id = fields.Many2one('wizard.coupon.production', string='Production')
    expiry_date = fields.Date(string='Expiry Date')
    state = fields.Selection([('new','New'),('sold','Sold'),('cancel','Cancel')],default='new')

    def update_expiry_date(self):
        package_ids = self.env['wizard.coupon.pack'].search([('expiry_date','=',False)],limit=1000)
        for package in package_ids:
            coupon_line_ids = package.production_id.mapped('coupon_line').filtered(lambda x: x.package_id == package.package_id)
            if coupon_line_ids:
                package.expiry_date = coupon_line_ids[0].expire_date



