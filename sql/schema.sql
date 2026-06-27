-- ============================================================
-- Onboarding DB (onboarding.db)
-- Reference DDL from core/models.py (not migration SSoT)
-- Authoritative migrations: alembic -x db=onboarding|runtime upgrade head
-- Last sync: 2026-06-15
-- ============================================================


CREATE TABLE approvals (
	approval_id VARCHAR(36) NOT NULL, 
	scope VARCHAR NOT NULL, 
	target_id VARCHAR(36) NOT NULL, 
	approved_by VARCHAR(36) NOT NULL, 
	approved_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	detail TEXT, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (approval_id), 
	FOREIGN KEY(approved_by) REFERENCES operators (op_id)
)




CREATE TABLE audit_logs (
	log_id VARCHAR(36) NOT NULL, 
	op_id VARCHAR(36), 
	action VARCHAR(100), 
	target_id VARCHAR(36), 
	reason VARCHAR(500), 
	access_time DATETIME DEFAULT CURRENT_TIMESTAMP, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (log_id), 
	FOREIGN KEY(op_id) REFERENCES operators (op_id)
)




CREATE TABLE devices (
	dev_id VARCHAR(36) NOT NULL, 
	man_id VARCHAR(36), 
	vendor_id VARCHAR(36), 
	serial_num VARCHAR NOT NULL, 
	device_type VARCHAR, 
	model_name VARCHAR, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	PRIMARY KEY (dev_id), 
	FOREIGN KEY(man_id) REFERENCES manufacturers (man_id), 
	FOREIGN KEY(vendor_id) REFERENCES vendors (vendor_id), 
	UNIQUE (serial_num)
)




CREATE TABLE document_fields (
	field_id VARCHAR(36) NOT NULL, 
	temp_id VARCHAR(36) NOT NULL, 
	field_name VARCHAR NOT NULL, 
	field_type VARCHAR NOT NULL, 
	extract_method VARCHAR NOT NULL, 
	extract_rule VARCHAR, 
	is_required INTEGER, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	PRIMARY KEY (field_id), 
	FOREIGN KEY(temp_id) REFERENCES document_templates (temp_id)
)




CREATE TABLE document_templates (
	temp_id VARCHAR(36) NOT NULL, 
	hosp_code VARCHAR, 
	temp_name VARCHAR NOT NULL, 
	doc_type VARCHAR NOT NULL, 
	vendor_name VARCHAR, 
	identifier_keyword VARCHAR, 
	confidence_policy VARCHAR NOT NULL, 
	approved INTEGER, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	PRIMARY KEY (temp_id), 
	CONSTRAINT uq_doctemp_org_type_keyword UNIQUE (org_id, doc_type, identifier_keyword)
)




CREATE TABLE frequent_hospitals (
	fh_id VARCHAR(36) NOT NULL, 
	hosp_code VARCHAR NOT NULL, 
	hosp_name VARCHAR NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	PRIMARY KEY (fh_id), 
	UNIQUE (hosp_code)
)




CREATE TABLE manufacturers (
	man_id VARCHAR(36) NOT NULL, 
	man_name VARCHAR NOT NULL, 
	country VARCHAR, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	PRIMARY KEY (man_id), 
	UNIQUE (man_name)
)




CREATE TABLE operators (
	op_id VARCHAR(36) NOT NULL, 
	vendor_id VARCHAR(36), 
	name VARCHAR(50) NOT NULL, 
	phone_num VARCHAR(20), 
	email VARCHAR(100), 
	role VARCHAR(20), 
	is_active INTEGER, 
	last_login_at DATETIME, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (op_id), 
	FOREIGN KEY(vendor_id) REFERENCES vendors (vendor_id), 
	UNIQUE (phone_num)
)




CREATE TABLE security_settings (
	ss_id VARCHAR(36) NOT NULL, 
	op_id VARCHAR(36) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	password_set_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	password_snooze_until DATETIME, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (ss_id), 
	UNIQUE (op_id), 
	FOREIGN KEY(op_id) REFERENCES operators (op_id)
)




CREATE TABLE vendors (
	vendor_id VARCHAR(36) NOT NULL, 
	vendor_name VARCHAR NOT NULL, 
	device_hwid VARCHAR, 
	manager_name VARCHAR, 
	contact VARCHAR, 
	biz_num VARCHAR NOT NULL, 
	company_name VARCHAR, 
	rep_name VARCHAR, 
	address VARCHAR, 
	biz_type VARCHAR, 
	biz_item VARCHAR, 
	email VARCHAR, 
	bc_doc_path VARCHAR, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	PRIMARY KEY (vendor_id), 
	UNIQUE (biz_num)
)



-- ============================================================
-- Runtime DB (runtime.db)
-- Reference DDL from core/models.py (not migration SSoT)
-- Authoritative migrations: alembic -x db=onboarding|runtime upgrade head
-- Last sync: 2026-06-15
-- ============================================================


CREATE TABLE claim_docs (
	cd_id VARCHAR(36) NOT NULL, 
	claim_id VARCHAR(36) NOT NULL, 
	doc_type VARCHAR(10) NOT NULL, 
	ps_id VARCHAR(36), 
	sr_id VARCHAR(36), 
	ct_id VARCHAR(36), 
	rt_id VARCHAR(36), 
	is_required BOOLEAN, 
	is_attached BOOLEAN, 
	attached_at DATETIME, 
	required_reason VARCHAR(50), 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (cd_id), 
	CONSTRAINT uq_claim_doc UNIQUE (claim_id, doc_type, ps_id, sr_id), 
	FOREIGN KEY(claim_id) REFERENCES claims (claim_id), 
	FOREIGN KEY(ps_id) REFERENCES prescriptions (ps_id), 
	FOREIGN KEY(sr_id) REFERENCES sleep_reports (sr_id), 
	FOREIGN KEY(ct_id) REFERENCES contracts (ct_id), 
	FOREIGN KEY(rt_id) REFERENCES return_receipts (rt_id)
)




CREATE TABLE claims (
	claim_id VARCHAR(36) NOT NULL, 
	mu_id VARCHAR(36), 
	pat_id VARCHAR(36), 
	ps_id VARCHAR(36), 
	billing_month VARCHAR(7) NOT NULL, 
	period_start DATE, 
	period_end DATE, 
	period_days INTEGER, 
	split_reason VARCHAR, 
	billing_rate INTEGER, 
	base_total INTEGER, 
	base_insurance INTEGER, 
	base_self_pay INTEGER, 
	travel_deduct_days INTEGER, 
	travel_deduct_amount INTEGER, 
	return_deduct_to_self INTEGER, 
	total_amount INTEGER, 
	final_insurance INTEGER, 
	final_self_pay INTEGER, 
	status VARCHAR, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	PRIMARY KEY (claim_id), 
	FOREIGN KEY(mu_id) REFERENCES monthly_updates (mu_id), 
	FOREIGN KEY(pat_id) REFERENCES patients (pat_id), 
	FOREIGN KEY(ps_id) REFERENCES prescriptions (ps_id)
)




CREATE TABLE consumables (
	c_id VARCHAR(36) NOT NULL, 
	pat_id VARCHAR(36), 
	c_type VARCHAR, 
	c_detail_type VARCHAR, 
	c_price INTEGER, 
	c_note VARCHAR, 
	purchase_date DATETIME, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (c_id), 
	FOREIGN KEY(pat_id) REFERENCES patients (pat_id)
)




CREATE TABLE contracts (
	ct_id VARCHAR(36) NOT NULL, 
	pat_id VARCHAR(36), 
	doc_id VARCHAR(36), 
	start_date DATETIME, 
	end_date DATETIME, 
	device_serial VARCHAR, 
	rental_fee INTEGER, 
	device_dn INTEGER, 
	model_name VARCHAR, 
	device_type VARCHAR, 
	mask_fee INTEGER, 
	contact VARCHAR, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (ct_id), 
	FOREIGN KEY(pat_id) REFERENCES patients (pat_id), 
	FOREIGN KEY(doc_id) REFERENCES patient_documents (doc_id)
)




CREATE TABLE device_assignments (
	da_id VARCHAR(36) NOT NULL, 
	dev_id VARCHAR(36) NOT NULL, 
	pat_id VARCHAR(36) NOT NULL, 
	ct_id VARCHAR(36), 
	assigned_at DATE NOT NULL, 
	returned_at DATE, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	PRIMARY KEY (da_id), 
	FOREIGN KEY(pat_id) REFERENCES patients (pat_id), 
	FOREIGN KEY(ct_id) REFERENCES contracts (ct_id)
)




CREATE TABLE excel_import_sessions (
	session_id VARCHAR(36) NOT NULL, 
	file_path VARCHAR NOT NULL, 
	original_filename VARCHAR, 
	first_data_row INTEGER NOT NULL, 
	sample_patient_json TEXT NOT NULL, 
	header_candidates_json TEXT, 
	column_mapping_json TEXT, 
	preview_rows_json TEXT, 
	anomalies_json TEXT, 
	status VARCHAR(20) NOT NULL, 
	created_by_op_id VARCHAR(36), 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	confirmed_at DATETIME, 
	confirmed_by_op_id VARCHAR(36), 
	success_count INTEGER, 
	failed_count INTEGER, 
	failed_detail_json TEXT, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	PRIMARY KEY (session_id)
)




CREATE TABLE extracted_data (
	data_id VARCHAR(36) NOT NULL, 
	doc_id VARCHAR(36), 
	raw_key VARCHAR, 
	raw_value VARCHAR, 
	confidence FLOAT, 
	is_confirmed INTEGER, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (data_id), 
	FOREIGN KEY(doc_id) REFERENCES patient_documents (doc_id)
)




CREATE TABLE monthly_updates (
	mu_id VARCHAR(36) NOT NULL, 
	pat_id VARCHAR(36), 
	billing_month VARCHAR(7) NOT NULL, 
	comp_status VARCHAR, 
	split_claim_count INTEGER, 
	claim_id_1 VARCHAR(36), 
	claim_id_2 VARCHAR(36), 
	claim_id_3 VARCHAR(36), 
	status VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	org_id VARCHAR, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (mu_id), 
	CONSTRAINT uq_mu_pat_month UNIQUE (pat_id, billing_month), 
	FOREIGN KEY(pat_id) REFERENCES patients (pat_id)
)




CREATE TABLE ocr_sessions (
	session_id VARCHAR(36) NOT NULL, 
	doc_id VARCHAR(36) NOT NULL, 
	status VARCHAR(40) NOT NULL, 
	adjusted_bboxes TEXT, 
	local_results TEXT, 
	local_corrections TEXT, 
	local_reviewed_by VARCHAR(36), 
	local_reviewed_at DATETIME, 
	matched_pat_id VARCHAR(36), 
	pat_match_score FLOAT, 
	matched_fh_id VARCHAR(36), 
	masked_image_path VARCHAR, 
	mask_reviewed_by VARCHAR(36), 
	mask_reviewed_at DATETIME, 
	external_called_at DATETIME, 
	external_response_time FLOAT, 
	external_results TEXT, 
	external_corrections TEXT, 
	external_reviewed_by VARCHAR(36), 
	external_reviewed_at DATETIME, 
	final_prescription_id VARCHAR(36), 
	final_sleep_report_id VARCHAR(36), 
	final_mu_id VARCHAR(36), 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (session_id), 
	FOREIGN KEY(doc_id) REFERENCES patient_documents (doc_id), 
	FOREIGN KEY(matched_pat_id) REFERENCES patients (pat_id), 
	FOREIGN KEY(final_prescription_id) REFERENCES prescriptions (ps_id), 
	FOREIGN KEY(final_sleep_report_id) REFERENCES sleep_reports (sr_id), 
	FOREIGN KEY(final_mu_id) REFERENCES monthly_updates (mu_id)
)




CREATE TABLE patient_alerts (
	alert_id VARCHAR(36) NOT NULL, 
	pat_id VARCHAR(36), 
	alert_type VARCHAR, 
	billing_month VARCHAR(7), 
	description VARCHAR, 
	due_date DATE, 
	is_resolved BOOLEAN, 
	resolved_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	PRIMARY KEY (alert_id), 
	FOREIGN KEY(pat_id) REFERENCES patients (pat_id)
)




CREATE TABLE patient_business_certificates (
	pbc_id VARCHAR(36) NOT NULL, 
	pat_id VARCHAR(36) NOT NULL, 
	biz_num VARCHAR NOT NULL, 
	company_name VARCHAR, 
	rep_name VARCHAR, 
	address VARCHAR, 
	biz_type VARCHAR, 
	biz_item VARCHAR, 
	email VARCHAR, 
	doc_path VARCHAR, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	PRIMARY KEY (pbc_id), 
	FOREIGN KEY(pat_id) REFERENCES patients (pat_id), 
	UNIQUE (biz_num)
)




CREATE TABLE patient_documents (
	doc_id VARCHAR(36) NOT NULL, 
	pat_id VARCHAR(36), 
	doc_type VARCHAR, 
	directory VARCHAR, 
	generated_filename VARCHAR, 
	issue_date VARCHAR, 
	file_status VARCHAR, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	PRIMARY KEY (doc_id), 
	CONSTRAINT uq_docinfo_org_filename UNIQUE (org_id, generated_filename), 
	FOREIGN KEY(pat_id) REFERENCES patients (pat_id)
)




CREATE TABLE patients (
	pat_id VARCHAR(36) NOT NULL, 
	pat_name VARCHAR NOT NULL, 
	chart_num VARCHAR NOT NULL, 
	reg_num_front VARCHAR(6), 
	reg_num_back VARCHAR(7), 
	phone_num VARCHAR, 
	address VARCHAR, 
	address_detail VARCHAR(200), 
	birth_date DATE, 
	uses_biz_num BOOLEAN, 
	biz_num VARCHAR, 
	pbc_id VARCHAR(36), 
	is_auto_registered BOOLEAN NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	is_medicaid BOOLEAN NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	PRIMARY KEY (pat_id), 
	CONSTRAINT uq_patient_org_chart UNIQUE (org_id, chart_num), 
	FOREIGN KEY(pbc_id) REFERENCES patient_business_certificates (pbc_id)
)




CREATE TABLE prescriptions (
	ps_id VARCHAR(36) NOT NULL, 
	pat_id VARCHAR(36), 
	doc_id VARCHAR(36), 
	issue_date DATETIME, 
	start_date DATETIME, 
	end_date DATETIME, 
	duration INTEGER, 
	device_type VARCHAR, 
	pressure_val1 FLOAT, 
	pressure_val2 FLOAT, 
	is_post_compliance BOOLEAN, 
	comp_eval_start_date DATETIME, 
	comp_eval_pass_date DATETIME, 
	comp_over_4h_days INTEGER, 
	doctor_name VARCHAR, 
	doctor_license VARCHAR, 
	hosp_name VARCHAR, 
	hosp_code VARCHAR, 
	disease_code VARCHAR, 
	disease_name VARCHAR, 
	phone VARCHAR, 
	serial_num VARCHAR, 
	specialist_num VARCHAR, 
	superseded_by_ps_id VARCHAR(36), 
	superseded_date DATE, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (ps_id), 
	FOREIGN KEY(pat_id) REFERENCES patients (pat_id), 
	FOREIGN KEY(doc_id) REFERENCES patient_documents (doc_id), 
	FOREIGN KEY(superseded_by_ps_id) REFERENCES prescriptions (ps_id)
)




CREATE TABLE receipts (
	rc_id VARCHAR(36) NOT NULL, 
	pat_id VARCHAR(36), 
	doc_id VARCHAR(36), 
	rcpt_approval_num VARCHAR, 
	rcpt_issue_date DATETIME, 
	registration_num VARCHAR, 
	total_amount INTEGER, 
	attachment_path VARCHAR, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (rc_id), 
	FOREIGN KEY(pat_id) REFERENCES patients (pat_id), 
	FOREIGN KEY(doc_id) REFERENCES patient_documents (doc_id)
)




CREATE TABLE return_receipts (
	rt_id VARCHAR(36) NOT NULL, 
	pat_id VARCHAR(36), 
	doc_id VARCHAR(36), 
	return_date DATETIME, 
	device_serial VARCHAR, 
	valid_until DATE, 
	billing_restarted_at DATETIME, 
	restarted_by_op_id VARCHAR(36), 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (rt_id), 
	FOREIGN KEY(pat_id) REFERENCES patients (pat_id), 
	FOREIGN KEY(doc_id) REFERENCES patient_documents (doc_id)
)




CREATE TABLE sleep_reports (
	sr_id VARCHAR(36) NOT NULL, 
	pat_id VARCHAR(36), 
	doc_id VARCHAR(36), 
	report_start_date DATETIME, 
	report_end_date DATETIME, 
	device_serial VARCHAR, 
	avg_usage_time FLOAT, 
	pressure_val1 FLOAT, 
	pressure_val2 FLOAT, 
	ahi FLOAT, 
	manufacturer VARCHAR, 
	usage_days INTEGER, 
	total_days INTEGER, 
	over_4h_days INTEGER, 
	mode VARCHAR, 
	device_type VARCHAR, 
	birth_date VARCHAR, 
	linked_ps_id VARCHAR(36), 
	report_month VARCHAR(7), 
	compliance_status VARCHAR(20), 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (sr_id), 
	FOREIGN KEY(pat_id) REFERENCES patients (pat_id), 
	FOREIGN KEY(doc_id) REFERENCES patient_documents (doc_id), 
	FOREIGN KEY(linked_ps_id) REFERENCES prescriptions (ps_id)
)




CREATE TABLE system_logs (
	id VARCHAR(36) NOT NULL, 
	level VARCHAR(20), 
	step_name VARCHAR(100), 
	message TEXT, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	PRIMARY KEY (id)
)




CREATE TABLE tax_invoices (
	ti_id VARCHAR(36) NOT NULL, 
	pat_id VARCHAR(36), 
	doc_id VARCHAR(36), 
	ti_approval_num VARCHAR, 
	ti_issue_date DATETIME, 
	registration_num VARCHAR, 
	total_amount INTEGER, 
	attachment_path VARCHAR, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (ti_id), 
	FOREIGN KEY(pat_id) REFERENCES patients (pat_id), 
	FOREIGN KEY(doc_id) REFERENCES patient_documents (doc_id)
)




CREATE TABLE travels (
	t_id VARCHAR(36) NOT NULL, 
	pat_id VARCHAR(36), 
	depart_date DATETIME, 
	entry_date DATETIME, 
	return_record_path VARCHAR, 
	rt_id VARCHAR(36), 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (t_id), 
	FOREIGN KEY(pat_id) REFERENCES patients (pat_id), 
	FOREIGN KEY(rt_id) REFERENCES return_receipts (rt_id)
)




CREATE TABLE workflow_sessions (
	session_id VARCHAR(36) NOT NULL, 
	op_id VARCHAR(36) NOT NULL, 
	started_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	finished_at DATETIME, 
	status VARCHAR(20), 
	current_step VARCHAR(100), 
	completed_steps TEXT, 
	error_message TEXT, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (session_id)
)




CREATE TABLE workflow_step_logs (
	log_id VARCHAR(36) NOT NULL, 
	session_id VARCHAR(36) NOT NULL, 
	step_name VARCHAR(100) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	started_at DATETIME, 
	finished_at DATETIME, 
	detail TEXT, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	org_id VARCHAR, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	created_by VARCHAR(36), 
	updated_by VARCHAR(36), 
	deleted_at DATETIME, 
	PRIMARY KEY (log_id), 
	FOREIGN KEY(session_id) REFERENCES workflow_sessions (session_id)
)


