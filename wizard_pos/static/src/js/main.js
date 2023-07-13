odoo.define('pos_customer_field.pos_customer_field', function (require) {
"use strict";

    var models = require('point_of_sale.models');
    var gui = require('point_of_sale.gui');
    var rpc = require('web.rpc');
    var screens = require('point_of_sale.screens');

    models.load_fields("res.partner", ['car_ids']);

    models.load_models([
        {
            model: 'car.details',
            fields: ['name'],
            loaded: function(self,car_details){
                self.car_details = car_details;
                var get_car_detail_by_id = {};
                _.each(car_details, function (car_detail) {
                    get_car_detail_by_id[car_detail.id] = car_detail;
                });
                self.get_car_detail_by_id = get_car_detail_by_id;
            },
        }],{'after': 'res.partner'});

    var ClientListScreenWidget = screens.ClientListScreenWidget.extend({
        show: function(){
            this._super();
            this.car_detail_input = [];
        },
        save_client_details: function(partner) {
            var self = this;
            this.$('.client-details-contents .client-car-detail-input').val("["+this.car_detail_input.toString()+"]");
            this.car_detail_input = [];
            this._super(partner);
        },
        reload_partners: function(){
            var self = this;
            var def  = new $.Deferred();
            return this._super().then(function () {
                rpc.query({
                    model: 'car.details',
                    method: 'search_read',
                    args: [[], []],
                }, {
                    timeout: 3000,
                    shadow: true,
                })
                .then(function(car_details){
                    if (car_details) {
                        self.pos.car_details = car_details;
                        var get_car_detail_by_id = {};
                        _.each(car_details, function (car_detail) {
                            get_car_detail_by_id[car_detail.id] = car_detail;
                        });
                        self.pos.get_car_detail_by_id = get_car_detail_by_id;
                        def.resolve();
                    } else {
                        def.reject();
                    }
                }, function(type,err){ def.reject(); });
                return def;
            });
        },
        display_client_details: function(visibility,partner,clickpos){
            var self = this;
            this._super(visibility,partner,clickpos);
            var contents = this.$('.client-details-contents');

            if(visibility === 'edit'){
                contents.off('click','.add_plate_number');
                contents.off('click', '.delete');
                contents.off('change', '.client-car-detail');
                contents.on('click', '.add_plate_number', function(ev){
                    var last_tr = contents.find('.client-line-detail:last');
                    last_tr.clone().insertAfter(last_tr).data('id', 0).find( 'input.client-car-detail' ).val('');
                });
                contents.on('change', '.client-car-detail', function(ev){
                    var id = $(this).parents('tr').data('id');
                    var name = $(this).val();
                    if (id == 0) {
                        self.car_detail_input.push("(0, 0, {'name': '"+name+"'})");
                    } else {
                        self.car_detail_input.push("(1, '"+id+"', {'name': '"+name+"'})");
                    }
                });
                contents.on('click', '.delete', function(ev){
                    var id = $(this).parents('tr').data('id');
                    self.car_detail_input.push("(2, '"+id+"')");
                    $(this).parents('tr').remove();
                });
            }
        },
    });
    gui.define_screen({name:'clientlist', widget: ClientListScreenWidget});
});