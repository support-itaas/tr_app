# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).

import odoo
from odoo import api, models
from odoo import SUPERUSER_ID
from odoo import http, _
from odoo.exceptions import AccessError
from odoo.http import request
import base64
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from odoo.addons.portal.controllers.portal import get_records_pager, pager as portal_pager, CustomerPortal
#
#
class CustomerPortal(CustomerPortal):

    @http.route(['/my/purchase/<int:order_id>'], type='http', auth="user", website=True)
    def portal_my_purchase_order(self, order_id=None, **kw):
        print ('---X___')
        response = super(CustomerPortal, self).portal_my_purchase_order(order_id, **kw)
        if not 'order' in response.qcontext:
            print ('---NO ORDER< RETURN')
            return response
        print ('--skip-return')
        order = response.qcontext['order']
        if kw.get('websale_reply'):
            customer_msg = _('%s') % (kw.get('websale_reply'))
            order.with_context(ecom_reply=True).sudo().message_post(body=customer_msg,
                                                                    message_type='comment',
                                                                    subtype="mt_comment",
                                                                    ecom_reply='OK',
                                                                    author_id=order.partner_id.id, **kw)
        return response
        # return request.render("purchase.portal_my_purchase_order", values)

# class website_account(website_account):
#
#     @http.route(['/my/orders/<int:order>'], type='http', auth="user", website=True)
#     def orders_followup(self, order=None, **kw):
#         response = super(website_account, self).orders_followup(order, **kw)
#         if not 'order' in response.qcontext:
#             return response
#         order = response.qcontext['order']
#         # attachment_list = request.httprequest.files.getlist('attachment_ids')
#
#
#         if kw.get('websale_reply'):
#
#             customer_msg = _('%s') % (kw.get('websale_reply'))
#             order.with_context(ecom_reply=True).sudo().message_post(body=customer_msg,
#                                       message_type='comment',
#                                       subtype="mt_comment",
#                                       ecom_reply='OK',
#                                       author_id=order.partner_id.id, **kw)
#
#             # return request.redirect('/page/thank-you?#scrollTop=0')
#
#         return response
#
