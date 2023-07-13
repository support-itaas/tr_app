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


class WizardCouponProduction(models.Model):
    _name = 'wizard.coupon.production'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Coupon Production'

    name = fields.Text(readonly=True, required=True, copy=False, default=lambda x: _('New'),string='หมายเลขการผลิต')
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
                    coupon_val = {
                        'coupon_id': line.product_id.id,
                        'package_id': package_line_id.package_id.id,
                        'quantity': line.product_quantity * package_line_id.quantity,
                        'expire_date': date.today() + timedelta(days=package_line_id.day_to_expire),
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
                        'branch_id': order.branch_id.id,
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
                                'order_branch_id': self.branch_id.id,
                                'production_id': self.id,
                                'type': 'paper',
                                'coupon_running': pack_id.name,
                            })
                            barcode = generate_ean(str(coupon_id.id))
                            coupon_id.update({'barcode': barcode})

        self.write({'state': 'done'})

    @api.multi
    def button_cancel(self):
        if self.coupon_line:
            self.coupon_line.unlink()
        self.write({'state':'cancel'})


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
    state = fields.Selection([('new','New'),('sold','Sold')],default='new')


