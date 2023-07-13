odoo.define('wizard_pos_customer_filter.models', function (require) {
"use strict";
    var models = require('point_of_sale.models');
    var rpc = require('web.rpc');

    var models_models = models.PosModel.prototype.models;

    for(var i=0; i<models_models.length; i++){
        var model=models_models[i];
        if(model.model === 'res.partner'){
            model.fields.push('is_available_in_pos');
            model.domain.push(['is_available_in_pos','=',true]);
        }
    }

    models.PosModel = models.PosModel.extend({

    load_new_partners: function(load_new_partners){
        var self = this;
        var def  = new $.Deferred();
        var fields = _.find(this.models,function(model){ return model.model === 'res.partner'; }).fields;
        var domain = [['customer','=',true],['write_date','>',this.db.get_partner_write_date()],['is_available_in_pos','=',true]];
        rpc.query({
                model: 'res.partner',
                method: 'search_read',
                args: [domain, fields],
            }, {
                timeout: 3000,
                shadow: true,
            })
            .then(function(partners){
                if (self.db.add_partners(partners)) {   // check if the partners we got were real updates
                    def.resolve();
                } else {
                    def.reject();
                }
            }, function(type,err){ def.reject(); });
        return def;
    }
});
});