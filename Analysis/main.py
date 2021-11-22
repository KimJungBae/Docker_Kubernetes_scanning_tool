# main.py

import json
import traceback
from cli.dagda_cli import execute_dagda_cmd
from cli.dagda_cli_parser import DagdaCLIParser
from log.dagda_logger import DagdaLogger


# -- Main function
def main(parsed_args):
    # -- Init
    cmd = parsed_args.get_command()
    parsed_args = parsed_args.get_extra_args()

    try:
        # Execute Dagda command
        r = execute_dagda_cmd(cmd=cmd, args=parsed_args)

        # -- Print cmd output
        if r is not None and r.content:
            output = r.content.decode('utf-8')
            try:
                print(json.dumps(json.loads(output), sort_keys=True, indent=4))
            except json.decoder.JSONDecodeError as err:
                DagdaLogger.get_logger().error('JSONDecodeError with the received response: "' + output + '"')
                DagdaLogger.get_logger().error(str(err))
    except BaseException as err:
        DagdaLogger.get_logger().error(str(err))
        traceback.print_exc()


if __name__ == "__main__":
    main(DagdaCLIParser())