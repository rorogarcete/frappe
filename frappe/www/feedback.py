import frappe
from frappe.core.doctype.feedback_request.feedback_request import is_valid_feedback_request

no_cache = True

def get_context(context):
	reference_doctype = frappe.form_dict.get("reference_doctype")
	reference_name = frappe.form_dict.get("reference_name")
	communications = frappe.get_all("Communication", filters={
		"reference_doctype": reference_doctype,
		"reference_name": reference_name,
		"communication_type": "Communication"	
	}, fields=["*"], limit_page_length=10, order_by="creation desc")

	return {
		"reference_doctype": reference_doctype,
		"reference_name": reference_name,
		"comment_list": communications,
		"is_communication": True
	}

@frappe.whitelist(allow_guest=True)
def accept(key, sender, reference_doctype, reference_name, feedback, rating):
	""" save the feedback in communication """
	if not reference_doctype and not reference_name:
		frappe.throw("Invalid Reference Doctype, Reference Name")

	if not rating or not feedback:
		frappe.throw("Please give both Rating and Detailed Feedback")

	if not is_valid_feedback_request(key):
		frappe.throw("Link is expired")

	try:
		feedback_request = frappe.db.get_value("Feedback Request", {"key": key})

		communication = frappe.get_doc({
			"rating": rating,
			"sender": sender,
			"status": "Closed",
			"feedback": feedback,
			"doctype": "Communication",
			"sent_or_received": "Received",
			"communication_type": "Feedback",
			"reference_name": reference_name,
			"feedback_request": feedback_request,
			"reference_doctype": reference_doctype,
			"subject": "Feedback for {0} {1}".format(reference_doctype, reference_name),
		}).insert(ignore_permissions=True)

		doc = frappe.get_doc("Feedback Request", feedback_request)
		doc.is_feedback_submitted = 1
		doc.rating = rating
		doc.reference_communication = communication.name
		doc.save(ignore_permissions=True)
		return True
	except Exception as e:
		frappe.throw("Can not submit feedback, Please try again later")
