#

import os
import requests
from log.dagda_logger import DagdaLogger


# -- Execute Dagda command
def execute_dagda_cmd(cmd, args):
    # Init
    r = None

    # Executes start sub-command
    if cmd == 'start':
        from api.dagda_server import DagdaServer
        ds = DagdaServer(dagda_server_host=args.get_server_host(),
                         dagda_server_port=args.get_server_port(),
                         mongodb_host=args.get_mongodb_host(),
                         mongodb_port=args.get_mongodb_port(),
                         mongodb_ssl=args.is_mongodb_ssl_enabled(),
                         mongodb_user=args.get_mongodb_user(),
                         mongodb_pass=args.get_mongodb_pass(),
                         falco_rules_filename=args.get_falco_rules_filename(),
                         external_falco_output_filename=args.get_external_falco_output_filename(),
                         debug_logging=args.is_debug_logging_required())
        ds.run()

    # CLI commands
    else:
        dagda_base_url = _get_dagda_base_url()
        # Executes history sub-command
        if cmd == 'history':
            # Gets the global history
            if not args.get_docker_image_name():
                r = requests.get(dagda_base_url + '/history')
            else:
                # Updates product vulnerability as false positive
                if args.get_fp() is not None:
                    fp_product, fp_version = args.get_fp()
                    if fp_version is not None:
                        fp_product += '/' + fp_version
                    r = requests.patch(dagda_base_url + '/history/' + args.get_docker_image_name() + '/fp/'
                                       + fp_product)
                # Checks if a product vulnerability is a false positive
                if args.get_is_fp() is not None:
                    fp_product, fp_version = args.get_is_fp()
                    if fp_version is not None:
                        fp_product += '/' + fp_version
                    r = requests.get(dagda_base_url + '/history/' + args.get_docker_image_name() + '/fp/'
                                     + fp_product)
                # Gets the image history
                else:
                    query_params = ''
                    if args.get_report_id() is not None:
                        query_params = '?id=' + args.get_report_id()
                    r = requests.get(dagda_base_url + '/history/' + args.get_docker_image_name() + query_params)

    # Return
    return r


# -- Private methods

# -- Get Dagda server base url
def _get_dagda_base_url():
    # -- Load env variables
    try:
        dagda_host = os.environ['DAGDA_HOST']
    except KeyError:
        DagdaLogger.get_logger().error('DAGDA_HOST environment variable is not set.')
        exit(1)

    try:
        dagda_port = os.environ['DAGDA_PORT']
    except KeyError:
        DagdaLogger.get_logger().error('DAGDA_PORT environment variable is not set.')
        exit(1)

    # -- Return Dagda server base url
    return 'http://' + dagda_host + ':' + dagda_port + '/v1'

