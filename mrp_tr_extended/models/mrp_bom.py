# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
# from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round


class MrpBomInherit(models.Model):
    """ Defines bills of material for a product or a product template """
    _inherit = 'mrp.bom'
    # _description = 'Bill of Material'
    # _inherit = ['mail.thread']
    # _rec_name = 'product_tmpl_id'
    # _order = "sequence"

    type_bom = fields.Selection([('machine','Machine'),('cleanser','Cleanser'),('service','Service')],string='ประภท')
    # type = fields.Selection([
    #     ('normal', 'Manufacture this product'),
    #     ('phantom', 'Kit'),
    #     ('machine','Machine'),
    #     ('cleanser','Cleanser')], 'BoM Type',
    #     default='normal', required=True)
    permission_machine = fields.Boolean('Machine Use')
    permission_cleanser = fields.Boolean('Cleanser use')

    @api.onchange('type')
    def onpermission_type(self):
        if self:
            if self.type_bom == 'machine':
                permission_machine = True
                permission_cleanser = False
            elif self.type_bom == 'cleanser':
                permission_machine = False
                permission_cleanser = True
            else:
                permission_machine = False
                permission_cleanser = False


class MrpProduction(models.Model):
    _inherit ='mrp.production'

    bom_machine_ids = fields.Many2many('product.product',string='Bom Machine')
    bom_cleanser_ids = fields.Many2many('product.product', string='Bom Cleanser')

    # test 01-10-2019
    @api.onchange('product_id')
    def filter_product(self):
        result_machine = []
        result_cleanser = []
        result_id =[]
        self._cr.execute("select res_id from ir_model_data where name='group_mrp_bom_machine'")
        res_num_machine = self._cr.fetchall()
        if not res_num_machine:
            self._cr.execute("select res_id from ir_model_data where name='group_manufacturing_bom_machine'")
            res_num_machine = self._cr.fetchall()
        # print('res_num_machine : ',res_num_machine)
        # for line in res_num_machine:
        #     result_id.append(line[0])
        id_machine = res_num_machine[0][0]

        self._cr.execute("select uid from res_groups_users_rel where gid=" + str(id_machine))
        ress_machine = self._cr.fetchall()
        for ids_machine in ress_machine:
            result_machine.append(ids_machine[0])

        self._cr.execute("select res_id from ir_model_data where name='group_mrp_bom_cleanser'")
        res_num_cleanser = self._cr.fetchall()
        if not res_num_cleanser:
            self._cr.execute("select res_id from ir_model_data where name='group_manufacturing_bom_cleanser'")
            res_num_cleanser = self._cr.fetchall()

        id_cleanser = res_num_cleanser[0][0]
        self._cr.execute("select uid from res_groups_users_rel where gid=" + str(id_cleanser))
        ress_cleanser = self._cr.fetchall()
        for ids_cleanser in ress_cleanser:
            result_cleanser.append(ids_cleanser[0])

        if self._uid in result_machine and self._uid in result_cleanser:
            print('1')
        elif self._uid in result_machine:
            print('2')
            bom_ids = self.env['mrp.bom'].search([('type_bom','=','machine')])
            product_tmpl_ids = []
            for line in bom_ids:
                product_tmpl_ids.append(line.product_tmpl_id.id)
            product_id = self.env['product.product'].search([('product_tmpl_id','in',product_tmpl_ids)])
            product_ids =[]
            for line in product_id:
                product_ids.append(line.id)
            return {'domain': {'product_id': [('id', 'in', product_ids)]}}
        elif self._uid in result_cleanser:
            print('3')
            bom_ids = self.env['mrp.bom'].search([('type_bom', '=', 'cleanser')])
            product_tmpl_ids = []
            for line in bom_ids:
                product_tmpl_ids.append(line.product_tmpl_id.id)
            product_id = self.env['product.product'].search([('product_tmpl_id', 'in', product_tmpl_ids)])
            product_ids = []
            for line in product_id:
                product_ids.append(line.id)
            return {'domain': {'product_id': [('id', 'in', product_ids)]}}
