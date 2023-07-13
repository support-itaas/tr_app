
Date ? 23/04/2021
Version ? 4.3

1. Api for generating OTP at Signup time

	    pass - ?Signup?  as 3rd argument

	    http://68.183.90.127:8069/web/dataset/call
	    {"jsonrpc":"2.0","method":"call","id":2,
	    "params":{"model":"res.partner","method":"generate_otp_new",
	    "args":	["","0816655718","Signup"],"domain_id":"null","context_id":1}}
		
		
* Modified Api for generating OTP at Signup time (API No. 1)
	
		{"jsonrpc":"2.0","method":"call","id":1,
   		"params":{"model":"res.partner","method":"generate_otp_new",
   		"args":["", "mobile", SOURCE, PARTNER_ID, "NEW_MOBILE"]}}
		
		mobile: Existing mobile number
   		SOURCE :
  				1. Signup: "Signup" for SignUp
  				2. Forget: "Forget" for Change Password
  				3. CHANGE: "CHANGE" is the argument for Change Mobile Number
  		PARTNER_ID: ID of the Partner
		NEW_MOBILE: New mobile number
  		


2. API for generating otp at forget password time

	pass - ?Forget?  as 3rd argument

	    http://68.183.90.127:8069/web/dataset/call
	    {"jsonrpc":"2.0","method":"call","id":2,
	    "params":{"model":"res.partner","method":"generate_otp_new",
	    "args":["", "0816655719","Forget"],"domain_id":"null","context_id":1}
	    }

3. API for OTP Validation

	pass otp in arguments list for signup

	    http://68.183.90.127:8069/web/dataset/call
	    {"jsonrpc":"2.0","method":"call","id":2,
	    "params":{"model":"res.partner","method":"create_from_app_new",
	    "args":[{"name": "Jacob New6","mobile": "0816655719",
	    "email":"jasad@technaureus.com","is_a_member":0,"signup":"mobile",
	    "password":"abcd12345","user_credential":"","customer":"True","otp":"9622"}],
	    "domain_id":"null","context_id":1}}


4. API for Checking Appointment Slot

	arguments ? type (service/coupon)
	product_id
	date in format (YYYY/MM/DD)
	branch_id

	    http://68.183.90.127:8069/web/dataset/call
	    {"jsonrpc":"2.0","method":"call","id":2,
	    "params":{"model":"appointment.appointment","method":"check_appointment_slot",
	    "args":["", "service", 75, "2020-11-19", 6],
	    "domain_id":"null","context_id":1}}



date: 19/04/2021

5. API for Getting All Popup Promotions
   
		POST: http://0.0.0.0:8069/web/dataset/call

		{"jsonrpc":"2.0","method":"call","id":1,
   		"params":{"model":"popup.api","method":"get_popup_promotion",
   		"args":["", PARTNER_ID]}}

		PARTNER_ID: ID of the Partner
		popup_promotion_id: id of the popup promotion
		name: Name of the popup promotion
		image: Image of the popup promotion
		title: Title of the popup promotion
		news_and_promotion_id: ID of the news_and_promotion
		news_and_promotion_name: Name of the news_and_promotion
		link: Link
	

6. API for Restricting Popups

		POST: http://0.0.0.0:8069/web/dataset/call
	
   		{"jsonrpc":"2.0","method":"call","id":1,
   		"params":{"model":"popup.promotion","method":"popup_restrict",
   		"args":["", "PARTNER_ID", POPUP_PROMOTION_ID]}}
   
   		POPUP_PROMOTION_ID: Requested ID popup_promotion_id
		PARTNER_ID: ID of Partner
		popup_promotion_id: ID of the popup_promotion

   
7. API for Getting Version Of the App
   		
		POST: http://0.0.0.0:8069/web/dataset/call
   
		{"jsonrpc":"2.0","method":"call","id":1,
   		"params":{"model":"car.settings",
   		"fields":["id","ios","android"]}}
	
		id: ID
		ios: version of ios
		android: version of android


8. API for Read All Notifications
   
		POST: http://0.0.0.0:8069/web/dataset/call
	
		{"jsonrpc":"2.0","method":"call","id":1,
   		"params":{"model":"wizard.notification","method":"read_all_notification",
   		"args":["", PARTNER_ID]}}
	
		PARTNER_ID: ID of the Partner


9. API for Remove Plate Number
   
		POST: http://0.0.0.0:8069/web/dataset/call
	
		{"jsonrpc":"2.0","method":"call","id":1,
   		"params":{"model":"res.partner","method":"remove_plate_number",
   		"args":["", PARTNER_ID, PLATE_NUMBER]}}
	
		PARTNER_ID: ID of the Partner
		PLATE_NUMBER: PLATE NUMBER of the Vehicle


10. API for Change Mobile Number
		
		POST: http://0.0.0.0:8069/web/dataset/call

		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"res.partner","method":"change_number",
		"args":["", NEW_MOBILE, PARTNER_ID, OTP]}}
	
		NEW_MOBILE: New mobile number
		PARTNER_ID: ID of the Partner
		OTP: OTP


11. API for Request Redeem
	
		POST: http://0.0.0.0:8069/web/dataset/call
	
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"wizard.coupon","method":"button_redeem",
		"args":["", couponIds, plateNumberId, branchId]}}
	
		couponIds: list of coupon ids (eg: [1, 2, 3])


12. API for Cancel Redeem
	
		POST: http://0.0.0.0:8069/web/dataset/call
	
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"wizard.coupon","method":"cancel_redeem",
		"args":["", couponIds]}}
	
		couponIds: list of coupon ids (eg: [1, 2, 3])

13. API for Get FCM Token
	
		POST: http://0.0.0.0:8069/web/dataset/call
	
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"res.partner","method":"get_fcm_token",
		"args":["", PARTNER_ID, FCM_TOKEN]}}
	
		PARTNER_ID: ID of the partner
		FCM_TOKEN: FCM TOKEN 


14. API for Promocode Coupon Transfer
	
		POST: http://0.0.0.0:8069/web/dataset/call
	
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"wizard.coupon","method":"transfer_coupon_app_new",
		"args":["", BARCODE, PARTNER_ID]}}
	
		BARCODE: barcode
    	PARTNER_ID: ID of the partner

15. API for Get Partner Profile
		
		POST: http://0.0.0.0:8069/web/dataset/call
	
		{"jsonrpc":"2.0","method":"call","id":1, 
		"params":{"model":"res.partner","method":"get_partner_profile", 
		"args":["", PARTNER_ID]}}

		PARTNER_ID = ID of the partner

16. API for getting Home Banners

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"promo.banner","fields":["image", "sequence", "news_promo_id"],
		"domain":[]}}

17. API for getting Gallery Tags

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"gallery.tags","fields":["name", "image"],
		"domain":[]}}

18. API for getting Gallery Images

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"image.gallery",
		"fields":["name", "image_wizard", "tag_id", "gallery_type", "video_url"],
		"domain":[["tag_id", "=", tagId]]}}

19. API for getting Branches

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"project.project",
		"fields":["name", "latitude", "longitude", "sequence", "address_string"],
		"domain":[]}}

20. API for getting Branch by Ids

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"project.project",
		"fields":["name", "latitude", "longitude", "sequence", "address_string"],
		"domain":[["id","in",branchIds]]}}

21. API for getting News and Promotions

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"news.promotions",
		"fields":["name", "description", "type", "sequence", "image"],
		"domain":[]}}

22. API for getting News Details

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"news.promotions",
		"fields":["name", "description", "type", "sequence", "image"],
		"domain":[["id", "=", id]]}}

23. API for getting Helps

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"help.support",
		"fields":["name", "answer", "sequence"],
		"domain":[]}}

24. API for getting Coupons

		POST: http://0.0.0.0:8069/web/dataset/call
		{"jsonrpc":"2.0","method":"call","id":1, 
		"params":{"model":"product.product","method":"buy_coupons", 
		"args":["", partnerId]}}

25. API for getting Service List

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"product.product",
		"fields":["name", "is_service", "is_pack", "is_coupon", "list_price", "description_sale", "coupon_validity", "description", "currency_id"],
		"domain":[["is_service", "=", "True"]]}}

26. API for getting Wallet Balance

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"res.partner",
		"fields":["wallet_balance", "currency_id"],
		"domain":[["id", "=", partnerId]]}}

27. API for getting Wallet History

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"account.payment",
		"fields":["payment_date", "branch_id", "amount", "currency_id", "state"],
		"domain":[["add_to_wallet", "=", "True"], ["partner_id", "=", partnerId], ["payment_date", ">=", paymentDateFilter]]}}

28. API for getting Expiry Coupon

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"wizard.coupon",
		"fields":["name", "branch_id", "partner_id", "package_id", "product_id", "purchase_date", "expiry_date", "amount", "currency_id", "image", "description"],
		"domain":[[domain]]}}

		if (toDate) {
      	domain = [["state", "=", "draft"], ["partner_id", "=", partnerId], ["expiry_date", ">=", fromDate], ["expiry_date", "<=", toDate]];
    	} else {
      	domain = [["state", "=", "draft"], ["partner_id", "=", partnerId], ["expiry_date", ">=", fromDate]];
    	}

29. API to get coupons for a partner

		POST: http://0.0.0.0:8069/web/dataset/call
		{"jsonrpc":"2.0","method":"call","id":1, 
		"params":{"model":"wizard.coupon","method":"use_coupon_app", 
		"args":["", partnerId]}}

30. API to get Service History

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"project.task",
		"fields":["name", "project_id", "partner_id", "date_deadline", "description", "amount", "currency_id", "state", "public_price"],
		"domain":[["partner_id", "=", partnerId]]}}

31. API to cancel service

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1, 
		"params":{"model":"project.task","method":"cancel_service_app", 
		"args":["", serviceId]}}

32. API to get Plate Numbers

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"car.details",
		"fields":["name", "is_primary","state_id"],
		"domain":[["partner_id", "=", partnerId]]}}

33. API to create Plate Number

		  createPlateNumber(plateNumber: IAddPlateNumber) {
    		return new Promise((resolve, reject) => {
      		this.odooRpc.createRecordMethod("car.details", plateNumber).then((response) => {
        		if (response.error) {
          			reject(response.error.code + ":" + response.error.data.message);
        		} else {
          			resolve(response.result);
        		}
      			}).catch(err => {
			reject(err);
      		});
    		})
		}

34. API to create Slots

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"appointment.slot",
		"fields":["from_time", "to_time"],
		"domain":[["branch_id", "=", branchId], ["type", "=", type], ["product_id", "=", productId]]}}

35. API to create Slots New

		POST: http://0.0.0.0:8069/web/dataset/call
		{"jsonrpc":"2.0","method":"call","id":1, 
		"params":{"model":"appointment.appointment","method":"check_appointment_slot", 
		"args":["", type,productId,date,branchId]}}

36. API to get profile titles

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"res.partner.title",
		"fields":["shortcut"],
		"domain":[]}}

37. API to get Profile Info

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"res.partner",
		"fields":["name", "last_name", "company_type", "title", "gender", "birth_date", "mobile", "line_id", "email", 
		"street", "street2", "city", "state_id", "country_id", "zip", "member", "member_number", "member_date",
		"membership_type_id", "base_branch_id", "plate_id", "points", "credit", "stars", "last_service", 
		"membership_type_color", "image", "vat"],
		"domain":[["customer", "=", "True"], ["is_a_member", "=", "True"], ["id", "=", partnerId]]}}

38. API to update Profile Info

		return new Promise((resolve, reject) => {
      	this.odooRpc.updateRecordMethod("res.partner", partnerId, profile).then((response) => {
        if (response.error) {
          reject(response.error.code + ":" + response.error.data.message);
        } else {
          resolve(response.result);
        }
      	}).catch(err => {
        reject(err);
      	});
    	})
	
39. API to redeem coupon

		POST: http://0.0.0.0:8069/web/dataset/call
		{"jsonrpc":"2.0","method":"call","id":1, 
		"params":{"model":"wizard.coupon","method":"button_redeem", 
		"args":["", couponIds, plateNumberId, branchId]}}

40. API to create Appointment

	  	createAppointment(appointment: any) {
    		return new Promise((resolve, reject) => {
      		this.odooRpc.createRecordMethod("appointment.appointment", appointment).then((response) => {
        	if (response.error) {
          		reject(response.error.code + ":" + response.error.data.message);
			} else {
          		resolve(response.result);
        		}
      		}).catch(err => {
        	reject(err);
      		});
    		})
			}

41. API to transfer coupon

		POST: http://0.0.0.0:8069/web/dataset/call
		{"jsonrpc":"2.0","method":"call","id":1, 
		"params":{"model":"wizard.coupon","method":"transfer_coupon_app", 
		"args":["", couponIds, partnerId, notes, mobile]}}

42. API to get Journals

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"account.journal",
		"fields":["name"],
		"domain":[["type", "in", ["cash", "bank"]],["is_in_app_wallet","=", 1]}}

43. API to Add money request

  		createAddMoneyRequest(addMoneyRequest: IAddMoneyRequest) {
    	return new Promise((resolve, reject) => {
      	this.odooRpc.createRecordMethod("account.payment", addMoneyRequest).then((response) => {
        if (response.error) {
          reject(response.error.code + ":" + response.error.data.message);
        } else {
          resolve(response.result);
        }

      	}).catch(err => {
        reject(err);
      	});
    	})

  		}

44. API to search partner

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"res.partner",
		"fields":["name", "mobile", "last_name"],
		"domain":[["customer", "=", "True"], ["is_a_member", "=", "True"], ["mobile", "=", mobile]]}}

45. API to search coupon

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"wizard.coupon",
		"fields":["name", "mobile", "last_name"],
		"domain":[["barcode", "=", couponCode], ["state", "=", "draft"]]}}

46. API to Place Order

		POST: http://0.0.0.0:8069/web/dataset/call
		{"jsonrpc":"2.0","method":"call","id":1, 
		"params":{"model":"pos.order","method":"place_order", 
		"args":["", partnerId, branchId, useWallet, cartItems]}}

47. API to get Order history

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"pos.order",
		"fields":["name", "amount_total", "points", "date_order", "branch_id", "pricelist_currency_id"],
		"domain":[["partner_id", "=", partnerId]]}}

48. API to Change password

		POST: http://0.0.0.0:8069/web/dataset/call
		{"jsonrpc":"2.0","method":"call","id":1, 
		"params":{"model":"res.partner","method":"change_password", 
		"args":["", partnerId, oldPassword, newPassword]}}

49. API to Reset password

		POST: http://0.0.0.0:8069/web/dataset/call
		{"jsonrpc":"2.0","method":"call","id":1, 
		"params":{"model":"res.partner","method":"forget_password", 
		"args":["", mobileNo, newPassword,otpCode]}}

50. API for signup

		POST: http://0.0.0.0:8069/web/dataset/call
		{"jsonrpc":"2.0","method":"call","id":1, 
		"params":{"model":"res.partner","method":"create_from_app_new", 
		"args":["", signupRequest]}}

51. API for Mobile Signin

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"res.partner",
		"fields":["name"],
		"domain":[["signup", "=", "mobile"], ["mobile", "=", mobileNo], ["password", "=", password]]}}

52. API for signinwith Google

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"res.partner",
		"fields":["name"],
		"domain":[["signup", "=", "gmail"], ["user_credential", "=", userId], ["password", "=", ""]]}}

53. API for signin with Facebook

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"res.partner",
		"fields":["name"],
		"domain":[["signup", "=", "facebook"], ["user_credential", "=", userId], ["password", "=", ""]]}}

54. API for signin with Apples

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"res.partner",
		"fields":["name"],
		"domain":[["signup", "=", "apple"], ["user_credential", "=", userId], ["password", "=", ""]]}}

55. API to get Countries

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"res.country",
		"fields":["name", "code", "phone_code"],
		"domain":[["available_app", "=", true]]}}

56. API to get terms and conditions

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"terms.conditions",
		"fields":["name"],
		"domain":[]}}

57. API to get Company Info

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"res.company",
		"fields":["social_facebook", "social_instagram", "social_line"],
		"domain":[["id", "=", 1]]}}

58. API to get Notification

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"wizard.notification",
		"fields":["name", "message", "read_message", "partner_id", "message_at"],
		"domain":[["partner_id", "=", partnerId]]}}

59. API to get unread notification

		POST: http://0.0.0.0:8069/web/dataset/call
		{"jsonrpc":"2.0","method":"call","id":1, 
		"params":{"model":"wizard.notification","method":"get_unread_msg_count", 
		"args":["", partnerId]}}

60. APi to Update Notification Read Status

		let args = {
      		read_message: "True"
    		}
		return new Promise((resolve, reject) => {
      	this.odooRpc.updateRecordMethod("wizard.notification", notificationId, args).then((response) => {
        if (response.error) {
          reject(response.error.code + ":" + response.error.data.message);
        } else {
          resolve(response.result);
        }

      	}).catch(err => {
        reject(err);
      	});
    	})

  		}

61. API to get States

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"res.country.state",
		"fields":["id", "name"],
		"domain":[["country_id", "=", countryId]]}}

62. API to get brand

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"fleet.vehicle.model.brand",
		"fields":["id", "name"],
		"domain":[]}}

63. API to get Model

		POST: http://0.0.0.0:8069/web/dataset/search_read
		{"jsonrpc":"2.0","method":"call","id":1,
		"params":{"model":"fleet.vehicle.model",
		"fields":["id", "name"],
		"domain":[["brand_id", "=", brandID]]}}










		















		






		

		

























		



















	

























		













		

		


		


		


		
	


