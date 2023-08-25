# -*- coding: utf-8 -*-
from openerp import models, fields, api
    
class ProductCategory(models.Model):
    _inherit = "product.category"
    
    @api.multi
    @api.depends('is_apply')
    def _compute_is_apply(self):
#         commission_based_on = self.env['ir.values'].get_default('sale.config.settings', 'commission_based_on')
        commission_based_on = self.env['ir.config_parameter'].sudo().get_param('sales_commission_target_fix_percentage.commission_based_on') #odoo11
        for rec in self:
            if commission_based_on == 'product_category':
                rec.is_apply = True

    commission_type = fields.Selection(
        string="Commission Amount Type",
        selection=[
            ('percentage', 'By Percentage'),
            ('fix', 'Fixed Amount'),
        ],
    )
    is_apply = fields.Boolean(
        string='Is Apply ?',
        compute='_compute_is_apply'
    )
    commission_range_ids = fields.One2many(
        'sales.commission.range',
        'commission_category_id',
         string='Sales Commission Range Category',
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
