/* Copyright 2018 Tecnativa - David Vidal
   License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */

odoo.define("pos_auto_lot.models", function (require) {
    "use strict";

    var BarcodeParser = require('barcodes.BarcodeParser');
    var PosDB = require('point_of_sale.DB');
    var devices = require('point_of_sale.devices');
    var core = require('web.core');
    var Model = require('web.DataModel');
    var formats = require('web.formats');
    var session = require('web.session');
    var time = require('web.time');
    var utils = require('web.utils');

    var QWeb = core.qweb;
    var _t = core._t;
    var Mutex = utils.Mutex;
    var round_di = utils.round_decimals;
    var round_pr = utils.round_precision;
    var Backbone = window.Backbone;

    var exports = {};
    exports.Orderline = Backbone.Model.extend({
        updatetxt: function(product){
        //add use use_existing_lots option by itaas
            //this.has_product_lot = product.tracking !== 'none' && this.pos.config.use_existing_lots;
            //this.pack_lot_lines  = this.has_product_lot && new PacklotlineCollection(null, {'order_line': this});
            alert('ddd');
        },

    });
};
