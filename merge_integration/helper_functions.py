import logging
from marshmallow import ValidationError
from flask import jsonify, make_response

file = "apiLog"


def api_log(level=logging.DEBUG, msg=""):
    logging.basicConfig(level=level, filename=file, filemode='a', format='%(asctime)s [%(levelname)s] %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p', encoding='utf-8')
    logging.log(level, msg)


def error_response(error, message='', status_code=500):
    """Error response"""
    response = {'success': False, 'error': str(error)}
    if message != '':
        response['message'] = message

    if isinstance(error, ValidationError):
        return make_response(jsonify(response), 400)

    return make_response(jsonify(response), status_code)


def success_response(data, message='', status_code=200):
    """Success response"""
    response = {'success': True, 'data': data}
    if message != '':
        response['message'] = message

    return make_response(jsonify(response), status_code)
