"""
check-book Azure Function

Returns book availability with mTLS validation support.
Validates the Nuance Dialog service client certificate CN
and x-nuance-application-id header.
"""
import json
import logging
import os

import azure.functions as func

SUCCESS_CODE = '0'

# Configurable via environment variable or .env file
EXPECTED_APP_ID = os.environ.get('NUANCE_APP_ID', '')
EXPECTED_CERT_CN = 'backend.dlgaas.nuance.partner.azure.com'
MTLS_ENABLED = os.environ.get('MTLS_ENABLED', 'false').lower() == 'true'


def log_incoming_request(req: func.HttpRequest):
    """Log everything coming from Nuance server."""
    logging.info("=" * 60)
    logging.info("INCOMING REQUEST TO /api/check-book")
    logging.info("=" * 60)

    # Method and URL
    logging.info(f"Method: {req.method}")
    logging.info(f"URL: {req.url}")

    # All headers
    logging.info("----- HEADERS -----")
    for key, value in req.headers.items():
        logging.info(f"  {key}: {value}")

    # Query parameters
    if req.params:
        logging.info("----- QUERY PARAMS -----")
        for key, value in req.params.items():
            logging.info(f"  {key}: {value}")

    # Body
    logging.info("----- BODY -----")
    try:
        body = req.get_json()
        logging.info(f"  JSON: {json.dumps(body, indent=2)}")
    except ValueError:
        body_text = req.get_body().decode('utf-8', errors='replace')
        logging.info(f"  Raw: {body_text}")

    # mTLS specific headers
    logging.info("----- MTLS INFO -----")
    logging.info(f"  x-nuance-application-id: {req.headers.get('x-nuance-application-id', 'NOT PRESENT')}")
    logging.info(f"  x-arr-clientcert: {req.headers.get('x-arr-clientcert', 'NOT PRESENT')}")
    logging.info(f"  x-client-dn: {req.headers.get('x-client-dn', 'NOT PRESENT')}")
    logging.info(f"  x-client-verified: {req.headers.get('x-client-verified', 'NOT PRESENT')}")
    logging.info(f"  Date: {req.headers.get('date', 'NOT PRESENT')}")
    logging.info("=" * 60)


def validate_mtls(req: func.HttpRequest):
    """
    Validate mTLS: check x-nuance-application-id and client certificate CN.
    Returns (is_valid, error_message) tuple.
    """
    if not MTLS_ENABLED:
        logging.info("mTLS validation is DISABLED (set MTLS_ENABLED=true to enable)")
        return True, None

    logging.info("mTLS validation is ENABLED")

    # 1. Check x-nuance-application-id header
    app_id = req.headers.get('x-nuance-application-id', '')
    if EXPECTED_APP_ID and app_id != EXPECTED_APP_ID:
        msg = f"App ID mismatch. Expected: '{EXPECTED_APP_ID}', Got: '{app_id}'"
        logging.warning(msg)
        return False, msg

    if not app_id:
        msg = "Missing x-nuance-application-id header"
        logging.warning(msg)
        return False, msg

    logging.info(f"App ID verified: {app_id}")

    # 2. Check client certificate CN
    # When behind Nginx/reverse proxy, cert info comes via headers
    client_dn = req.headers.get('x-client-dn', '')
    client_cert = req.headers.get('x-arr-clientcert', '')

    if client_dn:
        if EXPECTED_CERT_CN not in client_dn:
            msg = f"Certificate CN mismatch. Expected CN containing: '{EXPECTED_CERT_CN}', Got DN: '{client_dn}'"
            logging.warning(msg)
            return False, msg
        logging.info(f"Certificate CN verified: {client_dn}")
    elif client_cert:
        logging.info(f"Client certificate present (thumbprint/encoded): {client_cert[:50]}...")
    else:
        logging.warning("No client certificate information found in headers")
        # Don't fail here — cert may be terminated at Ngrok/LB level

    return True, None


def main(req: func.HttpRequest) -> func.HttpResponse:

    # Log everything from the incoming request
    log_incoming_request(req)

    # Validate mTLS
    is_valid, error_msg = validate_mtls(req)
    if not is_valid:
        ret = {
            'returnCode': 'error.mtls.validation',
            'returnMessage': error_msg
        }
        logging.warning(f"mTLS validation FAILED: {error_msg}")
        return func.HttpResponse(
            json.dumps(ret),
            mimetype='application/json',
            status_code=403
        )

    # Process the request
    try:
        try:
            req_body = req.get_json()
        except ValueError:
            req_body = {}

        logging.info(f"Processing check-book request with data: {req_body}")

        ret = {
            'returnCode': SUCCESS_CODE,
            'returnMessage': 'available'
        }

    except Exception as ex:
        logging.exception(ex)
        ret = {
            'returnCode': 'error.undefined',
            'returnMessage': f'Undefined error: {str(ex)}'
        }

    return func.HttpResponse(
        json.dumps(ret),
        mimetype='application/json',
        status_code=200
    )
