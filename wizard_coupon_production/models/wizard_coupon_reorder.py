# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
from datetime import date

from odoo import fields, models, api, _


def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))


class WizardCouponReorder(models.Model):
    _name = 'wizard.coupon.reorder'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Coupon Reorder'

    name = fields.Char(readonly=True, required=True, copy=False, default=lambda x: _('New'),string='หมายเลขการผลิตซ้ำ')
    operating_unit_id = fields.Many2one('operating.unit','Branch')
    branch_id = fields.Many2one('project.project', string="Order Branch")
    state = fields.Selection([('draft', 'Draft'), ('validate', 'Validate'), ('cancel', 'Cancel')], string='state',
                             default='draft')
    note = fields.Char(string='Note')
    partner_id = fields.Many2one('res.partner', string='Partner')

    #
    package_line = fields.One2many('wizard.coupon.package.reorderline','production_id',string='Package Reorder')
    #


    # def get_project_id_from_ou(self):
    #     if self.operating_unit_id:
    #         project_id = self.env['project.project'].sudo().search([('operating_branch_id','=',self.operating_unit_id.id)],limit=1)
    #         if project_id:
    #             return project_id.id
    #         else:
    #             raise UserError(_('ตรวจสอบว่าใส่ชื่อสาขาถูกต้องหรือไม่'))


    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('wizard.coupon.reorder') or _('New')
        res = super(WizardCouponReorder, self).create(vals)

        return res

    @api.multi
    def button_validate(self):
        self.write({'state': 'validate'})

    @api.multi
    def button_cancel(self):
        self.write({'state':'cancel'})

    @api.multi
    def action_create_production_coupon_reorder(self):
        print('check_coupon')
        reorder_ids = self.env['wizard.coupon.reorder'].search([])
        for reorder in reorder_ids:
            print('reorder:',reorder)
            for line in reorder.package_line:

                check_coupon_state_new = self.env['wizard.coupon.pack'].search([('branch_id', '=', reorder.branch_id.id),
                                                                                ('state', '=', 'new'),
                                                                                ('package_id', '=', line.package_id.id),
                                                                                ], )

                print('line.min_quantity:',line.min_quantity)
                print('check_coupon_state_new', len(check_coupon_state_new))
                if len(check_coupon_state_new) < line.min_quantity:
                    count = line.max_quantity - len(check_coupon_state_new)
                    print('count:', count)

                    domain = [('production_id.branch_id', '=', reorder.branch_id.id),
                              ('production_id.state', '=', 'draft'),
                              ('production_id.operating_unit_id', '=', reorder.operating_unit_id.id),
                              ('production_id.partner_id', '=', reorder.partner_id.id),
                              ('package_id', '=', line.package_id.id),
                              ]
                    print('domain ',domain)
                    production_line_id = self.env['wizard.coupon.package.line'].search(domain ,limit=1)
                    print('production_line_id:',production_line_id)
                    # if production_line_id:
                    #     production_line_id.update({
                    #         'quantity': count
                    #     })
                    # else:
                    production_id = self.env['wizard.coupon.production'].search([('branch_id', '=', reorder.branch_id.id),
                                                                                 ('state', '=', 'draft')])
                    print('production_id:',production_id)
                    if not production_id:
                        val_production = {
                            'operating_unit_id' : reorder.operating_unit_id.id,
                            'date_order' : reorder.create_date,
                            'partner_id' : reorder.partner_id.id,
                            'branch_id' : reorder.branch_id.id,
                        }
                        production_id = self.env['wizard.coupon.production'].create(val_production)
                        print('production_id:', production_id)
                        # print('production_id.operating_unit_id:',production_id.operating_unit_id)
                        # print('production_id.date_order:',production_id.date_order)
                        # print('production_id.partner_id:',production_id.partner_id)
                        # print('production_id.branch_id:',production_id.branch_id)
                    val_coupon = {
                        'production_id': production_id.id,
                        'package_id': line.package_id.id,
                        'day_to_expire': line.day_to_expire,
                        'quantity': count,
                    }
                    production_package_id = self.env['wizard.coupon.package.line'].create(val_coupon)
                    print('production_package_id:',production_package_id)

    @api.multi
    def action_validate_production_coupon_reorder(self,  max_coupon=0):
        print('action_validate_production_coupon_reorder')

        if max_coupon:
            new_production_id = self.env['wizard.coupon.production'].search([('state', '=', 'draft')],limit=max_coupon)
        else:
            new_production_id = self.env['wizard.coupon.production'].search([('state', '=', 'draft')])

        for gen_production_id in new_production_id:
            if gen_production_id:
                gen_production_id.button_validate()
                gen_production_id.button_generate()



class WizardCouponPackageReorderLine(models.Model):
    _name = 'wizard.coupon.package.reorderline'

    package_id = fields.Many2one('product.product', string="Package")
    day_to_expire = fields.Integer(string='Days to Expire')
    min_quantity = fields.Integer(string='Min Quantity')
    max_quantity = fields.Integer(string='Max Quantity')
    production_id = fields.Many2one('wizard.coupon.reorder', string='Production')