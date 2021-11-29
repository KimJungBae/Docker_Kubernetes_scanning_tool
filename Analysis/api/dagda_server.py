#

import os
import json
import datetime
import traceback
from waitress import serve
from flask import Flask
from flask_cors import CORS, cross_origin
from api.internal.internal_server import InternalServer
from api.service.check import check_api
from api.service.docker import docker_api
from api.service.history import history_api
from api.service.monitor import monitor_api
from api.service.vuln import vuln_api
from vulnDB.db_composer import DBComposer
from analysis.analyzer import Analyzer
from analysis.runtime.sysdig_falco_monitor import SysdigFalcoMonitor
from exception.dagda_error import DagdaError
from log.dagda_logger import DagdaLogger
from analysis.runtime.docker_events_monitor import DockerDaemonEventsMonitor


# Dagda server class

class DagdaServer:

    # -- Global attributes

    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(check_api)
    app.register_blueprint(docker_api)
    app.register_blueprint(history_api)
    app.register_blueprint(monitor_api)
    app.register_blueprint(vuln_api)

    # -- Public methods

    # DagdaServer Constructor
    def __init__(self, dagda_server_host='127.0.0.1', dagda_server_port=5000, mongodb_host='127.0.0.1',
                 mongodb_port=27017, mongodb_ssl=False, mongodb_user=None, mongodb_pass=None,
                 falco_rules_filename=None, external_falco_output_filename=None, debug_logging=False):
        super(DagdaServer, self).__init__()
        self.dagda_server_host = dagda_server_host
        self.dagda_server_port = dagda_server_port
        InternalServer.set_debug_logging_enabled(debug_logging)
        InternalServer.set_mongodb_driver(mongodb_host, mongodb_port, mongodb_ssl, mongodb_user, mongodb_pass)
        self.sysdig_falco_monitor = SysdigFalcoMonitor(InternalServer.get_docker_driver(),
                                                       InternalServer.get_mongodb_driver(),
                                                       falco_rules_filename,
                                                       external_falco_output_filename)

    # Runs DagdaServer
    def run(self):
        edn_pid = os.fork()
        if edn_pid == 0:
            try:
                while True:
                    item = InternalServer.get_dagda_edn().get()
                    if item['msg'] == 'init_db':
                        self._init_or_update_db()
                    elif item['msg'] == 'check_image':
                        self._check_docker_by_image_name(item)
                    elif item['msg'] == 'check_container':
                        self._check_docker_by_container_id(item)
            except KeyboardInterrupt:
                # Pressed CTRL+C to quit, so nothing to do
                pass

    # -- Post process

    # Apply headers
    @app.after_request
    def apply_headers(response):
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response

    # -- Error handlers

    # 400 Bad Request error handler
    @app.errorhandler(400)
    def bad_request(self):
        return json.dumps({'err': 400, 'msg': 'Bad Request'}, sort_keys=True), 400

    # 404 Not Found error handler
    @app.errorhandler(404)
    def not_found(self):
        return json.dumps({'err': 404, 'msg': 'Not Found'}, sort_keys=True), 404

    # 500 Internal Server error handler
    @app.errorhandler(500)
    def internal_server_error(self):
        return json.dumps({'err': 500, 'msg': 'Internal Server Error'}, sort_keys=True), 500

    # -- Private methods

    # Init or update the vulnerabilities db
    @staticmethod
    def _init_or_update_db():
        try:
            InternalServer.get_mongodb_driver().insert_init_db_process_status(
                {'status': 'Initializing', 'timestamp': datetime.datetime.now().timestamp()})
            # Init db
            db_composer = DBComposer()
            db_composer.compose_vuln_db()
            InternalServer.get_mongodb_driver().insert_init_db_process_status(
                {'status': 'Updated', 'timestamp': datetime.datetime.now().timestamp()})
        except Exception as ex:
            message = "Unexpected exception of type {0} occurred: {1!r}".format(type(ex).__name__,  ex.args)
            DagdaLogger.get_logger().error(message)
            if InternalServer.is_debug_logging_enabled():
                traceback.print_exc()
            InternalServer.get_mongodb_driver().insert_init_db_process_status(
                    {'status': message, 'timestamp': datetime.datetime.now().timestamp()})

    # Check docker by image name
    @staticmethod
    def _check_docker_by_image_name(item):
        analyzer = Analyzer()
        # -- Evaluates the docker image
        evaluated_docker_image = analyzer.evaluate_image(item['image_name'], None)

        # -- Updates mongodb report
        InternalServer.get_mongodb_driver().update_docker_image_scan_result_to_history(item['_id'],
                                                                                       evaluated_docker_image)

        # -- Cleanup
        if item['pulled']:
            InternalServer.get_docker_driver().docker_remove_image(item['image_name'])

    # Check docker by container id
    @staticmethod
    def _check_docker_by_container_id(item):
        analyzer = Analyzer()
        # -- Evaluates the docker image
        evaluated_docker_image = analyzer.evaluate_image(None, item['container_id'])

        # -- Updates mongodb report
        InternalServer.get_mongodb_driver().update_docker_image_scan_result_to_history(item['_id'],
                                                                                       evaluated_docker_image)