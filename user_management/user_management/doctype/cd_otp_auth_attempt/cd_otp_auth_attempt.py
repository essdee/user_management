# -*- coding: utf-8 -*-
# Copyright (c) 2021, Essdee and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.model.document import Document
import requests
from frappe.utils import time_diff, now_datetime
from frappe.core.doctype.user.user import generate_keys
import secrets
from frappe.utils.password import get_decrypted_password

class CDOTPAuthAttempt(Document):
	pass

@frappe.whitelist(allow_guest=True)
def initiate_otp(mobile_number):
	settings = frappe.get_single('CD User Management Settings')
	frappe.set_user(settings.default_user)
	generated_otp = '{:0>4}'.format(secrets.randbelow(10**4))
	user = frappe.db.get_value('User', {'mobile_no':mobile_number})
	if not user:
		frappe.local.response.http_status_code = 404
		frappe.local.response["message"] = "User Not Found"
	
	otp_auth_attempt_doc = frappe.new_doc('CD OTP Auth Attempt')
	otp_auth_attempt_doc.update({
		"mobile_number": mobile_number,
		"login_status": 'OTP Generated',
		"generated_otp": generated_otp,
		"generated_time": now_datetime().__str__()[:-7]
	})
	otp_auth_attempt_doc.save()
	response = send_otp(mobile_number, generated_otp)
	json_res = response.json()
	
	# TODO: handle different errors from MSG91 API and take appropriate actions
	if response.status_code == 200:
		if json_res['type']== 'error':
			frappe.log_error("otp auth attempt name: "+ otp_auth_attempt_doc.name+ " | error message: " + json_res['message'] , "Send OTP Error")
			frappe.local.response.http_status_code = 500
			frappe.local.response["message"] = "OTP Generation Failed"

		if json_res['type'] == 'success':
			frappe.local.response["otp_auth_attempt_name"] = otp_auth_attempt_doc.name

	else:
		frappe.log_error("otp auth attempt name: "+otp_auth_attempt_doc.name+ " | code: "+str(response.status_code)+ " | error message: " +  response.text , "Send OTP Error")
		frappe.local.response.http_status_code = 500
		frappe.local.response["message"] = "OTP Generation Failed"
	frappe.local.response["otp_auth_attempt_name"] = otp_auth_attempt_doc.name

@frappe.whitelist(allow_guest = True)
def verify_otp(otp_auth_attempt_name, incoming_otp, action):
	settings = frappe.get_single('CD User Management Settings')
	frappe.set_user(settings.default_user)
	otp_auth_attempt_doc = frappe.get_doc("CD OTP Auth Attempt", {"name": otp_auth_attempt_name, "login_status": "OTP Generated"})
	verification_time = now_datetime().__str__()[:-7]
	otp_expiry_limit  = settings.otp_expiry_limit_in_mins
	max_otp_attempts = settings.max_otp_attempts

	if not (time_diff(verification_time, otp_auth_attempt_doc.generated_time).total_seconds()/60) <= otp_expiry_limit:
		otp_auth_attempt_doc.login_status = 'Expired'
		otp_auth_attempt_doc.save()
		frappe.local.response.http_status_code = 429
		frappe.local.response["message"] = "OTP Expired"
	
	if otp_auth_attempt_doc.generated_otp == incoming_otp:
		otp_auth_attempt_doc.login_status = 'Success'
		otp_auth_attempt_doc.verify_action = action.replace('_',' ').title()
		otp_auth_attempt_doc.save()

		user = frappe.get_doc("User", {'mobile_no':otp_auth_attempt_doc.mobile_number})
		if action == 'get_reset_password_key':
			user.reset_password()
			frappe.local.response["reset_password_key"] = user.reset_password_key
		
		if action == 'get_api_credentials':
			frappe.local.response["api_key"] = user.api_key
			frappe.local.response["api_secret"] = generate_keys(user.name)['api_secret']

	else:
		if len(otp_auth_attempt_doc.failed_attempts) == max_otp_attempts:
			otp_auth_attempt_doc.login_status = 'Blocked'
			otp_auth_attempt_doc.save()
			frappe.local.response.http_status_code = 429
			frappe.local.response["message"] = "Maximum Limit Reached"
		else:
			otp_auth_attempt_doc.append('failed_attempts',{'failed_incoming_otp': incoming_otp})
			otp_auth_attempt_doc.save()
			frappe.local.response.http_status_code = 401
			frappe.local.response["message"] = "Incorrect OTP"

def send_otp(mobile_number, generated_otp):
	settings = frappe.get_single('CD User Management Settings')
	template_id = settings.msg91_template_id
	authkey = get_decrypted_password('CD User Management Settings', 'CD User Management Settings',
			fieldname='msg91_auth_key', raise_exception=False)
	mobile_number = '91'+mobile_number
	url = f"https://api.msg91.com/api/v5/otp/?otp={generated_otp}&authkey={authkey}&mobile={mobile_number}&template_id={template_id}"
	headers = {
		"Content-Type": "application/json"
	}
	response = requests.request("GET", url, headers=headers)
	return response

@frappe.whitelist(allow_guest = True)
def resend_otp(otp_auth_attempt_name):
	settings = frappe.get_single('CD User Management Settings')
	frappe.set_user(settings.default_user)
	default_limit = settings.resend_otp_limit
	mobile_number = '91'+frappe.db.get_value('CD OTP Auth Attempt', {'name':otp_auth_attempt_name}, 'mobile_number')
	authkey = get_decrypted_password('CD User Management Settings', 'CD User Management Settings',
			fieldname='msg91_auth_key', raise_exception=False)
	otp_auth_attempt_doc = frappe.get_doc('CD OTP Auth Attempt', otp_auth_attempt_name)
	otp_auth_attempt_doc.resend_count += 1
	otp_auth_attempt_doc.save()
	resend_count = otp_auth_attempt_doc.resend_count
	if resend_count <= default_limit:
		if resend_count == default_limit:
			url = f"https://api.msg91.com/api/v5/otp/retry?mobile={mobile_number}&authkey={authkey}"
		elif resend_count < default_limit:
			url = f"https://api.msg91.com/api/v5/otp/retry?mobile={mobile_number}&authkey={authkey}&retrytype=text"
		headers = {
			"Content-Type": "application/json"
		}
		response = requests.request("GET", url, headers=headers)
		json_res = response.json()
		if response.status_code == 200:
			if json_res['type'] == 'error':
				frappe.log_error("otp auth attempt name: "+ otp_auth_attempt_name+" | error message: " + json_res['message'] , "Resend OTP Error")
				frappe.local.response.http_status_code = 500
				frappe.local.response["message"] = "Resend OTP Failed"
			if json_res['type'] == 'success':
				frappe.local.response["message"] = "OTP Sent Successfully"

		else:
			frappe.log_error("otp auth attempt name: "+ otp_auth_attempt_name + " | code: " + str(response.status_code) + " | response: " + response.text , "Resend OTP Error")
			frappe.local.response.http_status_code = 500
			frappe.local.response["message"] = "Resend OTP Failed"
	else:
		frappe.local.response.http_status_code = 429
		frappe.local.response["message"] = "Maximum Limit Reached"