# -*- coding: utf-8 -*-
from odoo import fields, models, api

class SalesCommissionRange(models.Model):
    _name = 'sales.commission.range'
    
    starting_range = fields.Float(
        string='Start Total',
        required=True
    )
    ending_range = fields.Float(
        string='End Total',
        required=True
    )
    sales_manager_commission = fields.Float(
        'Sales Manager Commission(%)',
        required=True
    )
    sales_person_commission = fields.Float(
        'Sales Person Commission(%)',
        required=True
    )
    sales_manager_commission_amount = fields.Float(
        'Sales Manager Commission Amount',
        required=True
    )
    sales_person_commission_amount = fields.Float(
        'Sales Person Commission Amount',
        required=True
    )
    
    commission_product_id = fields.Many2one(
        'product.template',
        string='Product',
    )
    commission_team_id = fields.Many2one(
        'crm.team',
        string='Sales Team',
    )
    commission_category_id = fields.Many2one(
        'product.category',
        string='Commission Product Category',
    )

class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    @api.multi
    @api.depends('is_apply')
    def _compute_is_apply(self):
#         commission_based_on = self.env['ir.values'].get_default('sale.config.settings', 'commission_based_on')
        commission_based_on = self.env['ir.config_parameter'].sudo().get_param('sales_commission_target_fix_percentage.commission_based_on') #odoo11
        for rec in self:
            if commission_based_on == 'product_template':
                rec.is_apply = True
    
    
    commission_type = fields.Selection(
        string="Commission Amount Type",
        selection=[
            ('percentage', 'By Percentage'),
            ('fix', 'Fixed Amount'),
        ],
    )
    is_commission_product = fields.Boolean(
        'Is Commission Product ?'
    )
    is_apply = fields.Boolean(
        string='Is Apply ?',
        compute='_compute_is_apply'
    )
    commission_range_ids = fields.One2many(
        'sales.commission.range',
        'commission_product_id',
         string='Sales Commission Range',
    )
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: