odoo.define("wizard_pos.models", function (require) {
"use strict";

var models = require('point_of_sale.models');

models.load_fields('res.partner', ['last_name','gender','birth_date','line_id', 'mobile', 'member', 'member_number', 'member_date', 'base_branch_id', 'membership_type_id',
 'points', 'membership_type_color', 'is_a_member', 'available_coupon_count', 'stars','car_ids']);
models.load_models([
         {
           model: 'project.project',
           fields: ['id', 'name'],
//           domain: function(self){ return [['id','=', self.pos_session.branch_id[0]]]; }, // domain filter
           loaded: function(self,branches){
              self.branches = branches;
           },
         }
     ]);
models.load_models([
         {
           model: 'membership.type',
           fields: ['id', 'name'],
//           domain: function(self){ return [['id','=', self.pos_session.branch_id[0]]]; }, // domain filter
           loaded: function(self,membership_types){
              self.membership_types = membership_types;
           },
         }
     ]);
models.load_models([
         {
           model: 'car.details',
           fields: ['id', 'name'],
//           domain: function(self){ return [['id','=', self.pos_session.branch_id[0]]]; }, // domain filter
           loaded: function(self,car_details){
              self.car_details = car_details;
           },
         }
     ]);


})
