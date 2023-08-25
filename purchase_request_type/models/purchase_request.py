# -*- coding: utf-8 -*-
from unittest import result

from odoo import models, fields, api, _
from odoo.addons.test_impex.models import field
from odoo.exceptions import UserError, AccessError
from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta

# from odoo.fields import FailedValue
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, relativedelta, pytz, float_compare

class Purchase_request_inherit(models.Model):
    _inherit = 'purchase.request'

    # @api.model
    # def _get_default_request_type(self):
    #     user_id = self.env['res.users'].browse(self.env.uid)
    #     return user_id.request_type.id

    # request_type = fields.Many2one('purchase.request.type', string="Purchase Request Type",required=True,default=_get_default_request_type)
    request_type = fields.Many2one('purchase.request.type', string="Purchase Request Type",required=True)

    @api.model
    def create(self, vals):
        # print ('--PR CrEATE--')
        # print (vals)
        ############################################ Add purchase reqeust, purchse type, purchase order type to support auto create from procurement ##
        ref = False
        if vals.get('request_type'):
            ref = vals.get('request_type')
        elif vals.get('origin'):
            order_point_origin = vals['origin']
            # print (order_point_origin)
            order_point = order_point_origin.split(',')
            # print (order_point)
            if order_point:
                order_point_id = self.env['stock.warehouse.orderpoint'].search([('name','=',order_point[0])],limit=1)
                if order_point_id:
                    # print (order_point_id)
                    ref = order_point_id.request_type.id
                    vals['request_type'] = ref
                    vals['purchase_type'] = order_point_id.purchase_type.id
                    vals['order_type'] = order_point_id.order_type.id

        ############################################ Add purchase reqeust, purchse type, purchase order type to support auto create from procurement ##
        # print (order_point_origin)
        # ref = vals.get('request_type', 'purchase_sequence_id')
        if ref:
            request_type = self.env['purchase.request.type'].browse(ref)
            date_start = str(vals.get('date_start')).split(' ')
            if request_type.purchase_sequence_id and not vals.get('date_start'):
                se_code = request_type.purchase_sequence_id.code
                if vals.get('name', 'New') == 'New':
                    vals['name'] = self.env['ir.sequence'].next_by_code(se_code) or '/'
            elif vals.get('date_start'):
                if vals.get('name', 'New') == 'New':
                    se_code = request_type.purchase_sequence_id.code
                    vals['name'] = self.env['ir.sequence'].with_context(ir_sequence_date=date_start[0]).next_by_code(se_code) or '/'
                    # vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order') or '/'
            else:
                raise UserError(_('You don\'t  sequence. And try again.'))
                # if vals.get('name', 'New') == 'New':
                #     vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order') or '/'

        return super(Purchase_request_inherit, self).create(vals)