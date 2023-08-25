# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    branch_no = fields.Char(string='Branch',default='00000')
    area_id = fields.Many2one('customer.area', string='Area')
    customer_no_vat = fields.Boolean(string='Customer No TAX-ID',default=False,invisible=1)

    _sql_constraints = [
        ('uniq_ref_code', 'unique(ref)', "Unique Customer Code"),
    ]

    @api.model
    def create(self, vals):
        if vals.get('customer') and not vals.get('parent_id') and (
            not vals.get('vat') or len(vals['vat']) != 13) and self.env.user.company_id.tax_id_require:
            raise UserError(_("เลขประจำตัวผู้เสียภาษีอากรไม่ถูกต้อง จะต้องมีเลข 13 หลัก"))

        if vals.get('customer') and not vals.get('parent_id') and not vals.get(
                'vat') and self.env.user.company_id.tax_id_require:
            raise UserError(_("เลขประจำตัวผู้เสียภาษีอากรไม่ถูกต้อง จะต้องมีเลข 13 หลัก"))

        if vals.get('customer') and not vals.get('parent_id') and (
            not vals.get('branch_no') or len(vals['branch_no']) != 5) and self.env.user.company_id.branch_require:
            raise UserError(_("สาขาไม่ถูกต้อง จะต้องมีเลข 5 หลัก"))

        if not vals.get('ref') and vals.get('customer') and not vals.get(
                'parent_id') and self.env.user.company_id.auto_customer_code:
            vals['ref'] = self.env['ir.sequence'].next_by_code('customer.code')

        if not vals.get('ref') and vals.get('supplier') and not vals.get(
                'parent_id') and self.env.user.company_id.auto_supplier_code:
            vals['ref'] = self.env['ir.sequence'].next_by_code('supplier.code')

        return super(ResPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        if self.env.user.company_id.tax_id_require:
            if vals.get('vat'):
                if len(vals['vat']) != 13:
                    raise UserError(_("เลขประจำตัวผู้เสียภาษีอากรไม่ถูกต้อง จะต้องมีเลข 13 หลัก"))
            if vals.get('branch_no'):
                if len(vals['branch_no']) != 5:
                    raise UserError(_("สาขาไม่ถูกต้อง จะต้องมีเลข 5 หลัก"))

        return super(ResPartner, self).write(vals)

    #def get_full_address(self):
        #print "xx"

class customer_area(models.Model):
    _name = 'customer.area'

    name = fields.Char(string="Area Name")
    description = fields.Text(string="คำอธิบายพื้นที่")
