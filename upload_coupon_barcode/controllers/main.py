# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import http
from odoo.models import check_method_name
from odoo.api import call_kw, Environment
from odoo.http import content_disposition, dispatch_rpc, request, \
    serialize_exception as _serialize_exception, Response

class DataSet(http.Controller):

    def _call_kw(self, model, method, args, kwargs):
        check_method_name(method)
        return call_kw(request.env[model], method, args, kwargs)

    @http.route('/web/dataset/call_button_wizard', type='json', auth="user")
    def call_button(self, model, method, args, domain_id=None, context_id=None):
        action = self._call_kw(model, method, args, {})
        # if isinstance(action, dict) and action.get('type') != '':
        #     return clean_action(action)
        return action